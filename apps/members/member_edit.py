"""Editar les dades d'un soci (P5) i corregir la data d'alta (P6) des de la fitxa (T-M01-15b;
HU-M01-07, RN-M01-22, RN-RP-21, S-M01-22).

- Permís al servidor, també aquí i no només a la vista: P5 o P6, i P4 (RN-RP-21). Sense
  permís, «no trobat».
- Per camp: només s'editen els camps que el compte pot veure a la fitxa (`roster.Visibility`):
  el nom amb P4; el correu i el telèfon amb P4 sencer; el document i l'adreça, també amb C2.
  La data d'alta (P6) demana P4 sencer, perquè «dades mínimes» no la veu.
- Conflicte d'interès (S-M01-22, regla protegida): ningú no edita el seu propi soci des de
  l'administració; l'intent queda registrat (`services.ensure_not_own_member`).
- Les dades de la persona les escriu el servei de la 00 (`persons.update`), amb una entrada per
  camp al registre d'activitat amb el valor anterior. La data d'alta deixa una fila a
  `MemberJoinDateChange` (historial visible a la fitxa) i el registre d'activitat (RN-M01-22).

Fora d'abast (docs/planning.md, fila de la T-M01-15b): el número de soci (pendent de decisió), la
data de naixement (T-M01-33), el tipus i l'estat (serveis de la T-M01-12 i la T-M01-17) i els
camps opcionals de la P-58. Mai l'IBAN ni cap dada de salut.
"""

import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import audit, persons
from apps.core.normalization import normalize_document
from apps.core.permission_catalog import SCOPE_ALL
from apps.core.permissions import effective_permissions, has_perm

from . import roster
from .forms import DOCUMENT_INVALID, clean_phone_value, parse_document
from .models import Member, MemberJoinDateChange
from .services import _check_account_active, ensure_not_own_member

EDIT = "members.edit"  # P5
EDIT_JOIN_DATE = "members.edit_join_date"  # P6
JOIN_DATE_CORRECTED = "members.join_date_corrected"
OWN_MEMBER = _("És el teu soci: no pots editar-ne les dades des de l'administració.")

NAME_FIELDS = ("first_name", "last_name")
CONTACT_FIELDS = ("contact_email", "phone", "landline")
# L'adreça desglossada (072, P-58) va amb l'adreça: només amb C2.
IDENTITY_FIELDS = (
    "id_document_type",
    "id_document_number",
    "address",
    "postal_code",
    "city",
    "province",
)


def editable_fields(user, perms=None) -> tuple[str, ...]:
    """Camps de la persona que el compte pot editar; buit si no té P5 i P4."""
    perms = effective_permissions(user) if perms is None else perms
    if not (has_perm(user, EDIT, permissions=perms) and roster.LIST in perms):
        return ()
    vis = roster.visibility_for(user, perms)
    return (
        NAME_FIELDS
        + (CONTACT_FIELDS if vis.full else ())
        + (IDENTITY_FIELDS if vis.identity else ())
    )


def can_correct_join_date(user, perms=None) -> bool:
    perms = effective_permissions(user) if perms is None else perms
    return has_perm(user, EDIT_JOIN_DATE, permissions=perms) and perms.get(roster.LIST) == SCOPE_ALL


def authorize(member, by, permission, *, request=None) -> None:
    """Compte actiu, permís (Http404) i conflicte d'interès (registrat). Abans de cap
    transacció, com diu el contracte d'`ensure_not_own_member`."""
    _check_account_active(by)
    allowed = editable_fields(by) if permission == EDIT else can_correct_join_date(by)
    if not allowed:
        raise Http404
    ensure_not_own_member(member, by, request=request, message=OWN_MEMBER)


def edit_member_data(member, *, by, fields, request=None) -> list[str]:
    """P5. `fields` són camps de la persona; un camp que el compte no pot editar és «no trobat»,
    encara que la petició l'hagi afegit. Torna els camps que han canviat."""
    authorize(member, by, EDIT, request=request)
    if set(fields) - set(editable_fields(by)):
        raise Http404
    with transaction.atomic():
        _check_account_active(by, lock=True)
        return persons.update(member.person, by=by, request=request, **fields)


