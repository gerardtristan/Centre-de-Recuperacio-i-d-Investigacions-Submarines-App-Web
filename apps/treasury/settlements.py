"""Liquidacions del proveïdor de cobrament (T-M04-13, primer tall; HU-T11; P-M04-F; RN-T21).

`record_settlement` (el crida el 05b) desa l'abonament agrupat; `fee_split` en dona la comissió de
cada cobrament (CA-T04.4); `confirm` apunta comissions i traspàs en casar el net (CA-T11.1). El
format real és [A verificar: P-45 punt 9]: `SettlementData` és la forma de la 04, i l'adaptador
de cada proveïdor (092) hi tradueix el seu. Proposar la línia del banc (T-M04-11/12) i les
remeses SEPA (RN-T24) són dels talls següents.
"""

from dataclasses import dataclass
from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.models import Payment, validate_cents
from apps.core.permissions import has_perm

from . import services
from .models import ProviderSettlement, SettlementItem, TreasuryAccount

RECORDED = "treasury.settlement_recorded"
CONFIRMED = "treasury.settlement_confirmed"
RECONCILE = "treasury.reconcile"  # T4: conciliar inclou les liquidacions (C5 del M04-3)
Status = ProviderSettlement.Status


@dataclass(frozen=True)
class SettlementLine:
    reference: str  # la referència del proveïdor del cobrament (`Payment.provider_reference`)
    amount_cents: int
    fee_cents: int | None = None  # només si el proveïdor la detalla (S-M04-05)


@dataclass(frozen=True)
class SettlementData:
    external_id: str
    settled_on: date
    gross_cents: int
    fees_cents: int
    net_cents: int
    lines: tuple[SettlementLine, ...]


class DuplicateSettlement(ValidationError):
    """Aquesta liquidació del proveïdor ja hi és."""


class SettlementRejected(ValidationError):
    """Les xifres de la liquidació no quadren, o ja no es pot confirmar."""


@transaction.atomic
def record_settlement(
    provider_code: str, data: SettlementData, *, by, source: str = "notification"
) -> ProviderSettlement:
    """Desa la liquidació i la torna: «rebuda», amb una partida per cobrament, o «a revisar»,
    sense partides i amb els problemes de cada línia. Unes xifres que no quadren es rebutgen
    sense desar res; una liquidació repetida, també (`DuplicateSettlement`)."""
    if not services._system_or_account(by):
        raise services.BrowserOriginRejected(_("Una liquidació l'apunta el sistema o un compte."))
    _check_totals(data)
    payments, problems = _match(provider_code, data.lines)
    try:
        with transaction.atomic():
            settlement = ProviderSettlement.objects.create(
                provider_code=provider_code,
                external_id=data.external_id,
                settled_on=data.settled_on,
                gross_cents=data.gross_cents,
                fees_cents=data.fees_cents,
                net_cents=data.net_cents,
                source=source,
                status=Status.TO_REVIEW if problems else Status.RECEIVED,
                review_notes=problems,
            )
    except IntegrityError:  # únic per proveïdor i identificador
        raise DuplicateSettlement(_("Aquesta liquidació ja està registrada.")) from None
    if not problems:
        SettlementItem.objects.bulk_create(
            SettlementItem(
                settlement=settlement,
                payment=payment,
                amount_cents=line.amount_cents,
                fee_cents=line.fee_cents,
            )
            for line, payment in zip(data.lines, payments, strict=True)
        )
    audit.record(
        RECORDED,
        actor=by,
        target=settlement,
        details={"provider": provider_code, "status": settlement.status, "problems": problems},
    )
    return settlement


def fee_split(settlement: ProviderSettlement) -> dict[SettlementItem, int]:
    """La comissió de cada partida: la que detalla el proveïdor o, si no, el repartiment
    proporcional de VT-05 (CA-T04.4)."""
    items = list(settlement.items.select_related("payment").order_by("pk"))
    if items and all(item.fee_cents is not None for item in items):
        return {item: item.fee_cents for item in items}
    shares = split(settlement.fees_cents, [item.amount_cents for item in items])
    return dict(zip(items, shares, strict=True))


