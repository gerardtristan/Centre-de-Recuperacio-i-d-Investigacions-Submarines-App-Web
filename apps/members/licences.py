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
text «caducitat desconeguda» de la fitxa i la marca `expiry_unknown` (RN-M01-50, T-M01-34), el
número federatiu (fins que la 06 el defineixi) i la llista tancada de tipus de la FECDAS
[A verificar: FECDAS].
Cap dada de salut.
"""

import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Account
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
    deixar buida; no se'n pot buidar una de coneguda. Desar una caducitat declarada pel soci,
    igual o corregida, la confirma: treu la marca (RN-M01-77). Torna si ha canviat res."""
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
            "expiry_declared": (locked.expiry_declared, False),
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
        locked.expiry_declared = False
        locked.save(update_fields=["licence_type", "issued_on", "expires_on", "expiry_declared"])
    record.refresh_from_db()
    return True


# --- Confirmació en bloc de les caducitats d'any natural (T-M01-36; RN-M01-56, CA-M01-44) -------
# La plataforma no sap quines llicències són d'any natural (el tipus és text lliure fins a la 06):
# ho decideix la secretaria en seleccionar-les. Una caducitat declarada pel soci ja té data i, per
# tant, no surt aquí: la secretaria la confirma a la fitxa (`correct_record`; RN-M01-77).

CONFIRMED_IN_BULK = "members.licence_record.expiry_confirmed_in_bulk"
NOT_PENDING = _("Algun registre ja no està pendent de confirmar. Torna a carregar la llista.")
NOTHING_SELECTED = _("Selecciona almenys un registre.")


def pending_records(by):
    """Registres sense caducitat de persones no anonimitzades, sense els del soci de qui confirma
    (S-M01-22). Només llegeix: el permís el comprova la vista i el torna a comprovar el servei."""
    return (
        LicenceRecord.objects.filter(
            expires_on__isnull=True, member__person__status=Person.Status.ACTIVE
        )
        .exclude(member__person_id=by.person_id)
        .select_related("member__person")
        .order_by("member__member_number", "pk")
    )


def confirm_in_bulk(record_ids, *, year, by, request=None) -> int:
    """Fixa la caducitat al 31/12 de `year` a tots els registres triats, tot o res. Cada registre
    deixa una entrada al registre d'activitat amb el valor anterior (buit). Torna quants."""
    _check_account_active(by)
    if not can_manage(by):
        raise Http404
    ids = {int(pk) for pk in record_ids}
    if not ids:
        raise ValidationError(NOTHING_SELECTED)
    if isinstance(year, bool) or not isinstance(year, int) or year not in allowed_years():
        raise ValidationError(
            _("L'any de caducitat ha de ser %(this)s o %(next)s.")
            % {"this": allowed_years()[0], "next": allowed_years()[1]}
        )
    expires_on = datetime.date(year, 12, 31)
    own = LicenceRecord.objects.filter(pk__in=ids, member__person_id=by.person_id).first()
    if own is not None:
        ensure_not_own_member(own.member, by, request=request, message=OWN_MEMBER)
    with transaction.atomic():
        _check_account_active(by, lock=True)
        records = list(
            LicenceRecord.objects.select_for_update(of=("self",))
            .filter(
                pk__in=ids, expires_on__isnull=True, member__person__status=Person.Status.ACTIVE
            )
            .order_by("pk")
        )
        if len(records) != len(ids):
            raise ValidationError(NOT_PENDING)
        late = sum(1 for record in records if record.issued_on > expires_on)
        if late:
            raise ValidationError(
                _(
                    "Hi ha %(count)s registre(s) amb la data d'alta posterior al %(date)s: "
                    "treu-los de la selecció o tria un altre any."
                ),
                params={"count": late, "date": expires_on.strftime("%d/%m/%Y")},
            )
        for record in records:
            record.expires_on = expires_on
            audit.record_changes(
                CONFIRMED_IN_BULK,
                actor=by,
                target=record,
                changes={"expires_on": (None, expires_on)},
                request=request,
            )
        LicenceRecord.objects.bulk_update(records, ["expires_on"])
    return len(records)


