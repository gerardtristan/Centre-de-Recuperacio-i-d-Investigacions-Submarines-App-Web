"""RGPD dels comptes (T-M01-22; HU-18 i HU-19 de la spec 00; decisió 028).

El crida `apps.core.privacy`, que porta l'exportació i l'esborrat d'una persona de principi a fi.

- **Exportació:** quins comptes té la persona i amb què hi entra. Mai l'empremta de la
  contrasenya, el secret TOTP ni els codis de recuperació.
- **Esborrat (CA-19.1):** cada compte queda desactivat i sense sessions, i el que identifica la
  persona (correu d'entrada o nom d'usuari, i correu de notificació) se substitueix per la
  referència. La contrasenya queda inservible: un compte desactivat que algú tornés a
  activar tampoc no deixaria entrar. Les invitacions vives s'invaliden (079, punt 10).
- **TOTP i codis de recuperació:** s'eliminen (decisió 081, punt 18), amb el nombre de codis
  eliminats al registre. Els enllaços del correu també deixen de valer, perquè l'empremta dels
  testimonis inclou l'estat i la contrasenya (`tokens.py`).
"""

from django.core.exceptions import ValidationError

from apps.core import audit, roles
from apps.core.persons import anonymous_email

from . import invitations, limits
from .models import Account, EmailLinkRequest, FailedLogin, RecoveryCode, TotpDevice


def export(person) -> list[dict]:
    return [
        {
            "tipus": account.get_kind_display(),
            "identificador_d_entrada": account.login,
            "correu_de_notificacio": account.notification_email,
            "estat": account.get_status_display(),
            "doble_factor_actiu": account.has_totp,
            "creat_el": account.created_at,
            "ultima_entrada": account.last_login,
        }
        for account in person.accounts.select_related("totp_device").order_by("pk")
    ]


def addresses(person) -> set[str]:
    """Adreces de correu que els comptes guarden de la persona."""
    found = set()
    for account in person.accounts.all():
        found.add(account.notification_email)
        if account.kind == Account.Kind.PERSONAL:
            found.add(account.login)
    return found - {""}


def erasure_blocker(person) -> str:
    """Per què no es poden desactivar ara els comptes de la persona, o "" (RN-RP-13: mai cap
    administrador operatiu)."""
    for account in person.accounts.filter(kind=Account.Kind.ADMIN, status=Account.Status.ACTIVE):
        if roles._would_leave_no_operational_admin(account):
            return str(roles.NO_OPERATIONAL_ADMIN)
    return ""


def _anonymous_login(account, ref: str) -> str:
    # El correu porta sempre «@» i el nom d'usuari mai (restricció `account_login_matches_kind`).
    if account.kind == Account.Kind.PERSONAL:
        return anonymous_email(ref)
    return f"{ref.lower()}.admin"


def anonymise(person, *, by, known_addresses=(), request=None) -> list[int]:
    """Desactiva i anonimitza els comptes d'una persona ja anonimitzada, dins la transacció de
    qui crida. `known_addresses`: les adreces de correu que tenia la persona. Torna els
    identificadors dels comptes."""
    ref = person.anonymous_ref
    blocker = erasure_blocker(person)
    if blocker:
        raise ValidationError(blocker)
    ids = []
    for account in Account.objects.select_for_update().filter(person=person).order_by("pk"):
        old_status = account.status
        account.status = Account.Status.DISABLED
        account.login = _anonymous_login(account, ref)
        account.notification_email = ""
        account.set_unusable_password()
        account.failed_login_count = 0
        account.locked_until = None
        account.password_temporary_until = None
        account.last_login = None
        account.save()
        account.end_all_sessions()
        # Intents fallits: una adreça IP lligada al compte.
        FailedLogin.objects.filter(account=account).delete()
        # Decisió 081, punt 18: el secret TOTP i els codis de recuperació s'eliminen. El compte
        # ja no pot entrar (desactivat i sense contrasenya), però no se'n conserva cap factor.
        totp_removed, _ = TotpDevice.objects.filter(account=account).delete()
        codes_removed, _ = RecoveryCode.objects.filter(account=account).delete()
        audit.record(
            audit.Action.ACCOUNT_DISABLED_BY_ERASURE,
            actor=by,
            target=account,
            field="status",
            old=old_status,
            new=account.status,
            details={
                "second_factor_removed": bool(totp_removed),
                "backup_codes_removed": codes_removed,
            },
            request=request,
        )
        ids.append(account.pk)
    invitations.invalidate(person)
    # Límits dels enllaços del correu: l'empremta de l'adreça deixa de constar; la fila continua
    # comptant per a l'origen fins que la tasca diària l'esborra.
    EmailLinkRequest.objects.filter(
        recipient_hash__in=[limits.recipient_key(address) for address in known_addresses]
    ).update(recipient_hash="")
    return ids
