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

from apps.core import audit
from apps.treasury import settlements as treasury

from .providers import base, get_provider

logger = logging.getLogger(__name__)
ORIGIN = "payments.settlements"
REJECTED = "payments.settlement_rejected"
# Dies enrere que es tornen a demanar cada dia: una consulta que falla un dia es recupera
# l'endemà, i les que ja hi són es descarten (P-226).
LOOKBACK_DAYS = 7


def import_settlements(*, today=None) -> list:
    """Desa a la 04 els abonaments nous del proveïdor configurat i els torna. Idempotent: els
    que la 04 ja té es descarten. Un abonament que no quadra no es desa i queda al registre
    (P-227); els altres continuen. Sense proveïdor, sense liquidacions o amb el proveïdor
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
            recorded.append(treasury.record_settlement(provider.code, to_data(report), by=by))
        except treasury.DuplicateSettlement:
            continue
        except treasury.SettlementRejected as error:
            logger.warning("Liquidació %s rebutjada: %s", report.external_id, error.messages)
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


def to_data(report: base.ProviderSettlementReport) -> treasury.SettlementData:
    """La forma de la 04: cada operació és una línia amb la referència del pagament
    (`Payment.provider_reference`, l'identificador de l'ordre)."""
    return treasury.SettlementData(
        external_id=report.external_id,
        settled_on=report.settled_on,
        gross_cents=report.gross_cents,
        fees_cents=report.fees_cents,
        net_cents=report.net_cents,
        lines=tuple(
            treasury.SettlementLine(op.order_id, op.amount_cents, op.fee_cents)
            for op in report.operations
        ),
    )
