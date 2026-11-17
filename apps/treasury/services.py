"""Serveis de la tresoreria (M04-8). Cap altra app escriu als models de la 04: crida aquests
serveis. Cap ruta hi arriba: un ingrés mai neix d'una petició del navegador (RN-71, CA-T03.4).

`record_income` (T-M04-05; P-M04-A; CA-T03.x): l'ingrés d'un cobrament confirmat. El criden el
05b, en processar una notificació verificada, i la mateixa 04, en confirmar una conciliació.
- Idempotent (RN-T09, LT1): la base de dades només admet un ingrés per pagament (restricció
  `movement_one_income_per_payment`). La repetició torna l'ingrés que ja hi era i queda al registre.
- El càrrec i el pagament només es llegeixen, i de la base de dades: la còpia de qui crida pot
  ser antiga.
- Data de valor en un període tancat (RN-T31): arriba amb la T-M04-20.

`record_fee` (T-M04-06; P-M04-A, pas 3; RN-T10; CA-T04.1 a CA-T04.3): la comissió coneguda d'un
cobrament, com a sortida del compte on va entrar l'ingrés, amb el departament i el centre de cost
del càrrec. L'import el dona el proveïdor: la plataforma no en calcula cap.

`record_refund` i `record_return` (T-M04-07; P-M04-B; RN-T11; CA-T05.1 a CA-T05.4): una devolució
que fa el club o un rebut retornat, com a sortides noves; el càrrec el canvia el 05b.

`create_transit_account` (T-M04-17; RN-T01 i RN-T08): el compte de trànsit d'un proveïdor de
cobrament. El crida el 05a quan es configura el proveïdor (`apps/payments/setup.py`).

`reverse` (T-M04-08; P-M04-C; RN-T27): l'anul·lació amb contramoviment, manual (T5) o en desfer
una conciliació (045). El període tancat (RN-T28, RN-T30) arriba amb la T-M04-20.

`record_transfer` i `record_cash_count` (T-M04-09; P-M04-D; CA-T07.1 i CA-T08.1): el traspàs entre
comptes propis (T6) i l'arqueig de la caixa (T7), amb l'ajust opcional. El període tancat dels
dos (RN-T31: mai es rebutgen) arriba amb la T-M04-20.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.charges import PAID_ORIGINS
from apps.core.models import AuditEntry, Charge, Payment, validate_cents
from apps.core.permissions import has_perm
from apps.members import services as members

from .balances import balance
from .models import CashCount, CostCentre, Movement, TreasuryAccount
from .references import transfer_reference  # noqa: F401 (servei de M04-8, T-M04-10)

INCOME_RECORDED = "treasury.income_recorded"
INCOME_REPEATED = "treasury.income_repeated"
FEE_RECORDED = "treasury.fee_recorded"
FEE_REPEATED = "treasury.fee_repeated"
REFUND_RECORDED = "treasury.refund_recorded"
RETURN_RECORDED = "treasury.return_recorded"
TRANSIT_ACCOUNT_CREATED = "treasury.transit_account_created"
MOVEMENT_REVERSED = "treasury.movement_reversed"
REVERSE = "treasury.reverse"  # T5, «Anul·lar un moviment amb motiu» (M04-4)
MANUAL, RECONCILIATION = "manual", "reconciliation"  # qui demana `reverse`
TRANSFER_RECORDED = "treasury.transfer_recorded"
CASH_COUNTED = "treasury.cash_counted"
TRANSFER = "treasury.transfer"  # T6, «Registrar un traspàs» (M04-4)
CASH_COUNT = "treasury.cash_count"  # T7, «Registrar un arqueig» (M04-4)
# VT-06: el centre de cost dels ajustos d'arqueig (dades inicials, migració 0004).
CASH_ADJUSTMENTS = ("General", "Ajustos de caixa")

# Codi del compte de trànsit de les remeses SEPA (RN-T24; exemple de M04-6). El crea el 05a.
SEPA_REMITTANCE = "sepa_remittance"


class ChargeNotPaid(ValidationError):
    """El càrrec del pagament no és «pagat» (CA-T03.3)."""


class BrowserOriginRejected(ValidationError):
    """L'ingrés no ve del proveïdor ni d'una conciliació confirmada (RN-71, CA-T03.4)."""


class IncomeAccountUnavailable(ValidationError):
    """No hi ha un únic compte actiu on apuntar l'ingrés d'aquest mètode (RN-T08)."""


class InvalidAmount(ValidationError):
    """La comissió no és un enter positiu de cèntims o passa de l'import cobrat."""


