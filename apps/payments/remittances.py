"""Remesa de quotes domiciliades: selecció, previsualització i confirmació (T-M05b-09;
P-M05b-E, passos 1 a 3; RN-M05b-10 i 11; CA-M05b-12, 13 i 16).

- Entren les quotes «pendent» que vencen com a molt el dia del cobrament, d'un soci que ha triat
  la domiciliació i té un mandat actiu, sense cap intent en curs (RN-M05b-10; quines quotes,
  [P-230](docs/decisions/pendents.md)), mai d'una persona esborrada ni amb un mandat bloquejat
  ([P-213](docs/decisions/pendents.md)). La resta surt a la llista d'excloses amb el motiu.
- Confirmar-la demana el nivell 2 (RN-M05a-11, `ensure_charges_allowed`) i una data de cobrament
  que deixi temps per a l'avís previ (RN-M05b-11, `payments.prenotification_days`).
- En confirmar-la, cada deutor rep l'avís previ per la cua (P-M05b-E, pas 4; CA-M05b-14).
- Marcar-la enviada (pas 6) i, quan arriba l'abonament, liquidar-la (pas 8; RN-M05b-13, RN-T24,
  CA-M05b-17 i CA-T16.1): cada càrrec «pagat» per domiciliació, l'ingrés al trànsit «Remeses
  SEPA», el rebut al soci i la liquidació a la 04, conciliada amb la línia del banc.
- Cap IBAN: la previsualització i el registre només porten la referència del mandat, i l'avís,
  l'IBAN emmascarat (P-121). Cap cobrament real: el fitxer pain.008 és de la T-M05b-10.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta

from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import audit, business_settings, charges, mail
from apps.core.imports import statement_lines
from apps.core.models import Charge, Payment, Person
from apps.core.permissions import has_perm
from apps.members import recipients
from apps.members import services as members
from apps.members.models import AnnualFee
from apps.treasury import reconciliation, settlements
from apps.treasury import services as treasury
from apps.treasury.models import StatementLineState

from . import attempts, receipts
from .guards import requires_charges
from .models import (
    DirectDebitItem,
    DirectDebitRemittance,
    FeeMethod,
    FeePaymentPreference,
    PaymentAttempt,
    SepaMandate,
)
from .returns import max_attempts

MANAGE = "payments.remittances"  # B3 (M05b-4)
PRENOTIFICATION_DAYS = "payments.prenotification_days"  # VC-16 (S-M05b-06)
PRENOTIFICATION_TEMPLATE = "avis-previ-remesa"
IN_FLIGHT = (PaymentAttempt.Status.IN_PROGRESS, PaymentAttempt.Status.SENT_TO_BANK)

# Motius d'exclusió de la previsualització.
ERASED = _("Dades personals esborrades")
NO_MANDATE = _("Sense mandat actiu")
NOT_DIRECT_DEBIT = _("No ha triat la domiciliació")
IN_PROGRESS = _("Té un pagament en curs o en una altra remesa")
EXHAUSTED = _("Intents esgotats")


class PrenotificationTooLate(Exception):
    """RN-M05b-11: la data de cobrament no deixa temps per a l'avís previ."""


class EmptyRemittance(Exception):
    """Cap quota per cobrar: no es crea cap remesa."""


class WrongStatus(Exception):
    """La remesa no és a l'estat que demana el pas (avisada per enviar-la, enviada per
    liquidar-la), o el fitxer no s'ha descarregat o esborrat."""


@dataclass
class Preview:
    included: list = field(default_factory=list)  # (quota, mandat)
    excluded: list = field(default_factory=list)  # (quota, motiu)

    @property
    def total_cents(self) -> int:
        return sum(fee.charge.amount_cents for fee, _mandate in self.included)


def earliest_collection_date(today: date | None = None) -> date:
    today = today or timezone.localdate()
    return today + timedelta(days=business_settings.get(PRENOTIFICATION_DAYS, today))


