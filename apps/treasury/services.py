"""Serveis de la tresoreria (M04-8). Cap altra app escriu als models de la 04: crida aquests
serveis. Cap ruta hi arriba: un ingrés mai neix d'una petició del navegador (RN-71, CA-T03.4).

`record_income` (T-M04-05; P-M04-A; CA-T03.x): l'ingrés d'un cobrament confirmat. El criden el
05b, en processar una notificació verificada, i la mateixa 04, en confirmar una conciliació.
- Idempotent (RN-T09, LT1): la base de dades només admet un ingrés per pagament (restricció
  `movement_one_income_per_payment`). La repetició torna l'ingrés que ja hi era i queda al registre.
- El càrrec i el pagament només es llegeixen, i de la base de dades: la còpia de qui crida pot
  ser antiga.
- Data de valor en un període tancat (RN-T31): arriba amb la T-M04-20.

`create_transit_account` (T-M04-17; RN-T01 i RN-T08): el compte de trànsit d'un proveïdor de
cobrament. El crida el 05a quan es configura el proveïdor (`apps/payments/setup.py`).
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.charges import PAID_ORIGINS
from apps.core.models import AuditEntry, Charge, Payment
from apps.members import services as members

from .models import Movement, TreasuryAccount

INCOME_RECORDED = "treasury.income_recorded"
INCOME_REPEATED = "treasury.income_repeated"
TRANSIT_ACCOUNT_CREATED = "treasury.transit_account_created"

# Codi del compte de trànsit de les remeses SEPA (RN-T24; exemple de M04-6). El crea el 05a.
SEPA_REMITTANCE = "sepa_remittance"


class ChargeNotPaid(ValidationError):
    """El càrrec del pagament no és «pagat» (CA-T03.3)."""


class BrowserOriginRejected(ValidationError):
    """L'ingrés no ve del proveïdor ni d'una conciliació confirmada (RN-71, CA-T03.4)."""


class IncomeAccountUnavailable(ValidationError):
    """No hi ha un únic compte actiu on apuntar l'ingrés d'aquest mètode (RN-T08)."""


@transaction.atomic
def record_income(payment: Payment, *, origin: str, by) -> Movement:
    """Apunta l'ingrés d'un pagament amb el càrrec «pagat» i el torna; si ja hi era, torna
    l'existent sense crear res (CA-T03.1 i CA-T03.2). `origin` i `by`, com a
    `charges.mark_paid`: «provider» o «reconciliation», i el sistema o el tresorer."""
    if origin not in PAID_ORIGINS:
        raise BrowserOriginRejected(
            _("Un ingrés només s'apunta des del proveïdor o des de la conciliació.")
        )
    if not _system_or_account(by):
        # RN-T13: el registre ha de dir qui. Ni anònim ni un convidat (que ve del navegador).
        raise BrowserOriginRejected(_("Un ingrés l'apunta el sistema o un compte, mai ningú més."))
    payment = Payment.objects.select_related("charge__department", "charge__cost_centre").get(
        pk=payment.pk
    )
    charge = payment.charge
    if charge.status != Charge.Status.PAID:
        raise ChargeNotPaid(_("Només s'apunta l'ingrés d'un càrrec «pagat»."))
    movement = _income_of(payment)
    if movement is None:
        try:
            # En un punt de desament: si la base de dades rebutja el duplicat, la transacció de
            # qui crida continua.
            with transaction.atomic():
                movement = _create_income(payment, charge, by)
        except IntegrityError:
            # Una altra crida ha apuntat l'ingrés entre la comprovació i la inserció.
            movement = _income_of(payment)
            if movement is None:
                raise
        else:
            audit.record(
                INCOME_RECORDED,
                actor=by,
                target=movement,
                details={
                    "payment": payment.pk,
                    "charge": charge.pk,
                    "amount_cents": movement.amount_cents,
                    "account": movement.account.name,
                    "origin": origin,
                },
            )
            return movement
    audit.record(
        INCOME_REPEATED,
        actor=by,
        target=movement,
        details={"payment": payment.pk, "origin": origin},
    )
    return movement


@transaction.atomic
def create_transit_account(provider_code: str, name: str, *, by=None) -> TreasuryAccount:
    """El compte de trànsit del proveïdor, o l'existent (M04-8). Idempotent: la base de dades
    només admet un trànsit per proveïdor, i el que ja hi és es torna tal com és, sense
    reanomenar-lo ni reactivar-lo (desactivar-lo és cosa del tresorer). Un nom que ja fa servir
    un altre compte és un error de configuració i no es tapa (`IntegrityError`).
    `by` (un compte o el sistema) queda al registre d'activitat. Sense `by`, el crea la
    instal·lació en acabar `migrate` i, com els comptes inicials de les migracions, no hi deixa
    cap entrada (P-88)."""
    account, created = TreasuryAccount.objects.get_or_create(
        kind=TreasuryAccount.Kind.TRANSIT, provider_code=provider_code, defaults={"name": name}
    )
    if created and by is not None:
        audit.record(
            TRANSIT_ACCOUNT_CREATED,
            actor=by,
            target=account,
            details={"provider_code": provider_code, "name": name},
        )
    return account


def _system_or_account(by) -> bool:
    if isinstance(by, audit.Actor):
        return by.kind == AuditEntry.ActorKind.SYSTEM
    return isinstance(by, get_user_model())


def _income_of(payment: Payment) -> Movement | None:
    return Movement.objects.filter(payment=payment, kind=Movement.Kind.INCOME).first()


def _create_income(payment: Payment, charge: Charge, by) -> Movement:
    paid_on = timezone.localdate(payment.paid_at) if payment.paid_at else timezone.localdate()
    return Movement.objects.create(
        account=_income_account(payment.method),
        direction=Movement.Direction.IN,
        amount_cents=payment.amount_cents,
        value_date=paid_on,
        kind=Movement.Kind.INCOME,
        concept=_concept(charge),
        department=charge.department,
        cost_centre=charge.cost_centre,  # RN-T10
        payment=payment,
        # Sense compte: l'ha apuntat el sistema (una notificació del proveïdor).
        recorded_by=by if isinstance(by, get_user_model()) else None,
    )


def _income_account(method: str) -> TreasuryAccount:
    """RN-T08. Ha de ser un sol compte i actiu: si no, l'ingrés no s'apunta enlloc."""
    kind, method_of = TreasuryAccount.Kind, Payment.Method
    accounts = TreasuryAccount.objects.filter(active=True)
    if method in (method_of.CARD, method_of.BIZUM):
        accounts = accounts.filter(kind=kind.TRANSIT, provider_code=settings.PAYMENTS_PROVIDER)
    elif method == method_of.DIRECT_DEBIT:
        accounts = accounts.filter(kind=kind.TRANSIT, provider_code=SEPA_REMITTANCE)
    elif method == method_of.TRANSFER:
        accounts = accounts.filter(kind=kind.BANK)
    else:  # Manual: «caixa o bancari (quan es resolgui P-12)».
        accounts = accounts.none()
    found = list(accounts[:2])
    if len(found) != 1:
        raise IncomeAccountUnavailable(
            _("No hi ha un únic compte de tresoreria actiu per a aquest mètode de pagament.")
        )
    return found[0]


def _concept(charge: Charge) -> str:
    """RNF-T4: tipus, número de soci i referència del càrrec; mai el nom ni el text lliure."""
    parts = [charge.get_kind_display()]
    try:
        number = members.get_member_summary(charge.person).number
    except members.NotAMember:
        number = None
    if number:
        parts.append(_("soci %(number)s") % {"number": number})
    parts.append(_("càrrec %(id)s") % {"id": charge.pk})
    return " · ".join(parts)