class IncomeNotRecorded(ValidationError):
    """El pagament no té cap ingrés vigent: la comissió no té d'on sortir (P-M04-A)."""


class FeeAlreadyRecorded(ValidationError):
    """El pagament ja té una comissió vigent d'un altre import (P-116)."""


class RefundExceedsPaid(ValidationError):
    """Les devolucions i el retorn passarien de l'import cobrat (RN-T11, CA-T05.4; P-118)."""


class AlreadyReturned(ValidationError):
    """El pagament ja té un retorn vigent."""


class AlreadyReversed(ValidationError):
    """El moviment ja té contramoviment: només s'anul·la una vegada (RN-T27, CA-T17.1)."""


class NotReversible(ValidationError):
    """Aquest moviment no s'anul·la per aquest camí (CA-T06.2; P-114; P-115)."""


class TransferRejected(ValidationError):
    """El traspàs no és entre dos comptes propis diferents, o li falta alguna dada (RN-T12)."""


class CashCountRejected(ValidationError):
    """L'arqueig no és d'un compte de caixa, o l'ajust no es pot fer."""


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
def record_fee(payment: Payment, amount_cents: int, *, by) -> Movement:
    """Apunta la comissió coneguda d'un pagament i la torna (HU-T04; CA-T04.1 a CA-T04.3): una
    sortida del compte del seu ingrés, amb la data de valor, el departament i el centre de cost
    de l'ingrés, que són els del càrrec (RN-T10): una quota, a «General / Quotes de socis»; una
    inscripció, al de l'activitat; una llicència, a «General / Llicències» (RN-M06-10, VT-04).
    Idempotent: si el pagament ja en té una del mateix import, la torna sense crear-ne cap; d'un
    altre import, es rebutja (P-116). La comissió d'una liquidació és de la T-M04-13; la d'un
    retorn l'apunta `record_return`, enllaçada al retorn, i aquí no compta."""
    _validate_amount(amount_cents)
    payment, income = _live_income(payment, by)
    if amount_cents > payment.amount_cents:
        raise InvalidAmount(_("La comissió no pot passar de l'import cobrat."))
    fee = _live(payment, Movement.Kind.FEE).filter(linked_movement__isnull=True).first()
    if fee is not None:
        if fee.amount_cents != amount_cents:
            raise FeeAlreadyRecorded(_("Aquest pagament ja té una comissió d'un altre import."))
        audit.record(FEE_REPEATED, actor=by, target=fee, details={"payment": payment.pk})
        return fee
    fee = _outgoing(income, Movement.Kind.FEE, amount_cents, by, value_date=income.value_date)
    _record(FEE_RECORDED, by, fee)
    return fee


@transaction.atomic
def record_refund(payment: Payment, amount_cents: int, *, reason: str, by) -> Movement:
    """Apunta una devolució que ha fet el club, total o parcial (HU-T05; P-M04-B; CA-T05.1,
    CA-T05.2 i CA-T05.4): una sortida nova del compte de l'ingrés, amb el seu departament i
    centre de cost i data d'avui. L'ingrés no canvia i la comissió no es retorna (RN-T11). La
    suma de les devolucions i el retorn vigents no passa mai de l'import cobrat (P-118). El
    càrrec el canvia qui crida (05b, RN-M05b-17)."""
    _validate_amount(amount_cents)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Una devolució necessita el motiu."))
    payment, income = _live_income(payment, by)
    if _given_back(payment) + amount_cents > income.amount_cents:
        raise RefundExceedsPaid(_("La suma de les devolucions passaria de l'import cobrat."))
    refund = _outgoing(income, Movement.Kind.REFUND, amount_cents, by, reason=reason)
    _record(REFUND_RECORDED, by, refund, reason=reason)
    return refund