def split(total: int, amounts: list[int]) -> list[int]:
    """VT-05 i LT9: cada part, proporcional a l'import i arrodonida a la baixa; els cèntims que
    sobren, un a un, a les partides més grans (a igual import, a la primera)."""
    gross = sum(amounts)
    shares = [total * amount // gross for amount in amounts]
    by_size = sorted(range(len(amounts)), key=lambda i: (-amounts[i], i))
    for i in by_size[: total - sum(shares)]:
        shares[i] += 1
    return shares


@transaction.atomic
def confirm(settlement: ProviderSettlement, *, by) -> ProviderSettlement:
    """Confirma una liquidació rebuda (P-M04-F, pas 4; CA-T11.1): la comissió de cada cobrament
    al seu departament (`record_fee`; si ja n'hi ha una d'un altre import, es rebutja tot, P-116)
    i el traspàs del net del trànsit del proveïdor al banc, en dues potes enllaçades. Tot o res.
    La crida la conciliació, amb T4 (RN-T16)."""
    if not has_perm(by, RECONCILE, write=True):
        raise Http404
    settlement = ProviderSettlement.objects.select_for_update().get(pk=settlement.pk)
    if settlement.status != Status.RECEIVED:
        raise SettlementRejected(_("Només es confirma una liquidació rebuda i sense problemes."))
    transit = _single(kind=TreasuryAccount.Kind.TRANSIT, provider_code=settlement.provider_code)
    bank = _single(kind=TreasuryAccount.Kind.BANK)
    for item, fee in fee_split(settlement).items():
        if fee:
            services.record_fee(item.payment, fee, by=by)
    concept = _("Liquidació %(provider)s %(id)s") % {
        "provider": settlement.provider_code,
        "id": settlement.external_id,
    }
    services.transfer_legs(
        transit,
        bank,
        settlement.net_cents,
        value_date=settlement.settled_on,
        concept=concept[:140],
        by=by,
        settlement=settlement,
    )
    settlement.status = Status.RECONCILED
    settlement.save(update_fields=["status"])
    audit.record(
        CONFIRMED,
        actor=by,
        target=settlement,
        details={"net_cents": settlement.net_cents, "fees_cents": settlement.fees_cents},
    )
    return settlement


def _check_totals(data: SettlementData) -> None:
    try:
        validate_cents(data.gross_cents)
        validate_cents(data.net_cents)
        for line in data.lines:
            validate_cents(line.amount_cents)
    except ValidationError as error:
        raise SettlementRejected(error.messages) from None
    fees = [data.fees_cents] + [line.fee_cents for line in data.lines if line.fee_cents is not None]
    if any(isinstance(fee, bool) or not isinstance(fee, int) or fee < 0 for fee in fees):
        raise SettlementRejected(_("Les comissions han de ser enters de cèntims, zero o més."))
    detailed = {line.fee_cents is not None for line in data.lines}
    if (
        not data.lines
        or data.net_cents != data.gross_cents - data.fees_cents
        or sum(line.amount_cents for line in data.lines) != data.gross_cents
        or detailed == {True, False}
        or (detailed == {True} and sum(line.fee_cents for line in data.lines) != data.fees_cents)
    ):
        raise SettlementRejected(_("Les xifres de la liquidació no quadren."))


def _match(provider_code: str, lines) -> tuple[list[Payment], list[dict]]:
    """El cobrament de cada línia i els problemes (CA-T11.2, LT8): ha de ser un sol pagament
    amb aquesta referència, amb l'ingrés vigent al trànsit del proveïdor, del mateix import,
    sense devolucions ni retorn i en cap altra liquidació."""
    payments, problems, seen = [], [], set()
    for line in lines:
        found = list(Payment.objects.filter(provider_reference=line.reference)[:2])
        payment = found[0] if len(found) == 1 else None
        income = services._income_of(payment) if payment else None
        if payment is None:
            problem = "unknown_payment"
        elif line.reference in seen:
            problem = "repeated_line"
        elif income is None or income.is_reversed or income.account.provider_code != provider_code:
            problem = "no_income"
        elif line.amount_cents != payment.amount_cents:
            problem = "amount_mismatch"
        elif services._given_back(payment):
            problem = "refunded"
        elif SettlementItem.objects.filter(payment=payment).exists():
            problem = "already_settled"
        else:
            problem = None
        seen.add(line.reference)
        payments.append(payment)
        if problem:
            problems.append({"reference": line.reference, "problem": problem})
    return payments, problems


def _single(**filters) -> TreasuryAccount:
    found = list(TreasuryAccount.objects.filter(active=True, **filters)[:2])
    if len(found) != 1:
        raise SettlementRejected(_("No hi ha un únic compte actiu per a aquesta liquidació."))
    return found[0]