# --- Caducitat declarada pel soci (T-M01-36; RN-M01-77, CA-M01-76) ------------------------------

DECLARED = "members.licence_record.expiry_declared"
ALREADY_KNOWN = _("Aquesta llicència ja té data de caducitat: no la pots declarar.")


def declare_expiry(record, *, by, expires_on, request=None) -> None:
    """El soci declara la caducitat d'un registre seu que la té desconeguda. Es desa a
    `expires_on` amb la marca «declarada» fins que la secretaria la confirma a la fitxa. Un
    registre d'una altra persona és «no trobat»; la vista registra l'intent abans (CA-M01-25).
    És una acció pròpia: només amb el compte personal (059, punt 4.2; T-M01-37)."""
    _check_account_active(by)
    if not isinstance(by, Account) or by.kind != Account.Kind.PERSONAL:
        raise Http404
    if record.member.person_id != by.person_id:
        raise Http404
    with transaction.atomic():
        _check_account_active(by, lock=True)
        _check_person_active(record.member)
        locked = LicenceRecord.objects.select_for_update().get(pk=record.pk)
        if locked.expires_on is not None:
            raise ValidationError(ALREADY_KNOWN)
        _clean(locked.licence_type, locked.issued_on, expires_on)
        audit.record_changes(
            DECLARED,
            actor=by,
            target=locked,
            changes={"expires_on": (None, expires_on), "expiry_declared": (False, True)},
            request=request,
        )
        locked.expires_on, locked.expiry_declared = expires_on, True
        locked.save(update_fields=["expires_on", "expiry_declared"])
    record.refresh_from_db()


class DeclareExpiryForm(forms.Form):
    expires_on = forms.DateField(
        label=_("Declara la data de caducitat"),
        help_text=_("Quedarà «declarada per tu» fins que la secretaria la confirmi."),
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        error_messages={
            "required": _("Escriu la data de caducitat de la teva llicència."),
            "invalid": _("Escriu una data vàlida, per exemple 31/12/2027."),
        },
    )


def _current_year() -> int:
    return timezone.localdate().year


def allowed_years() -> tuple[int, int]:
    """Decisió 085 (S-4, opció B): en confirmar en bloc només es pot posar l'any actual o el
    següent. Evita que un error de teclat deixi llicències vigents durant anys."""
    year = _current_year()
    return (year, year + 1)


class BulkConfirmForm(forms.Form):
    records = forms.ModelMultipleChoiceField(
        label=_("Registres"),
        # El servei torna a comprovar el soci propi, la persona i que encara siguin pendents.
        queryset=LicenceRecord.objects.filter(expires_on__isnull=True),
        error_messages={
            "required": NOTHING_SELECTED,
            "invalid_choice": NOT_PENDING,
            "invalid_pk_value": NOT_PENDING,
        },
    )
    year = forms.IntegerField(
        label=_("Any de caducitat"),
        help_text=_(
            "Les llicències seleccionades caducaran el 31/12 d'aquest any. Només pot ser "
            "l'any actual o el següent."
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        this_year, next_year = allowed_years()
        self.fields["year"].min_value = this_year
        self.fields["year"].max_value = next_year
        self.fields["year"].widget.attrs.update({"min": this_year, "max": next_year})

    def clean_year(self):
        year = self.cleaned_data["year"]
        if year not in allowed_years():
            raise forms.ValidationError(
                _("L'any de caducitat ha de ser %(this)s o %(next)s.")
                % {"this": allowed_years()[0], "next": allowed_years()[1]}
            )
        return year


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
        if record is not None and record.expiry_declared:
            expires.help_text = _(
                "Declarada pel soci, pendent de confirmar. Desa-la tal com està per acceptar-la "
                "o escriu-ne una altra per corregir-la."
            )

    def clean(self):
        data = super().clean()
        issued, expires = data.get("issued_on"), data.get("expires_on")
        if issued and expires and expires < issued:
            self.add_error("expires_on", EXPIRES_BEFORE_ISSUE)
        return data