@transaction.atomic
def record_return(payment: Payment, fee_cents: int | None = None, *, by) -> Movement:
    """Apunta un rebut retornat o un contracàrrec (HU-T05; P-M04-B; CA-T05.3): una sortida de
    tot l'import cobrat del compte de l'ingrés, amb el seu departament i centre de cost i data
    d'avui, i, si n'hi ha, la comissió de retorn al mateix compte i departament, enllaçada al
    retorn. Un pagament només es retorna una vegada (`AlreadyReturned`), i mai si ja té
    devolucions (P-118). El càrrec el canvia qui crida (05b, P-M05b-F)."""
    if fee_cents is not None:
        _validate_amount(fee_cents)
    payment, income = _live_income(payment, by)
    if _live(payment, Movement.Kind.RETURN).exists():
        raise AlreadyReturned(_("Aquest pagament ja està retornat."))
    if _given_back(payment):
        raise RefundExceedsPaid(_("Aquest pagament ja té devolucions: el retorn s'ha de revisar."))
    returned = _outgoing(income, Movement.Kind.RETURN, income.amount_cents, by)
    _record(RETURN_RECORDED, by, returned)
    if fee_cents is not None:
        fee = _outgoing(income, Movement.Kind.FEE, fee_cents, by, linked=returned)
        _record(FEE_RECORDED, by, fee)
    return returned


def _validate_amount(amount_cents) -> None:
    try:
        validate_cents(amount_cents)
    except ValidationError as error:
        raise InvalidAmount(error.messages) from None


def _live_income(payment: Payment, by) -> tuple[Payment, Movement]:
    """El pagament, amb el pany (dues crides alhora no apunten res dues vegades), i el seu
    ingrés vigent: sense ingrés no hi ha res a descomptar (P-M04-A)."""
    if not _system_or_account(by):
        raise BrowserOriginRejected(_("Aquest moviment l'apunta el sistema o un compte."))
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    income = _income_of(payment)
    if income is None or income.is_reversed:
        raise IncomeNotRecorded(_("Aquest pagament no té cap ingrés vigent."))
    return payment, income


def _live(payment: Payment, *kinds):
    """Els moviments del pagament d'aquests tipus que no estan anul·lats (RN-T25)."""
    return Movement.objects.filter(payment=payment, kind__in=kinds, reversal__isnull=True)


def _given_back(payment: Payment) -> int:
    """Cèntims ja retornats al pagador: devolucions i retorn vigents (RN-T11, P-118)."""
    rows = _live(payment, Movement.Kind.REFUND, Movement.Kind.RETURN)
    return rows.aggregate(total=Sum("amount_cents"))["total"] or 0


def _outgoing(income, kind, amount_cents, by, *, value_date=None, reason="", linked=None):
    """Sortida del compte de l'ingrés, amb el seu departament i centre de cost (RN-T10).
    RN-T31: la data de valor dins un període tancat passa al període obert (T-M04-20)."""
    return Movement.objects.create(
        account=income.account,
        direction=Movement.Direction.OUT,
        amount_cents=amount_cents,
        value_date=value_date or timezone.localdate(),
        kind=kind,
        concept=f"{Movement.Kind(kind).label} · {income.concept}"[:140],
        department=income.department,
        cost_centre=income.cost_centre,
        payment=income.payment,
        linked_movement=linked,
        reason=reason,
        recorded_by=by if isinstance(by, get_user_model()) else None,
    )


def _record(action, by, movement, reason=""):
    audit.record(
        action,
        actor=by,
        target=movement,
        reason=reason,
        details={
            "payment": movement.payment_id,
            "amount_cents": movement.amount_cents,
            "account": movement.account.name,
            "cost_centre": movement.cost_centre.full_name if movement.cost_centre else None,
        },
    )


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


