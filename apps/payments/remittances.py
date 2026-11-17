"""Remesa de quotes domiciliades: selecció, previsualització i confirmació (T-M05b-09;
P-M05b-E, passos 1 a 3; RN-M05b-10 i 11; CA-M05b-12, 13 i 16).

- Entren les quotes «pendent» que vencen com a molt el dia del cobrament, d'un soci que ha triat
  la domiciliació i té un mandat actiu, sense cap intent en curs (RN-M05b-10; quines quotes,
  [P-230](docs/decisions/pendents.md)). La resta surt a la llista d'excloses amb el motiu.
- Confirmar-la demana el nivell 2 (RN-M05a-11, `ensure_charges_allowed`) i una data de cobrament
  que deixi temps per a l'avís previ (RN-M05b-11, `payments.prenotification_days`).
- En confirmar-la, cada deutor rep l'avís previ per la cua (P-M05b-E, pas 4; CA-M05b-14).
- Cap IBAN: la previsualització i el registre només porten la referència del mandat, i l'avís,
  l'IBAN emmascarat (P-121). Cap cobrament real: el fitxer pain.008 és de la T-M05b-10.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import audit, business_settings, charges, mail
from apps.core.models import Charge
from apps.members import recipients
from apps.members.models import AnnualFee

from . import attempts
from .models import (
    DirectDebitItem,
    DirectDebitRemittance,
    FeeMethod,
    FeePaymentPreference,
    PaymentAttempt,
    SepaMandate,
)
from .providers.base import ensure_charges_allowed

PRENOTIFICATION_DAYS = "payments.prenotification_days"  # VC-16 (S-M05b-06)
PRENOTIFICATION_TEMPLATE = "avis-previ-remesa"
IN_FLIGHT = (PaymentAttempt.Status.IN_PROGRESS, PaymentAttempt.Status.SENT_TO_BANK)

# Motius d'exclusió de la previsualització.
NO_MANDATE = _("Sense mandat actiu")
NOT_DIRECT_DEBIT = _("No ha triat la domiciliació")
IN_PROGRESS = _("Té un pagament en curs o en una altra remesa")


class PrenotificationTooLate(Exception):
    """RN-M05b-11: la data de cobrament no deixa temps per a l'avís previ."""


class EmptyRemittance(Exception):
    """Cap quota per cobrar: no es crea cap remesa."""


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
    # El mandat actiu del soci, no el de la preferència: signar-ne un de nou revoca l'anterior
    # sense tocar la preferència (P-125), i l'avís ha de portar la referència vigent.
    mandates = {
        m.member_id: m
        for m in SepaMandate.objects.filter(member__in=members, status=SepaMandate.Status.ACTIVE)
    }
    busy = set(
        PaymentAttempt.objects.filter(
            charge__in=[fee.charge_id for fee in fees], status__in=IN_FLIGHT
        ).values_list("charge_id", flat=True)
    )
    result = Preview()
    for fee in fees:
        mandate = mandates.get(fee.member_id)
        if mandate is None:
            result.excluded.append((fee, NO_MANDATE))
        elif fee.member_id not in debit:
            result.excluded.append((fee, NOT_DIRECT_DEBIT))
        elif fee.charge_id in busy:
            result.excluded.append((fee, IN_PROGRESS))
        else:
            result.included.append((fee, mandate))
    return result


@transaction.atomic
def build_remittance(period: str, collection_date: date, actor) -> DirectDebitRemittance:
    """P-M05b-E, passos 2 i 3: comprova el nivell 2 i el termini de l'avís previ i crea la
    remesa en esborrany, un rebut per quota i un intent «enviat al banc» per càrrec. Dos
    tresorers alhora: l'índex únic d'intents en curs (RN-M05b-04) fa fallar el segon."""
    ensure_charges_allowed()  # CA-M05b-16: amb el nivell 1, cap remesa
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
        # shortcut: sense retorns encara (T-M05b-11), cap càrrec torna a una remesa; el límit
        # de `max_direct_debit_attempts` (RN-M05b-15) s'hi afegeix amb els reintents.
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
