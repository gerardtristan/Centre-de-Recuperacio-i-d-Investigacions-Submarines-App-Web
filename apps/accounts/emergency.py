"""Comptes d'emergència (T-M00-03; spec 00, HU-10, CA-10.1 i CA-10.2; RN-RP-13 i RN-RP-18; decisió
079, A-30).

- **Persona tècnica (A-30).** Cada compte d'emergència es lliga a una persona tècnica pròpia, sense
  cap dada personal: nom genèric, cap cognom, correu, telèfon, document ni data. És l'única excepció
  a la definició de «Persona» (079), i així cap persona real no té dos comptes d'administrador
  (RN-13, CA-06.4; Q-02 resolta per la 079).
- **Rol.** El rol administrador, que no el fa comptar com a administrador operatiu (RN-RP-13) i li
  permet l'excepció de RN-RP-18 (`roles`, ja implementada). Rol i custòdia de les credencials:
  [A validar: junta].
- **Creació.** Només des del servidor (`manage.py crea_compte_emergencia`), com el primer
  administrador: l'actor del registre és el sistema amb el nom de l'ordre. La contrasenya no surt
  mai a la sortida ni al registre. El doble factor es dona d'alta en la primera entrada, amb els
  codis de recuperació fora de línia (CA-09.1, ja implementats).
- **Avís (CA-10.1).** Amb menys de `MINIMUM` comptes d'emergència actius amb TOTP, els comptes amb
  el rol administrador veuen un avís a l'inici de l'administració i a la llista de comptes.
- **Ús (CA-10.2, proposta de la spec).** Cada entrada amb un compte d'emergència queda al registre i
  s'avisa per correu tots els altres comptes actius amb el rol administrador que tenen adreça de
  notificació.
"""

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from apps.core import audit, mail, roles
from apps.core.models import AccountRole, Person, Role

from .models import Account

MINIMUM = 2
CREATED = "accounts.emergency_created"
USED = "accounts.emergency_used"
NOTICE_TEMPLATE = "avis-compte-emergencia"
TECHNICAL_NAME = "Compte d'emergència"
COMMAND = "crea_compte_emergencia"


@transaction.atomic
def create(username: str, password: str, *, origin: str = COMMAND) -> Account:
    """Crea la persona tècnica i el compte d'emergència amb el rol administrador."""
    from apps.core.roles import grant_initial_administrator

    person = Person.objects.create(first_name=TECHNICAL_NAME, origin=Person.Origin.TECHNICAL)
    account = Account(person=person, kind=Account.Kind.ADMIN, login=username, is_emergency=True)
    validate_password(password, user=account)
    account = Account.objects.create_admin(person, username, password)
    account.is_emergency = True
    account.save(update_fields=["is_emergency"])
    audit.record(CREATED, actor=audit.system(origin), target=account)
    grant_initial_administrator(account, origin=origin)
    return account


def ready_accounts():
    """CA-10.1: comptes d'emergència actius i amb el TOTP donat d'alta."""
    return Account.objects.filter(
        kind=Account.Kind.ADMIN,
        is_emergency=True,
        status=Account.Status.ACTIVE,
        totp_device__confirmed_at__isnull=False,
    )


def _is_administrator(account) -> bool:
    return AccountRole.objects.filter(
        admin_account=account, role__code=Role.Code.ADMINISTRATOR, removed_at__isnull=True
    ).exists()


def warning_for(account) -> int | None:
    """Torna quants n'hi ha a punt si cal avisar aquest compte (CA-10.1), o `None`."""
    if account is None or not getattr(account, "is_authenticated", False):
        return None
    if not _is_administrator(account):
        return None
    ready = ready_accounts().count()
    return ready if ready < MINIMUM else None


def record_use(account: Account, *, area: str, request=None) -> None:
    """CA-10.2: l'entrada d'un compte d'emergència queda al registre i s'avisa els altres comptes
    amb el rol administrador. No fa res amb cap altre compte."""
    if not account.is_emergency:
        return
    notified = list(roles.administrators_to_notify(exclude=account))
    when = timezone.now()
    for admin in notified:
        mail.queue_email(
            NOTICE_TEMPLATE,
            to=admin.notification_email,
            person=admin.person,
            context={"username": account.login, "when": when},
        )
    audit.record(
        USED,
        actor=account,
        target=account,
        details={"area": area, "notified": len(notified)},
        request=request,
    )