def correct_join_date(member, *, by, joined_on, approximate, request=None) -> bool:
    """P6 (RN-M01-22). Historial i registre amb el valor anterior. Torna si ha canviat res."""
    authorize(member, by, EDIT_JOIN_DATE, request=request)
    if not isinstance(joined_on, datetime.date) or isinstance(joined_on, datetime.datetime):
        raise ValidationError(_("Cal la data d'alta."))
    if joined_on > timezone.localdate():
        raise ValidationError(_("La data d'alta no pot ser posterior a avui."))
    with transaction.atomic():
        _check_account_active(by, lock=True)
        locked = Member.objects.select_for_update().get(pk=member.pk)
        # Ja ho garanteix la baixa (T-M01-12): una baixa no és anterior a la data d'alta.
        if locked.left_on and joined_on > locked.left_on:
            raise ValidationError(_("La data d'alta no pot ser posterior a la data de baixa."))
        old = (locked.joined_on, locked.joined_on_is_approximate)
        if old == (joined_on, approximate):
            return False
        MemberJoinDateChange.objects.create(
            member=locked,
            from_joined_on=old[0],
            from_is_approximate=old[1],
            to_joined_on=joined_on,
            to_is_approximate=approximate,
            actor_account=by,  # `authorize` ja exigeix un compte amb P6
        )
        audit.record_changes(
            JOIN_DATE_CORRECTED,
            actor=by,
            target=locked,
            changes={
                "joined_on": (old[0], joined_on),
                "joined_on_is_approximate": (old[1], approximate),
            },
            request=request,
        )
        locked.joined_on, locked.joined_on_is_approximate = joined_on, approximate
        locked.save(update_fields=["joined_on", "joined_on_is_approximate", "updated_at"])
    member.refresh_from_db()
    return True


# --- Formularis ----------------------------------------------------------------------------


class MemberDataForm(forms.Form):
    """Només porta els camps de `editable_fields`: la resta de la petició s'ignora."""

    first_name = forms.CharField(label=_("Nom"), max_length=100)
    last_name = forms.CharField(label=_("Cognoms"), max_length=150)
    contact_email = forms.EmailField(label=_("Correu electrònic"), max_length=254)
    phone = forms.CharField(label=_("Telèfon"), max_length=30)
    id_document = forms.CharField(
        label=_("Document d'identitat"),
        max_length=30,
        required=False,
        help_text=_("Un document nou ha de ser un DNI o un NIE vàlid, amb la lletra."),
    )
    address = forms.CharField(label=_("Adreça (opcional)"), max_length=255, required=False)
    landline = forms.CharField(label=_("Telèfon fix (opcional)"), max_length=30, required=False)
    postal_code = forms.CharField(label=_("Codi postal (opcional)"), max_length=10, required=False)
    city = forms.CharField(label=_("Població (opcional)"), max_length=100, required=False)
    province = forms.CharField(label=_("Província (opcional)"), max_length=100, required=False)

    def __init__(self, data=None, *, person, fields):
        self.person = person
        initial = {name: getattr(person, name) for name in fields}
        initial["id_document"] = person.id_document_number
        super().__init__(data, initial=initial)
        keep = {"id_document" if name.startswith("id_document") else name for name in fields}
        for name in list(self.fields):
            if name not in keep:
                del self.fields[name]
        for field in self.fields.values():
            field.widget.attrs["autocomplete"] = "off"  # no les dades de qui edita
        if "id_document" in self.fields:
            self.fields["id_document"].widget.attrs["spellcheck"] = "false"

    def clean_phone(self):
        return clean_phone_value(self.cleaned_data["phone"])

    def clean_id_document(self):
        """El document actual es pot deixar tal com és (també un passaport). Un de nou ha de ser
        un DNI o un NIE vàlid, com a l'alta. No es pot buidar: sense la data de naixement
        (T-M01-33) no se sap si la persona és menor, l'únic cas en què és opcional (068)."""
        raw = self.cleaned_data["id_document"].strip()
        current = (self.person.id_document_type, self.person.id_document_number)
        if normalize_document(raw) == current[1]:
            return current
        if not raw:
            raise ValidationError(_("El document no es pot treure, només corregir."))
        parsed = parse_document(raw)
        if parsed is None:
            raise ValidationError(DOCUMENT_INVALID)
        return parsed

    def person_fields(self) -> dict:
        data = dict(self.cleaned_data)
        if "id_document" in data:
            data["id_document_type"], data["id_document_number"] = data.pop("id_document")
        return data


class JoinDateForm(forms.Form):
    joined_on = forms.DateField(
        label=_("Data d'alta"),
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        error_messages={"invalid": _("Escriu una data vàlida, per exemple 12/03/1987.")},
    )
    approximate = forms.BooleanField(
        label=_("La data és aproximada"),
        required=False,
        help_text=_("Marca-ho si no és segura (per exemple, recuperada d'un carnet antic)."),
    )

    def __init__(self, data=None, *, member):
        super().__init__(
            data,
            initial={"joined_on": member.joined_on, "approximate": member.joined_on_is_approximate},
        )
        self.fields["joined_on"].widget.attrs["max"] = timezone.localdate().isoformat()
