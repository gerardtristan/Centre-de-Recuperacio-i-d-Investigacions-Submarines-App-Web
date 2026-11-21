"""Llicència d'un dia (T-M06-19; RN-M06-19 i 20; CA-M06-21 a 23), darrere de l'opció
`licences.day_enabled`, desactivada fins a la T-M06-21.

- La unicitat per data és una restricció del model (`licences_licence_one_day_in_progress`).
- Un tipus d'un dia no es pot crear ni activar amb l'opció desactivada (`LicenceType.clean`).
- `lapse_overdue(today)`: la tasca diària. Una d'un dia pagada o tramitada que no és vigent en
  acabar el seu dia passa a «no tramitada a temps» (`lapsed`) una sola vegada, i si es va pagar
  queda una proposta de devolució per al tresorer, sense cap devolució automàtica. Avisos: a qui
  tramita (LC5) i, si hi ha proposta, a qui fa devolucions (LC7).
"""

import datetime

from django.db import transaction
from django.utils import timezone

from apps.core import audit
from apps.core.models import Charge

from . import events as licence_events
from .models import Licence, LicenceRefundProposal, ValidityRule
from .services import notify_refund

ACTION_LAPSED = "licences.lapsed"
SYSTEM = audit.system("licences.lapse_overdue")
REASON = "No tramitada a temps (RN-M06-20)"


def lapse_overdue(today: datetime.date | None = None) -> int:
    today = today or timezone.localdate()
    overdue = Licence.objects.filter(
        validity_rule=ValidityRule.SINGLE_DAY,
        status__in=[Licence.Status.PAID, Licence.Status.FILED],
        expires_on__lt=today,
    ).values_list("pk", flat=True)
    done = 0
    for pk in list(overdue):
        with transaction.atomic():
            licence = Licence.objects.select_for_update().get(pk=pk)
            if licence.status not in (Licence.Status.PAID, Licence.Status.FILED):
                continue  # una altra execució ja l'ha passada
            previous = licence.status
            licence.status = Licence.Status.LAPSED
            licence.save(update_fields=["status", "updated_at"])
            charge = licence.charge
            if charge is not None and charge.status == Charge.Status.PAID:
                LicenceRefundProposal.objects.create(
                    licence=licence, amount_cents=charge.amount_cents, reason=REASON
                )
                notify_refund(licence, charge.amount_cents)
            # CA-M06-23: també a qui tramita (LC5).
            licence_events.notify(
                "licences.file", "avis-llicencia-no-tramitada",
                {"licence_id": licence.pk, "day": licence.starts_on},
            )  # fmt: skip
            audit.record(
                ACTION_LAPSED, actor=SYSTEM, target=licence, field="status", old=previous,
                new=Licence.Status.LAPSED,
            )  # fmt: skip
            done += 1
    return done
