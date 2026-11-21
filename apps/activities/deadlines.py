"""Terminis de pagament, ofertes de plaça i caducitat (T-M02-13; P-M02-D passos 1 i 2; RN-M02-08 i
RN-M02-09; CA-M02-09 i CA-M02-27; L-M02-01). Portat de la branca aparcada.

- **Termini de pagament** (RN-M02-08). Una inscripció pendent de pagament que no s'ha pagat quan
  arriba `payment_due_at` (les hores de l'activitat, que copia l'ajust
  `activities.default_payment_window_hours`) passa a `expired`, el seu càrrec s'anul·la amb motiu
  i la plaça s'ofereix. Un pagament en curs al 05b (targeta o Bizum) allarga el termini fins que
  acaba; una transferència anunciada no. Si el càrrec ja és pagat, no caduca: la confirma el
  subscriptor de `charge.paid` (T-M02-10).
- **Oferta de plaça** (RN-M02-09). Quan hi ha una plaça lliure, el primer de la llista passa a
  `offered`, amb un termini per acceptar-la: les hores de l'ajust `activities.offer_accept_hours`
  (VC-22) o la data límit d'inscripció, si arriba abans. Una plaça oferta ocupa plaça. Si
  l'accepta: càrrec i termini de pagament, com una inscripció nova (o confirmada, si és gratuïta).
  Si no l'accepta o se li acaba el termini: `expired`, i es passa al següent.

`run_deadlines` és la tasca de la cua: fa caducar el que toca i ofereix les places lliures, una
transacció per activitat i amb la fila de l'activitat bloquejada. Idempotent.

**Concrecions:** amb les inscripcions tancades no s'ofereix cap plaça (decisió 103): qui espera es
queda a la llista, i si el responsable les reobre les ofertes tornen a sortir. Respon una oferta
la mateixa persona (compte personal) o qui inscriu presencialment (AC5). Les posicions de la
llista són sempre 1, 2, 3…, sense forats.

Un convidat no té compte: l'oferta l'accepta per ell qui té AC5 i, en acceptar-la, rep l'enllaç
de convidat per pagar (P-457).

**Fora d'aquesta peça:** ordenar la llista i oferir una plaça a mà (AC16) i els correus de l'oferta
i del termini (T-M02-21).
"""

import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import Account
from apps.core import audit, business_settings, charges, guest_links
from apps.core.models import Charge
from apps.payments import checkout

from . import enrolment as enrolments
from . import extensions, permissions
from .models import Activity, Enrolment

S = Enrolment.Status
OFFER_HOURS_KEY = "activities.offer_accept_hours"  # VC-22
SYSTEM = audit.system("activities.deadlines")
UNPAID_REASON = "No s'ha pagat dins el termini de la inscripció."


def offer_deadline(activity, now) -> datetime.datetime:
    """Fins quan es pot acceptar una plaça oferta ara (RN-M02-09; CA-M02-27)."""
    hours = business_settings.get(OFFER_HOURS_KEY)
    return min(now + datetime.timedelta(hours=hours), activity.registration_closes_at)


def _renumber(activity) -> None:
    for position, row in enumerate(enrolments.waitlist(activity), start=1):
        if row.waitlist_position != position:
            Enrolment.objects.filter(pk=row.pk).update(waitlist_position=position)


def offer_free_places(activity, *, now) -> list[Enrolment]:
    """Ofereix les places lliures als primers de la llista. `activity` ha d'estar bloquejada
    (`enrolment.lock`). Amb les inscripcions tancades no ofereix res."""
    if not enrolments.is_open(activity, now):
        return []
    free = enrolments.free_places(activity)
    offered = list(enrolments.waitlist(activity).select_for_update(of=("self",))[:free])
    for row in offered:
        enrolments.change_status(
            row, S.OFFERED, actor=SYSTEM, details={"waitlist_position": row.waitlist_position}
        )
        row.waitlist_position = None
        row.offer_expires_at = offer_deadline(activity, now)
        row.save(update_fields=["status", "waitlist_position", "offer_expires_at", "updated_at"])
    if offered:
        _renumber(activity)
    return offered


# --- La persona respon l'oferta ------------------------------------------------------------------


def _locked_offer(enrolment, actor):
    if isinstance(actor, Account) and actor.kind == Account.Kind.PERSONAL:
        if actor.person_id != enrolment.person_id:
            raise Http404
    else:
        permissions.require(actor, permissions.ENROL_IN_PERSON)
    activity = enrolments.lock(enrolment.activity)
    row = Enrolment.objects.select_for_update(of=("self",)).get(pk=enrolment.pk)
    if row.status != S.OFFERED:
        raise ValidationError(_("Aquesta inscripció no té cap plaça oferta."))
    return activity, row


