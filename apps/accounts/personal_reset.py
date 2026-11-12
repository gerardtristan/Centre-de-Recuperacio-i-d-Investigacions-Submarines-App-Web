"""Restabliment presencial del doble factor d'un compte personal (P-52; decisió 081, punt 24;
RN-M01-104; T-M01-51).

Quan un soci perd el mòbil amb el doble factor actiu, la secretaria el restableix **en persona**,
després de comprovar-ne la identitat amb el document original. No hi ha cap altre camí: cap
enllaç del correu, cap formulari públic ni la recuperació de la contrasenya no treuen el doble
factor (una prova ho comprova). Els comptes personals continuen sense codis de recuperació
(decisió 081: no se n'afegeixen); els comptes d'administrador mantenen els seus i el restabliment
d'un altre administrador (M4, HU-08).

- **Permís:** M2 (`core.people.manage`, «crear i editar perfils d'altres persones i els seus
  comptes personals», amb edició). La vista també demana P4 per obrir la fitxa del soci.
- **Comprovació presencial:** casella obligatòria i el número del document que la persona mostra,
  que ha de coincidir amb el de la fitxa (no es desa ni surt al registre). Sense document a la
  fitxa, no es pot fer per aquesta via.
- **Qui ho fa:** un codi TOTP nou seu a la mateixa petició (com RN-M01-60) i un motiu obligatori.
  Ningú no restableix el seu propi compte.
- **Efecte:** s'eliminen el secret TOTP i els codis de recuperació que pogués tenir el compte i
  se'n tanquen totes les sessions. El titular pot tornar a activar el doble factor des de
  «Seguretat» quan entri amb la contrasenya (HU-05).
- **Registre i avís:** el registre d'activitat guarda qui, quan i el motiu; el titular rep un avís
  a l'adreça del compte, sense cap enllaç ni codi, i el resultat de l'avís té la seva entrada.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import audit, mail
from apps.core.models import Person
from apps.core.normalization import normalize_document
from apps.core.permissions import has_perm

from .models import Account, RecoveryCode, TotpDevice

PERMISSION = "core.people.manage"  # M2
NOTICE_TEMPLATE = "restabliment-doble-factor"
PERSONAL_TOTP_RESET = "auth.personal_totp_reset"

NOT_PERSONAL = _("Aquesta acció és per a comptes personals.")
OWN_ACCOUNT = _("Ningú no pot restablir el doble factor del seu propi compte.")
IDENTITY_REQUIRED = _("Cal confirmar que has comprovat la identitat en persona.")
NOTE_REQUIRED = _("Cal un motiu per restablir el doble factor.")
NO_SECOND_FACTOR = _("Aquest compte no té el doble factor activat.")
NO_DOCUMENT = _(
    "La persona no té document a la fitxa: no es pot comprovar la identitat per aquesta via."
)
DOCUMENT_MISMATCH = _("El document no coincideix amb el de la fitxa. No s'ha canviat res.")


def can_reset(user, perms=None) -> bool:
    return has_perm(user, PERMISSION, write=True, permissions=perms)


def personal_account_with_totp(person) -> Account | None:
    return (
        Account.objects.filter(
            person=person,
            kind=Account.Kind.PERSONAL,
            totp_device__confirmed_at__isnull=False,
        )
        .exclude(status=Account.Status.DISABLED)
        .first()
    )


@transaction.atomic
def reset_personal_totp(
    account: Account, *, by: Account, document: str, identity_checked: bool, note: str, request=None
) -> bool:
    """Restableix el doble factor del compte personal. Torna si s'ha posat l'avís a la cua. El
    codi TOTP de qui ho fa el comprova la vista, a la mateixa petició."""
    if not can_reset(by):
        raise Http404
    if account.kind != Account.Kind.PERSONAL:
        raise ValidationError(NOT_PERSONAL)
    if account.person_id == by.person_id:
        raise ValidationError(OWN_ACCOUNT)
    if not identity_checked:
        raise ValidationError(IDENTITY_REQUIRED)
    if not (note or "").strip():
        raise ValidationError(NOTE_REQUIRED)
    locked = Account.objects.select_for_update().get(pk=account.pk)
    person = Person.objects.get(pk=locked.person_id)
    if person.status != Person.Status.ACTIVE or locked.status == Account.Status.DISABLED:
        raise ValidationError(NOT_PERSONAL)
    if not person.id_document_number:
        raise ValidationError(NO_DOCUMENT)
    if normalize_document(document or "") != person.id_document_number:
        raise ValidationError(DOCUMENT_MISMATCH)
    if not TotpDevice.objects.filter(account=locked, confirmed_at__isnull=False).exists():
        raise ValidationError(NO_SECOND_FACTOR)

    audit.record(
        PERSONAL_TOTP_RESET,
        actor=by,
        target=locked,
        reason=note.strip(),
        details={"identity_checked_in_person": True, "document_matched": True},
        request=request,
    )
    TotpDevice.objects.filter(account=locked).delete()
    RecoveryCode.objects.filter(account=locked).delete()
    locked.end_all_sessions()

    email = mail.queue_email(
        NOTICE_TEMPLATE,
        to=locked.login,
        person=person,
        context={"when": timezone.localtime()},
    )
    audit.record(
        audit.Action.RESET_NOTICE,
        actor=by,
        target=locked,
        details={
            "result": "queued" if email is not None else "not_sent",
            "email_id": email.pk if email is not None else None,
            "second_factor": True,
        },
        request=request,
    )
    return email is not None
