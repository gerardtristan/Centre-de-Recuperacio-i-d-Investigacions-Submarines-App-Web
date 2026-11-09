"""Registre mínim de llicència a la fitxa del soci (T-M01-23; RN-M01-29, P19).

- Veure: P19 amb qualsevol abast (configuració inicial de la 059: secretaria i administrador
  «Sí»; tresorer i responsable de cursos i sortides «Cons.»). La fitxa ja demana P4: el
  responsable de cursos i sortides, que no té P4, no l'hi veu.
- Afegir i corregir: P19 sencer (no «Cons.») i P4 (RN-RP-21), comprovat aquí i no només a la
  vista. Sense permís, «no trobat». Ningú no ho fa amb el seu propi soci (S-M01-22): l'intent
  queda registrat.
- Validació de dates: `expires_on ≥ issued_on` quan hi ha data (addenda de la 058); la base de
  dades ho torna a comprovar (`licencerecord_expires_after_issue`).
- Registre d'activitat: una entrada per camp, amb el valor anterior.
- Res s'esborra (RN-M01-36). Els registres nous tenen l'origen `manual`; corregir-ne un de Cluber
  no en canvia l'origen ni el lot.

Fora d'aquesta tasca: els serveis de lectura `licence_record` i `licence_records` (T-M01-30), el
text i la priorització de la caducitat desconeguda (RN-M01-50, T-M01-34), el número federatiu
(fins que la 06 el defineixi) i la llista tancada de tipus de la FECDAS [A verificar: FECDAS].
Cap dada de salut.
"""

import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from apps.core import audit
from apps.core.models import Person
from apps.core.permissions import effective_permissions, has_perm

from . import roster
from .models import LicenceRecord
from .services import _check_account_active, ensure_not_own_member

MANAGE = "members.licence_record.manage"  # P19
ADDED = "members.licence_record.added"
CORRECTED = "members.licence_record.corrected"
OWN_MEMBER = _("És el teu soci: no pots canviar-ne la llicència des de l'administració.")
EXPIRES_BEFORE_ISSUE = _("La data de caducitat no pot ser anterior a la data d'alta.")
EXPIRES_REQUIRED = _("Cal la data de caducitat.")
ANONYMISED = _("Les dades d'aquesta persona estan anonimitzades i no es poden editar.")


def can_view(user, perms=None) -> bool:
    perms = effective_permissions(user) if perms is None else perms
    return has_perm(user, MANAGE, permissions=perms)


def can_manage(user, perms=None) -> bool:
    perms = effective_permissions(user) if perms is None else perms
    return has_perm(user, MANAGE, write=True, permissions=perms) and roster.LIST in perms


def authorize(member, by, *, request=None) -> None:
    """Compte actiu, permís (Http404) i conflicte d'interès (registrat), abans de cap
    transacció, com diu el contracte d'`ensure_not_own_member`."""
    _check_account_active(by)
    if not can_manage(by):
        raise Http404
    ensure_not_own_member(member, by, request=request, message=OWN_MEMBER)


def _is_date(value) -> bool:
    # Un `datetime` també és un `date`: es rebutja per no perdre l'hora en silenci.
    return isinstance(value, datetime.date) and not isinstance(value, datetime.datetime)


def _clean(licence_type, issued_on, expires_on, *, expires_optional=False):
    licence_type = (licence_type or "").strip()
    if not licence_type:
        raise ValidationError(_("Cal el tipus de llicència."))
    if len(licence_type) > LicenceRecord._meta.get_field("licence_type").max_length:
        raise ValidationError(_("El tipus de llicència és massa llarg."))
    if not _is_date(issued_on):
        raise ValidationError(_("Cal la data d'alta de la llicència."))
    if expires_on is None:
        if not expires_optional:
            raise ValidationError(EXPIRES_REQUIRED)
    elif not _is_date(expires_on):
        raise ValidationError(EXPIRES_REQUIRED)
    elif expires_on < issued_on:
        raise ValidationError(EXPIRES_BEFORE_ISSUE)
    return licence_type