@transaction.atomic
def reverse(movement: Movement, *, reason: str, by, origin: str = MANUAL) -> Movement:
    """Anul·la un moviment amb motiu (T-M04-08; P-M04-C; RN-T07, RN-T25, RN-T27; CA-T06.1): el
    contramoviment mirall (mateix compte, import, departament i centre de cost; sentit contrari;
    enllaçat amb `reverses`) amb data d'avui (RN-T29). L'original no es toca i es mostra anul·lat.
    `origin`: «manual» (una persona amb T5, des de la pantalla o el 09) o «reconciliation»
    (`reconciliation.undo`, que ja ha comprovat T4 i només hi passa ingressos de cobrament)."""
    if origin not in (MANUAL, RECONCILIATION):
        raise ValueError(origin)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Per anul·lar un moviment cal escriure'n el motiu."))
    if origin == MANUAL and not has_perm(by, REVERSE, write=True):
        raise Http404
    movement = Movement.objects.get(pk=movement.pk)
    if movement.is_reversed:
        raise AlreadyReversed(_("Aquest moviment ja està anul·lat."))
    if origin == MANUAL:
        _ensure_manually_reversible(movement)
        # RN-T28 i RN-T30: aquí va el bloqueig de període tancat (`PeriodClosed`), només per a
        # l'anul·lació manual; el de la conciliació és d'origen extern i mai es rebutja (RN-T31).
        # Arriba amb la T-M04-20 (`register_movement_guard`): fins llavors no hi ha períodes.
    elif movement.kind != Movement.Kind.INCOME:
        raise NotReversible(_("Desfer una conciliació només anul·la ingressos de cobrament."))
    try:
        with transaction.atomic():
            reversal = Movement.objects.create(
                account=movement.account,
                direction=_OPPOSITE[movement.direction],
                amount_cents=movement.amount_cents,
                value_date=timezone.localdate(),
                kind=Movement.Kind.REVERSAL,
                concept=movement.concept,
                department=movement.department,
                cost_centre=movement.cost_centre,
                reverses=movement,
                reason=reason,
                recorded_by=by,
            )
    except IntegrityError:
        # Una altra anul·lació ha entrat entre la comprovació i la inserció (OneToOne).
        if Movement.objects.filter(reverses=movement).exists():
            raise AlreadyReversed(_("Aquest moviment ja està anul·lat.")) from None
        raise
    audit.record(
        MOVEMENT_REVERSED,
        actor=by,
        target=reversal,
        reason=reason,
        details={
            "reverses": movement.pk,
            "kind": movement.kind,
            "amount_cents": movement.amount_cents,
            "origin": origin,
        },
    )
    return reversal


_OPPOSITE = {
    Movement.Direction.IN: Movement.Direction.OUT,
    Movement.Direction.OUT: Movement.Direction.IN,
}


def _ensure_manually_reversible(movement: Movement) -> None:
    kind = Movement.Kind
    if movement.kind == kind.INCOME:
        # CA-T06.2: es fa amb una devolució (05b) o desfent la conciliació.
        raise NotReversible(
            _("Un ingrés de cobrament no s'anul·la: cal una devolució o desfer la conciliació.")
        )
    if movement.kind == kind.REVERSAL:
        # P-115 (opció conservadora): desfer una anul·lació no és cap correcció prevista.
        raise NotReversible(_("Un contramoviment no s'anul·la."))
    if movement.kind == kind.TRANSFER:
        # P-114 (opció conservadora): una pota sola desquadraria els dos comptes.
        raise NotReversible(_("Una pota d'un traspàs no s'anul·la sola."))


@transaction.atomic
def record_transfer(
    source: TreasuryAccount,
    destination: TreasuryAccount,
    amount_cents: int,
    *,
    value_date,
    concept: str,
    by,
) -> tuple[Movement, Movement]:
    """Registra un traspàs entre dos comptes propis, bancaris o de caixa (HU-T07; P-M04-D;
    CA-T07.1): una sortida de l'origen i una entrada a la destinació, enllaçades, del mateix
    import i sense departament (RN-T12). Torna les dues potes (sortida, entrada). Un trànsit no
    hi entra: el buida la liquidació (P-222). Una data futura es rebutja (P-224). Es corregeix
    amb un traspàs en sentit contrari (P-114)."""
    if not has_perm(by, TRANSFER, write=True):
        raise Http404
    _validate_amount(amount_cents)
    concept = (concept or "").strip()
    if not concept or len(concept) > 140:
        raise TransferRejected(_("Un traspàs necessita un concepte de 140 caràcters com a màxim."))
    if value_date > timezone.localdate():
        raise TransferRejected(_("Un traspàs no pot tenir una data de valor futura."))
    own = {TreasuryAccount.Kind.BANK, TreasuryAccount.Kind.CASH}
    if source.pk == destination.pk or {source.kind, destination.kind} - own:
        raise TransferRejected(_("Un traspàs és entre dos comptes propis diferents."))
    out, entry = transfer_legs(
        source, destination, amount_cents, value_date=value_date, concept=concept, by=by
    )
    audit.record(
        TRANSFER_RECORDED,
        actor=by,
        target=out,
        details={
            "from": out.account.name,
            "to": entry.account.name,
            "amount_cents": amount_cents,
            "value_date": value_date.isoformat(),
            "legs": [out.pk, entry.pk],
        },
    )
    return out, entry


