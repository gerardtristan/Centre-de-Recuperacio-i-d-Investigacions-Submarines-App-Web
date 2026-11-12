"""Què fa el 02 quan es paga un dels seus càrrecs (T-M02-10; M02-8; CA-M02-07; 049).

`on_charge_paid(event)` és el subscriptor de l'esdeveniment general `charge.paid`. El 05b no crida
mai el 02: emet l'esdeveniment i el 02 s'hi subscriu.

- Només mira els càrrecs amb origen `activities`.
- **Idempotent:** si la inscripció ja és confirmada, no fa res; el mateix esdeveniment lliurat dues
  vegades confirma una sola vegada i envia `enrolment_confirmed` una sola vegada.
- **No es fia de l'esdeveniment:** torna a llegir el càrrec i només confirma si és «pagat».
- Una inscripció que ja no espera el pagament (caducada o cancel·lada, L-M02-01) **no es
  confirma**: en queda una entrada al registre perquè es revisi. La proposta de devolució d'aquest
  cas és de la T-M02-36 (RN-M02-37).

**Estat de la integració.** El mecanisme d'esdeveniments (`apps/core/events.py`, T-M05b-21) encara
no existeix, de manera que **ningú no crida aquesta funció en producció**: la subscripció
(`events.subscribe("charge.paid", on_charge_paid)`) s'afegirà a `apps.py` quan hi sigui. El format
de l'esdeveniment és el de la 049 (identificador del càrrec, tipus, mòdul d'origen, activitat i
import); aquí només se'n llegeixen `charge_id` i `origin`, i s'haurà d'ajustar al format real.
"""

from django.db import transaction

from apps.core import audit
from apps.core.models import Charge

from . import enrolment as enrolments
from . import extensions
from .models import Enrolment

S = Enrolment.Status
ORIGIN = "activities.charge_paid"
PAID_NOT_CONFIRMED = "activities.enrolment.paid_not_confirmed"


def _value(event, name):
    if isinstance(event, dict):
        return event.get(name)
    return getattr(event, name, None)


def on_charge_paid(event) -> Enrolment | None:
    """Subscriptor de `charge.paid`. Torna la inscripció confirmada, o `None` si no hi ha res a
    fer."""
    origin = _value(event, "origin")
    if origin is not None and origin != enrolments.CHARGE_ORIGIN:
        return None
    return confirm_paid(_value(event, "charge_id"))


@transaction.atomic
def confirm_paid(charge_id) -> Enrolment | None:
    """Passa a `confirmed` la inscripció del càrrec, si el càrrec és pagat i la inscripció encara
    l'esperava."""
    enrolment = (
        Enrolment.objects.select_for_update(of=("self",))
        .select_related("charge", "activity")
        .filter(charge_id=charge_id, charge__origin=enrolments.CHARGE_ORIGIN)
        .first()
    )
    if enrolment is None or enrolment.charge.status != Charge.Status.PAID:
        return None
    if enrolment.status == S.CONFIRMED:
        return None
    actor = audit.system(ORIGIN)
    if enrolment.status != S.PENDING_PAYMENT:
        already = audit.AuditEntry.objects.filter(
            action=PAID_NOT_CONFIRMED,
            target_type=enrolment._meta.label_lower,
            target_id=str(enrolment.pk),
        ).exists()
        if not already:
            audit.record(
                PAID_NOT_CONFIRMED,
                actor=actor,
                target=enrolment,
                details={"status": enrolment.status, "charge": enrolment.charge_id},
            )
        return None
    enrolments.change_status(
        enrolment, S.CONFIRMED, actor=actor, details={"charge": enrolment.charge_id}
    )
    enrolment.payment_due_at = None
    enrolment.save(update_fields=["status", "payment_due_at", "updated_at"])
    extensions.enrolment_confirmed.send(sender=Enrolment, enrolment=enrolment)
    return enrolment