def _check_person_active(member) -> None:
    status = Person.objects.filter(pk=member.person_id).values_list("status", flat=True).first()
    if status != Person.Status.ACTIVE:
        raise ValidationError(ANONYMISED)


def add_record(member, *, by, licence_type, issued_on, expires_on, request=None) -> LicenceRecord:
    """Crea un registre amb l'origen `manual`. La caducitat és obligatòria: RN-M01-29 la demana i
    la caducitat desconeguda (RN-M01-50) és el cas dels registres de Cluber."""
    authorize(member, by, request=request)
    licence_type = _clean(licence_type, issued_on, expires_on)
    with transaction.atomic():
        _check_account_active(by, lock=True)
        _check_person_active(member)
        record = LicenceRecord.objects.create(
            member=member,
            licence_type=licence_type,
            issued_on=issued_on,
            expires_on=expires_on,
            source=LicenceRecord.Source.MANUAL,
        )
        audit.record_changes(
            ADDED,
            actor=by,
            target=record,
            changes={
                "licence_type": (None, licence_type),
                "issued_on": (None, issued_on),
                "expires_on": (None, expires_on),
            },
            request=request,
        )
    return record


def correct_record(record, *, by, licence_type, issued_on, expires_on, request=None) -> bool:
    """Corregeix el tipus i les dates. Una caducitat que ja era buida (registre de Cluber) es pot
    deixar buida; no se'n pot buidar una de coneguda. Torna si ha canviat res."""
    member = record.member
    authorize(member, by, request=request)
    with transaction.atomic():
        _check_account_active(by, lock=True)
        _check_person_active(member)
        locked = LicenceRecord.objects.select_for_update().get(pk=record.pk)
        licence_type = _clean(
            licence_type, issued_on, expires_on, expires_optional=locked.expires_on is None
        )
        changes = {
            "licence_type": (locked.licence_type, licence_type),
            "issued_on": (locked.issued_on, issued_on),
            "expires_on": (locked.expires_on, expires_on),
        }
        recorded = audit.record_changes(
            CORRECTED, actor=by, target=locked, changes=changes, request=request
        )
        if not recorded:
            return False
        locked.licence_type, locked.issued_on, locked.expires_on = (
            licence_type,
            issued_on,
            expires_on,
        )
        locked.save(update_fields=["licence_type", "issued_on", "expires_on"])
    record.refresh_from_db()
    return True


class LicenceRecordForm(forms.Form):
    licence_type = forms.CharField(
        label=_("Tipus de llicència"),
        max_length=100,
        help_text=_("Tal com consta a la llicència federativa."),
    )
    issued_on = forms.DateField(
        label=_("Data d'alta"),
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        error_messages={"invalid": _("Escriu una data vàlida, per exemple 01/01/2027.")},
    )
    expires_on = forms.DateField(
        label=_("Data de caducitat"),
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        error_messages={"invalid": _("Escriu una data vàlida, per exemple 31/12/2027.")},
    )

    def __init__(self, data=None, *, record=None):
        initial = {}
        if record is not None:
            initial = {
                "licence_type": record.licence_type,
                "issued_on": record.issued_on,
                "expires_on": record.expires_on,
            }
        super().__init__(data, initial=initial)
        self.fields["licence_type"].widget.attrs["autocomplete"] = "off"
        # Només es pot deixar buida una caducitat que ja ho era (registre de Cluber).
        expires = self.fields["expires_on"]
        expires.required = not (record is not None and record.expires_on is None)
        expires.error_messages["required"] = EXPIRES_REQUIRED

    def clean(self):
        data = super().clean()
        issued, expires = data.get("issued_on"), data.get("expires_on")
        if issued and expires and expires < issued:
            self.add_error("expires_on", EXPIRES_BEFORE_ISSUE)
        return data
