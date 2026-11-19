"""Liquidacions del proveïdor cap a la 04 (T-M05b-14; P-M05b-H; RN-T21; CA-T11.x).

Cada dia, la cua demana al proveïdor els abonaments al banc dels últims dies
(`list_settlements`), en tradueix cadascun a la forma de la 04 (`SettlementData`) i el desa amb
`treasury.settlements.record_settlement`. La 04 hi fa la resta: «a revisar» si una operació no
és d'un cobrament conegut (CA-T11.2) i, quan el tresorer la confirma, comissions i traspàs
(CA-T11.1). Com arriba la liquidació és [A verificar: P-45 punt 9]: aquí, una consulta diària
(P-226). Si el proveïdor no en dona, no es fa res i el tresorer casa per període (RN-T21).
"""

import logging
from datetime import timedelta

from django.utils import timezone

from apps.core import audit, mail
from apps.core.models import AuditEntry
from apps.core.permissions import accounts_with_perm
from apps.treasury import settlements as treasury

from .models import PaymentAttempt
from .providers import base, get_provider

logger = logging.getLogger(__name__)
ORIGIN = "payments.settlements"
REJECTED = "payments.settlement_rejected"
REJECTED_TEMPLATE = "avis-liquidacio-rebutjada"
TREASURY_PERMISSION = "treasury.view"  # T1, com l'avís d'un pagament a revisar
# Dies enrere que es tornen a demanar cada dia: una consulta que falla un dia es recupera
# l'endemà, i les que ja hi són es descarten (P-226).
LOOKBACK_DAYS = 7


def import_settlements(*, today=None) -> list:
    """Desa a la 04 els abonaments nous del proveïdor configurat i els torna. Idempotent: els
    que la 04 ja té es descarten. Un abonament que no quadra no es desa, queda al registre i, la
    primera vegada, s'avisa per correu qui té el permís de tresoreria (P-227, decisió 095); els
    altres continuen. Sense proveïdor, sense liquidacions o amb el proveïdor
    caigut, no es fa res (l'endemà es torna a provar)."""
    since = (today or timezone.localdate()) - timedelta(days=LOOKBACK_DAYS)
    by = audit.system(ORIGIN)
    try:
        provider = get_provider()
        reports = provider.list_settlements(since)
    except (base.ProviderNotConfigured, base.NotSupported):
        return []
    except base.ProviderError as error:
        logger.warning("No s'han pogut demanar les liquidacions al proveïdor: %s", error)
        return []
    recorded = []
    for report in reports:
        try:
            data = to_data(report, provider.code)
            recorded.append(treasury.record_settlement(provider.code, data, by=by))
        except treasury.DuplicateSettlement:
            continue
        except treasury.SettlementRejected as error:
            logger.warning("Liquidació %s rebutjada: %s", report.external_id, error.messages)
            _mail_rejected(provider.code, report.external_id, error.messages)
            audit.record(
                REJECTED,
                actor=by,
                details={
                    "provider": provider.code,
                    "external_id": report.external_id,
                    "errors": error.messages,
                },
            )
    return recorded


def _mail_rejected(provider_code: str, external_id: str, errors: list) -> None:
    """Un sol correu per liquidació i adreça: la consulta torna cada dia els darrers dies
    (P-226), i un rebuig que ja és al registre ja s'ha avisat. Cap dada personal."""
    already = AuditEntry.objects.filter(
        action=REJECTED, details__provider=provider_code, details__external_id=external_id
    ).exists()
    if already:
        return
    context = {"provider": provider_code, "external_id": external_id, "errors": errors}
    sent = set()
    for account in accounts_with_perm(TREASURY_PERMISSION):
        address = account.notification_email
        if address and address not in sent:
            mail.queue_email(REJECTED_TEMPLATE, to=address, person=account.person, context=context)
            sent.add(address)


def to_data(report: base.ProviderSettlementReport, provider_code: str) -> treasury.SettlementData:
    """La forma de la 04: cada operació és una línia amb la referència del pagament
    (`Payment.provider_reference`, l'identificador de l'ordre)."""
    return treasury.SettlementData(
        external_id=report.external_id,
        settled_on=report.settled_on,
        gross_cents=report.gross_cents,
        fees_cents=report.fees_cents,
        net_cents=report.net_cents,
        lines=tuple(
            treasury.SettlementLine(_reference(op, provider_code), op.amount_cents, op.fee_cents)
            for op in report.operations
        ),
    )


def _reference(op: base.SettledOperation, provider_code: str) -> str:
    """T-M05b-31: si l'operació porta la transacció del proveïdor, l'ordre de l'únic intent que
    la va desar; si no, la referència que porti. Una que no és de cap pagament la 04 la deixa «a
    revisar» (CA-T11.2)."""
    if op.transaction_id:
        orders = PaymentAttempt.objects.filter(
            provider_code=provider_code, provider_transaction_id=op.transaction_id
        ).values_list("provider_order_id", flat=True)[:2]
        if len(orders) == 1:
            return orders[0]
    return op.order_id or op.transaction_id
