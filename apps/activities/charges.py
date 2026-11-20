"""Què fa el 02 quan es paga un dels seus càrrecs (T-M02-10; M02-8; CA-M02-07; 049).

`on_charge_paid(event)` és el subscriptor de l'esdeveniment `charge.paid` (es registra a
`ActivitiesConfig.ready`). El 05b no crida mai el 02: emet l'esdeveniment i el 02 s'hi subscriu.

- Només mira els càrrecs amb origen `activities`.
- **Idempotent:** la cua no repeteix un lliurament fet (`EventDelivery`) i, si l'esdeveniment
  arriba dues vegades, una inscripció ja confirmada no canvia ni torna a avisar.
- **No es fia de l'esdeveniment:** torna a llegir el càrrec i només confirma si és «pagat».
- Una inscripció que ja no espera el pagament (caducada o cancel·lada, L-M02-01) **no es
  confirma**: en queda una sola entrada al registre perquè es revisi. La proposta de devolució
  d'aquest cas és de la T-M02-36 (RN-M02-37).

**Fora d'aquesta peça:** la confirmació per correu amb el calendari (T-M02-21) i la imputació de
l'ingrés a l'activitat (04).
"""

from django.db import transaction

from apps.core import audit
from apps.core.models import AuditEntry, Charge

from . import extensions
from .models import Enrolment

S = Enrolment.Status
CHARGE_ORIGIN = "activities"
ACTOR = audit.system("activities.charge_paid")
CONFIRMED = "activities.enrolment.confirmed"
PAID_NOT_CONFIRMED = "activities.enrolment.paid_not_confirmed"


@transaction.atomic
def on_charge_paid(event) -> Enrolment | None:
    """Passa a `confirmed` la inscripció del càrrec pagat. Torna la inscripció confirmada, o `None`
    si no hi ha res a fer."""
    payload = event.payload
    if payload.get("origin") != CHARGE_ORIGIN:
        return None
    enrolment = (
        Enrolment.objects.select_for_update(of=("self",))
        .select_related("charge")
        .filter(charge_id=payload.get("charge"), charge__origin=CHARGE_ORIGIN)
        .first()
    )
    if enrolment is None or enrolment.charge.status != Charge.Status.PAID:
        return None
    if enrolment.status == S.CONFIRMED:
        return None
    if enrolment.status != S.PENDING_PAYMENT:
        seen = AuditEntry.objects.filter(
            action=PAID_NOT_CONFIRMED, target_id=str(enrolment.pk)
        ).exists()
        if not seen:
            audit.record(
                PAID_NOT_CONFIRMED,
                actor=ACTOR,
                target=enrolment,
                details={"status": enrolment.status, "charge": enrolment.charge_id},
            )
        return None
    enrolment.status, enrolment.payment_due_at = S.CONFIRMED, None
    enrolment.save(update_fields=["status", "payment_due_at", "updated_at"])
    audit.record(
        CONFIRMED,
        actor=ACTOR,
        target=enrolment,
        field="status",
        old=S.PENDING_PAYMENT,
        new=S.CONFIRMED,
        details={"charge": enrolment.charge_id, "event": event.pk},
    )
    extensions.enrolment_confirmed.send(sender=Enrolment, enrolment=enrolment)
    return enrolment