def preview(collection_date: date) -> Preview:
    """P-M05b-E, pas 1: els rebuts i les quotes excloses amb el motiu, sense desar res."""
    fees = list(
        AnnualFee.objects.filter(charge__status=Charge.Status.PENDING, due_on__lte=collection_date)
        .select_related("charge", "member__person")
        .order_by("member__member_number", "due_on", "pk")
    )
    members = {fee.member_id for fee in fees}
    debit = set(
        FeePaymentPreference.objects.filter(
            member__in=members, method=FeeMethod.DIRECT_DEBIT
        ).values_list("member_id", flat=True)
    )
    # El mandat actiu del soci, no el de la preferència: l'avís ha de portar la referència vigent
    # encara que un mandat s'hagi signat sense passar per la pantalla (dades de prova, P-125).
    mandates = {
        m.member_id: m
        for m in SepaMandate.objects.filter(member__in=members, status=SepaMandate.Status.ACTIVE)
    }
    busy = set(
        PaymentAttempt.objects.filter(
            charge__in=[fee.charge_id for fee in fees], status__in=IN_FLIGHT
        ).values_list("charge_id", flat=True)
    )
    # RN-M05b-15 i 30: cap càrrec rep més rebuts dels permesos (els anteriors són retornats).
    tries = Counter(
        DirectDebitItem.objects.filter(
            attempt__charge__in=[fee.charge_id for fee in fees]
        ).values_list("attempt__charge_id", flat=True)
    )
    limit = max_attempts()
    result = Preview()
    for fee in fees:
        mandate = mandates.get(fee.member_id)
        # P-213 (opció per defecte): mai una persona esborrada, encara que li quedi un mandat
        # actiu; un mandat bloquejat ja no és actiu (L-M05a-06).
        if fee.member.person.status == Person.Status.ANONYMISED:
            result.excluded.append((fee, ERASED))
        elif mandate is None:
            result.excluded.append((fee, NO_MANDATE))
        elif fee.member_id not in debit:
            result.excluded.append((fee, NOT_DIRECT_DEBIT))
        elif fee.charge_id in busy:
            result.excluded.append((fee, IN_PROGRESS))
        elif tries[fee.charge_id] >= limit:
            result.excluded.append((fee, EXHAUSTED))
        else:
            result.included.append((fee, mandate))
    return result


@requires_charges("build_remittance")  # CA-M05b-16: amb el nivell 1, cap remesa
@transaction.atomic
def build_remittance(period: str, collection_date: date, actor) -> DirectDebitRemittance:
    """P-M05b-E, passos 2 i 3: comprova el nivell 2 i el termini de l'avís previ i crea la
    remesa en esborrany, un rebut per quota i un intent «enviat al banc» per càrrec. Dos
    tresorers alhora: l'índex únic d'intents en curs (RN-M05b-04) fa fallar el segon."""
    if not has_perm(actor, MANAGE, write=True):  # B3, també al servei (T-M05b-25)
        raise Http404
    if collection_date < earliest_collection_date():
        raise PrenotificationTooLate
    selection = preview(collection_date)
    if not selection.included:
        raise EmptyRemittance
    remittance = DirectDebitRemittance.objects.create(
        period=period,
        collection_date=collection_date,
        item_count=len(selection.included),
        total_cents=selection.total_cents,
        created_by=actor,
    )
    for fee, mandate in selection.included:
        attempt = PaymentAttempt.objects.create(
            charge=fee.charge,
            method=PaymentAttempt.Method.DIRECT_DEBIT,
            amount_cents=fee.charge.amount_cents,
            started_by=actor,
        )
        attempts.transition(attempt, PaymentAttempt.Status.SENT_TO_BANK, by=actor)
        previous = DirectDebitItem.objects.filter(attempt__charge=fee.charge).count()
        DirectDebitItem.objects.create(
            remittance=remittance,
            attempt=attempt,
            mandate=mandate,
            amount_cents=attempt.amount_cents,
            end_to_end_id=f"R{remittance.pk:06d}C{fee.charge_id:08d}",
            attempt_number=previous + 1,
        )
    audit.record(
        "payments.remittance.created",
        actor=actor,
        target=remittance,
        details={
            "period": period,
            "collection_date": collection_date.isoformat(),
            "item_count": remittance.item_count,
            "total_cents": remittance.total_cents,
            "excluded": len(selection.excluded),
        },
    )
    send_prenotifications(remittance)
    remittance.refresh_from_db()
    return remittance


@transaction.atomic
def send_prenotifications(remittance: DirectDebitRemittance) -> list[DirectDebitItem]:
    """P-M05b-E, pas 4 (RN-M05b-11, CA-M05b-14): l'avís previ a cada deutor que encara no l'ha
    rebut, per la cua i dins la transacció. La remesa passa a «avisada» quan tots l'han rebut.
    Torna els rebuts sense avís (sense adreça o persona anonimitzada) perquè el tresorer avisi
    per una altra via ([P-232](docs/decisions/pendents.md)); es pot tornar a cridar."""
    remittance = DirectDebitRemittance.objects.select_for_update().get(pk=remittance.pk)
    items = remittance.items.filter(prenotified_at__isnull=True).select_related(
        "attempt__charge__person", "mandate__bank_account"
    )
    now, pending = timezone.now(), []
    for item in items:
        charge = item.attempt.charge
        to = recipients.email_for(charge.person)
        context = {
            "collection_date": remittance.collection_date,
            "amount": charges.euros(item.amount_cents),
            "concept": charge.concept,
            "reference": item.mandate.reference,
            "creditor": item.mandate.creditor_identifier,
            "masked_iban": str(item.mandate.bank_account),
        }
        if (
            not to
            or mail.queue_email(
                PRENOTIFICATION_TEMPLATE, to=to, person=charge.person, context=context
            )
            is None
        ):
            pending.append(item)
            continue
        item.prenotified_at = now
        item.save(update_fields=["prenotified_at"])
    if not pending and remittance.status == DirectDebitRemittance.Status.DRAFT:
        remittance.status = DirectDebitRemittance.Status.NOTIFIED
        remittance.save(update_fields=["status"])
    audit.record(
        "payments.remittance.prenotified",
        actor=audit.system("payments"),
        target=remittance,
        details={"sent": len(items) - len(pending), "without_notice": len(pending)},
    )
    return pending