def transfer_legs(source, destination, amount_cents, *, value_date, concept, by, settlement=None):
    """Les dues potes d'un traspàs, sense comprovar cap permís: ho fa qui crida (`record_transfer`
    amb T6, `settlements.confirm` amb T4). La segona apunta la primera (`linked_movement`).
    Bloqueja els dos comptes, en ordre (sense interbloquejos), contra un arqueig simultani."""
    pks = [source.pk, destination.pk]
    list(TreasuryAccount.objects.select_for_update().filter(pk__in=pks).order_by("pk"))
    leg = {
        "amount_cents": amount_cents,
        "value_date": value_date,
        "kind": Movement.Kind.TRANSFER,
        "concept": concept,
        "settlement": settlement,
        "recorded_by": by if isinstance(by, get_user_model()) else None,
    }
    out = Movement.objects.create(account=source, direction=Movement.Direction.OUT, **leg)
    entry = Movement.objects.create(
        account=destination, direction=Movement.Direction.IN, linked_movement=out, **leg
    )
    return out, entry


@transaction.atomic
def record_cash_count(
    account: TreasuryAccount, counted_cents: int, *, counted_on, by, adjustment_reason: str = ""
) -> CashCount:
    """Registra l'arqueig d'una caixa (HU-T08; P-M04-D; CA-T08.1): el saldo calculat a
    `counted_on` i la diferència (comptat − calculat). Sense `adjustment_reason`, cap moviment.
    Amb motiu i diferència, l'ajust a «General / Ajustos de caixa» (VT-06) amb la data de
    l'arqueig, que deixa el saldo igual al comptat, i l'arqueig el porta. L'ajust es demana en la
    mateixa crida, perquè l'arqueig no es modifica (P-225). Una data futura es rebutja (P-224)."""
    if not has_perm(by, CASH_COUNT, write=True):
        raise Http404
    if isinstance(counted_cents, bool) or not isinstance(counted_cents, int) or counted_cents < 0:
        raise InvalidAmount(_("L'import comptat ha de ser un enter de cèntims, zero o més."))
    if counted_on > timezone.localdate():
        raise CashCountRejected(_("Un arqueig no pot tenir una data futura."))
    # El pany: dos arqueigs alhora no fan dos ajustos de la mateixa diferència.
    account = TreasuryAccount.objects.select_for_update().get(pk=account.pk)
    if account.kind != TreasuryAccount.Kind.CASH:
        raise CashCountRejected(_("L'arqueig només es fa d'un compte de caixa."))
    computed = balance(account, counted_on)
    difference = counted_cents - computed
    reason = (adjustment_reason or "").strip()
    adjustment = None
    if reason:
        if not difference:
            raise CashCountRejected(_("No hi ha cap diferència per ajustar."))
        department, name = CASH_ADJUSTMENTS
        centre = CostCentre.selectable().get(department__name=department, name=name)
        adjustment = Movement.objects.create(
            account=account,
            direction=Movement.Direction.IN if difference > 0 else Movement.Direction.OUT,
            amount_cents=abs(difference),
            value_date=counted_on,
            kind=Movement.Kind.CASH_ADJUSTMENT,
            concept=_("Ajust d'arqueig del %(date)s") % {"date": counted_on.strftime("%d/%m/%Y")},
            department=centre.department,
            cost_centre=centre,
            reason=reason,
            recorded_by=by,
        )
    count = CashCount.objects.create(
        account=account,
        counted_on=counted_on,
        counted_cents=counted_cents,
        computed_cents=computed,
        difference_cents=difference,
        adjustment=adjustment,
        recorded_by=by,
    )
    audit.record(
        CASH_COUNTED,
        actor=by,
        target=count,
        reason=reason,
        details={
            "account": account.name,
            "counted_on": counted_on.isoformat(),
            "counted_cents": counted_cents,
            "computed_cents": computed,
            "difference_cents": difference,
            "adjustment": adjustment.pk if adjustment else None,
        },
    )
    return count
