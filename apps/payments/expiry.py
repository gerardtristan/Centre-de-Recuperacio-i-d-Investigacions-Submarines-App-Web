"""Caducitat dels mandats sense cobraments (T-M05a-15; RN-M05a-08).

Un mandat actiu caduca quan fa 36 mesos de l'últim cobrament (`last_collection_on`) o, si no se
n'ha cobrat mai cap, de la signatura ([P-194](docs/decisions/pendents.md)). No s'esborra res:
l'estat passa a «caducat» i el registre d'activitat en guarda el motiu. La preferència de pagament
del soci no es toca ([P-195](docs/decisions/pendents.md)). El soci rep un correu per signar-ne un
de nou (`mandat-caducat`, T-M05a-09), a la mateixa transacció, per la cua.
"""

import calendar
from datetime import date

from django.db import transaction
from django.utils import timezone

from apps.core import audit

from . import mandates
from .models import SepaMandate

# VC-13: es queda al codi (regla SEPA, no és un valor de negoci editable) [A verificar: banc].
EXPIRY_MONTHS = 36
REASON = "36 mesos sense cap cobrament (RN-M05a-08)"
ACTOR = audit.system("payments.expire_mandates")


def months_after(day: date, months: int) -> date:
    """De data a data; si el mes d'arribada no té aquell dia, l'últim del mes (com a la 070)."""
    year, month = divmod(day.month - 1 + months, 12)
    year, month = day.year + year, month + 1
    return day.replace(
        year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1])
    )


def expires_on(mandate: SepaMandate) -> date:
    since = mandate.last_collection_on or timezone.localdate(mandate.signed_at)
    return months_after(since, EXPIRY_MONTHS)


@transaction.atomic
def expire_mandates(today: date | None = None) -> int:
    """Passa a «caducat» els mandats actius que han arribat a la data de caducitat. Idempotent:
    un mandat caducat ja no és actiu. Torna quants n'ha caducat."""
    today = today or timezone.localdate()
    # Bloquejades: un cobrament desat alhora (05b) es veu abans de decidir.
    active = SepaMandate.objects.select_for_update().filter(status=SepaMandate.Status.ACTIVE)
    # shortcut: es recorren tots els actius en Python (uns centenars); amb milers, filtrar a SQL.
    expired = [mandate for mandate in active if expires_on(mandate) <= today]
    for mandate in expired:
        mandate.status = SepaMandate.Status.EXPIRED
        mandate.save(update_fields=["status"])
        audit.record(
            "payments.mandate.expired",
            actor=ACTOR,
            target=mandate,
            field="status",
            old=SepaMandate.Status.ACTIVE,
            new=SepaMandate.Status.EXPIRED,
            reason=REASON,
            details={"reference": mandate.reference, "expires_on": str(expires_on(mandate))},
        )
        mandates.mail_member(mandates.EXPIRED_TEMPLATE, mandate, months=EXPIRY_MONTHS)
    return len(expired)