@transaction.atomic
def accept_offer(enrolment, *, actor, now=None, request=None) -> Enrolment:
    """`offered → pending_payment` (o `confirmed`, si és gratuïta)."""
    now = now or timezone.now()
    activity, row = _locked_offer(enrolment, actor)
    if row.offer_expires_at <= now:
        raise ValidationError(_("El termini per acceptar aquesta plaça ja ha passat."))
    if not enrolments.is_open(activity, now):
        raise enrolments.ActivityNotOpen(_("Aquesta activitat no té les inscripcions obertes."))
    row.offer_expires_at = None
    target = enrolments.take_place(row, activity, actor=actor, now=now)
    enrolments.change_status(
        row, target, actor=actor, details={"charge": row.charge_id}, request=request
    )
    row.save()
    if row.channel == Enrolment.Channel.GUEST and row.charge_id:
        # Un convidat no té compte: paga amb l'enllaç de convidat, com en inscriure's (P-457).
        guest_links.create(row.person, row.charge, by=SYSTEM, request=request)
    if row.status == S.CONFIRMED:
        extensions.enrolment_confirmed.send(sender=Enrolment, enrolment=row)
    return row


@transaction.atomic
def decline_offer(enrolment, *, actor, now=None, request=None) -> Enrolment:
    """`offered → expired`: no la vol. La plaça passa al següent de la llista."""
    now = now or timezone.now()
    activity, row = _locked_offer(enrolment, actor)
    enrolments.change_status(
        row, S.EXPIRED, actor=actor, reason=_("No ha acceptat la plaça oferta."), request=request
    )
    row.offer_expires_at = None
    row.save(update_fields=["status", "offer_expires_at", "updated_at"])
    offer_free_places(activity, now=now)
    return row


# --- La cua --------------------------------------------------------------------------------------


def _paying(charge) -> bool:
    """RN-M02-08: un intent del 05b en curs allarga el termini; una transferència anunciada no."""
    status = checkout.payment_status(charge)
    if status.state not in (checkout.IN_PROGRESS, checkout.TIMED_OUT):
        return False
    return status.attempt.method != checkout.TRANSFER


@transaction.atomic
def _run_activity(activity_id, now) -> dict:
    done = {"expired_unpaid": 0, "expired_offers": 0, "offered": 0}
    activity = Activity.objects.select_for_update(of=("self",)).get(pk=activity_id)
    rows = Enrolment.objects.select_for_update(of=("self",)).filter(activity=activity)
    unpaid = rows.filter(status=S.PENDING_PAYMENT, payment_due_at__lte=now)
    for row in unpaid.select_related("charge"):
        if row.charge.status == Charge.Status.PAID or _paying(row.charge):
            continue
        enrolments.change_status(row, S.EXPIRED, actor=SYSTEM, reason=UNPAID_REASON)
        row.payment_due_at = None
        row.save(update_fields=["status", "payment_due_at", "updated_at"])
        if row.charge.status == Charge.Status.PENDING:
            charges.cancel(row.charge, UNPAID_REASON, by=SYSTEM)
        done["expired_unpaid"] += 1
    for row in rows.filter(status=S.OFFERED, offer_expires_at__lte=now):
        enrolments.change_status(
            row, S.EXPIRED, actor=SYSTEM, reason=_("No ha acceptat la plaça oferta a temps.")
        )
        row.offer_expires_at = None
        row.save(update_fields=["status", "offer_expires_at", "updated_at"])
        done["expired_offers"] += 1
    done["offered"] = len(offer_free_places(activity, now=now))
    return done


def run_deadlines(now=None) -> dict:
    """Fa caducar les inscripcions sense pagar i les ofertes sense acceptar, i ofereix les places
    lliures (CA-M02-09). Torna quantes n'ha fet de cada."""
    now = now or timezone.now()
    due = Enrolment.objects.filter(
        status=S.PENDING_PAYMENT, payment_due_at__lte=now
    ) | Enrolment.objects.filter(status=S.OFFERED, offer_expires_at__lte=now)
    waiting = Enrolment.objects.filter(
        status=S.WAITLISTED,
        activity__status=Activity.Status.OPEN,
        activity__registration_closes_at__gt=now,
    )
    ids = set(due.values_list("activity_id", flat=True))
    ids |= set(waiting.values_list("activity_id", flat=True))
    total = {"expired_unpaid": 0, "expired_offers": 0, "offered": 0}
    for activity_id in sorted(ids):
        for key, value in _run_activity(activity_id, now).items():
            total[key] += value
    return total