@transaction.atomic
def mark_remittance_sent(remittance: DirectDebitRemittance, *, file_deleted: bool, by):
    """P-M05b-E, pas 6: el tresorer ha pujat el fitxer al banc i confirma que l'ha esborrat del
    dispositiu (044). Només una remesa avisada amb el fitxer descarregat."""
    if not has_perm(by, MANAGE, write=True):  # B3, també al servei (T-M05b-25)
        raise Http404
    remittance = DirectDebitRemittance.objects.select_for_update().get(pk=remittance.pk)
    if remittance.status != DirectDebitRemittance.Status.NOTIFIED or not remittance.file_hash:
        raise WrongStatus(remittance.status)
    if not file_deleted:
        raise WrongStatus("file_not_deleted")
    remittance.status = DirectDebitRemittance.Status.SENT_TO_BANK
    remittance.save(update_fields=["status"])
    audit.record(
        "payments.remittance.sent",
        actor=by,
        target=remittance,
        details={"sha256": remittance.file_hash, "file_deleted": True},
    )
    return remittance


def candidate_lines(remittance: DirectDebitRemittance, fees_cents: int = 0):
    """CA-T16.1: les línies obertes de l'extracte que poden ser l'abonament de la remesa: el net
    (total menys comissions) i a partir del dia del cobrament. Com abona el banc: P-237."""
    closed = StatementLineState.objects.exclude(status__in=reconciliation.OPEN)
    return (
        statement_lines()
        .filter(
            amount_cents=remittance.total_cents - fees_cents,
            value_date__gte=remittance.collection_date,
        )
        .exclude(pk__in=closed.values("statement_line"))
        .order_by("value_date", "pk")
    )


@requires_charges("settle_remittance")  # CA-M05b-17: amb el nivell 1, res no es liquida
@transaction.atomic
def settle_remittance(
    remittance: DirectDebitRemittance, line, *, fees_cents: int = 0, by
) -> DirectDebitRemittance:
    """P-M05b-E, pas 8 (CA-M05b-17, CA-T16.1): l'abonament de la línia `line` liquida la remesa,
    tot o res. Cada rebut: intent i càrrec «pagat» per domiciliació, l'ingrés al trànsit «Remeses
    SEPA», el rebut i el correu al soci, l'avís al 01 si és una quota i l'últim cobrament del
    mandat. Després, la liquidació a la 04 amb una partida per rebut, confirmada amb la línia
    (comissions i traspàs al banc; T4, que comprova la 04)."""
    if not has_perm(by, MANAGE, write=True):  # B3, també al servei (T-M05b-25)
        raise Http404
    remittance = DirectDebitRemittance.objects.select_for_update().get(pk=remittance.pk)
    if remittance.status != DirectDebitRemittance.Status.SENT_TO_BANK:
        raise WrongStatus(remittance.status)
    items = list(
        remittance.items.filter(status=DirectDebitItem.Status.INCLUDED)
        .select_related("attempt__charge", "mandate")
        .order_by("pk")
    )
    treasury.create_transit_account(treasury.SEPA_REMITTANCE, str(_("Remeses SEPA")), by=by)
    lines = []
    for item in items:
        attempt = attempts.transition(item.attempt, PaymentAttempt.Status.PAID, by=by)
        charge = attempt.charge
        payment = charges.record_payment(
            charge,
            method=Payment.Method.DIRECT_DEBIT,
            origin="reconciliation",
            by=by,
            provider_reference=item.end_to_end_id,
        )
        treasury.record_income(payment, origin="reconciliation", by=by)
        receipts.issue(attempt)
        fee = getattr(charge, "annual_fee", None)
        if fee is not None:
            members.on_fee_paid(fee.pk)
        item.status = DirectDebitItem.Status.COLLECTED
        item.save(update_fields=["status"])
        # El dia del càrrec al compte del deutor, per a la caducitat de 36 mesos (RN-M05a-08).
        item.mandate.last_collection_on = remittance.collection_date
        item.mandate.save(update_fields=["last_collection_on"])
        lines.append(settlements.SettlementLine(item.end_to_end_id, item.amount_cents))
    total = sum(line.amount_cents for line in lines)
    data = settlements.SettlementData(
        external_id=f"REM{remittance.pk:06d}",
        settled_on=line.value_date,
        gross_cents=total,
        fees_cents=fees_cents,
        net_cents=total - fees_cents,
        lines=tuple(lines),
    )
    settlement = settlements.record_settlement(
        treasury.SEPA_REMITTANCE, data, by=by, source="remittance"
    )
    settlements.confirm(settlement, by=by, statement_line=line)
    remittance.status = DirectDebitRemittance.Status.SETTLED
    remittance.save(update_fields=["status"])
    audit.record(
        "payments.remittance.settled",
        actor=by,
        target=remittance,
        details={"settlement": settlement.pk, "items": len(items), "fees_cents": fees_cents},
    )
    return remittance
