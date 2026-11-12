"""Terminis de pagament, ofertes de plaça i llista d'espera (T-M02-13; P-M02-D passos 1 i 2;
RN-M02-08 i RN-M02-09; CA-M02-09 i CA-M02-27; AC16).

- **Termini de pagament** (RN-M02-08). Una inscripció pendent de pagament que no s'ha pagat quan
  arriba `payment_due_at` passa a `expired`, el seu càrrec s'anul·la amb motiu i la plaça
  s'ofereix. Si el càrrec ja és pagat i el 02 encara no ho sabia, es confirma en lloc de caducar.
- **Oferta de plaça** (RN-M02-09). Quan hi ha una plaça lliure, el primer de la llista passa a
  `offered`, amb un termini per acceptar-la: les hores de l'ajust `activities.offer_accept_hours`
  (VC-22; 48 d'entrada) o la data límit d'inscripció, si arriba abans. Una plaça oferta ocupa
  plaça. Si l'accepta: càrrec i termini de pagament, com en una inscripció nova (o confirmada, si
  és gratuïta). Si no l'accepta o se li acaba el termini: `expired`, i es passa al següent.
- **A mà** (AC16): el responsable pot canviar l'ordre de la llista, amb motiu, i oferir una plaça
  lliure a algú de la llista (amb motiu si se salta l'ordre).

`run_deadlines` és la tasca de la cua: fa caducar el que toca i ofereix les places lliures.
Idempotent: una segona passada no troba res a fer.

**Concrecions d'implementació** (dins de les regles; al diari de la T-M02-13)

- Amb les inscripcions tancades (data límit o a mà) **no s'ofereix cap plaça**: el termini d'una
  oferta acaba, com a molt, a la data límit (RN-M02-09), i la decisió 088 no admet excepcions
  després del tancament. Qui espera es queda a la llista; si el responsable reobre les
  inscripcions (RN-M02-02), les ofertes tornen a sortir.
- Pot acceptar o rebutjar una oferta la mateixa persona (compte personal o enllaç de convidat) o
  qui té el permís d'inscriure presencialment (AC5).
- Les posicions de la llista són sempre 1, 2, 3… sense forats.

**Fora d'aquesta peça:** un pagament «en curs» allarga el termini (RN-M02-08): els intents de
pagament són del 05b, que encara no existeix, i ara cap inscripció no en pot tenir. Els correus
de l'oferta i del termini són de la T-M02-21.
"""

import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import Account
from apps.core import audit, charges
from apps.core.models import Charge

from . import charges as activity_charges
from . import enrolment as enrolments
from . import permissions, services
from .models import Activity, Enrolment

S = Enrolment.Status
ORIGIN = "activities.deadlines"
MOVED = "activities.waitlist.moved"
UNPAID_REASON = "No s'ha pagat dins el termini de la inscripció."


def offer_hours() -> int:
    return int(services.setting(services.OFFER_HOURS_KEY))


def offer_deadline(activity, now) -> datetime.datetime:
    """Fins quan es pot acceptar una plaça oferta ara: les hores de l'ajust o la data límit
    d'inscripció, el que arribi abans (RN-M02-09; CA-M02-27)."""
    return min(now + datetime.timedelta(hours=offer_hours()), activity.registration_closes_at)


def _renumber(activity) -> None:
    for position, row in enumerate(enrolments.waitlist(activity), start=1):
        if row.waitlist_position != position:
            Enrolment.objects.filter(pk=row.pk).update(waitlist_position=position)


def _offer(row, activity, *, actor, now, reason="", request=None) -> None:
    enrolments.change_status(
        row,
        S.OFFERED,
        actor=actor,
        reason=reason,
        details={"waitlist_position": row.waitlist_position},
        request=request,
    )
    row.waitlist_position = None
    row.offer_expires_at = offer_deadline(activity, now)
    row.save(update_fields=["status", "waitlist_position", "offer_expires_at", "updated_at"])


def offer_free_places(activity, *, actor, now) -> list[Enrolment]:
    """Ofereix les places lliures als primers de la llista. `activity` ha d'estar bloquejada
    (`enrolment.lock`). Amb les inscripcions tancades no ofereix res."""
    offered = []
    if not enrolments.is_open(activity, now):
        return offered
    free = activity.max_places - enrolments.occupied(activity)
    for row in list(enrolments.waitlist(activity).select_for_update(of=("self",))[: max(free, 0)]):
        _offer(row, activity, actor=actor, now=now)
        offered.append(row)
    if offered:
        _renumber(activity)
    return offered


# --- El participant respon a l'oferta ------------------------------------------------------------


def _check_responder(actor, person) -> None:
    """Qui pot respondre una oferta: la mateixa persona o qui inscriu presencialment (AC5)."""
    if isinstance(actor, Account):
        if actor.kind == Account.Kind.PERSONAL:
            if actor.person_id != person.pk:
                raise Http404
            return
        permissions.require(actor, permissions.ENROL_IN_PERSON)
        return
    guest = (
        isinstance(actor, audit.Actor)
        and actor.kind == audit.AuditEntry.ActorKind.GUEST
        and actor.person is not None
        and actor.person.pk == person.pk
    )
    if not guest:
        raise Http404


def _locked_offer(enrolment, actor, now):
    _check_responder(actor, enrolment.person)
    activity = enrolments.lock(enrolment.activity)
    row = Enrolment.objects.select_for_update(of=("self",)).get(pk=enrolment.pk)
    if row.status != S.OFFERED:
        raise ValidationError(_("Aquesta inscripció no té cap plaça oferta."))
    return activity, row


@transaction.atomic
def accept_offer(enrolment, *, actor, now=None, request=None) -> Enrolment:
    """`offered → pending_payment` (o `confirmed`, si és gratuïta)."""
    now = now or timezone.now()
    activity, row = _locked_offer(enrolment, actor, now)
    if row.offer_expires_at is None or row.offer_expires_at <= now:
        raise ValidationError(_("El termini per acceptar aquesta plaça ja ha passat."))
    if not enrolments.is_open(activity, now):
        raise enrolments.ActivityNotOpen(_("Aquesta activitat no té les inscripcions obertes."))
    target = enrolments.take_place(row, activity, actor=actor, now=now)
    enrolments.change_status(
        row, target, actor=actor, details={"charge": row.charge_id}, request=request
    )
    row.save()
    if row.status == S.CONFIRMED:
        from . import extensions

        extensions.enrolment_confirmed.send(sender=Enrolment, enrolment=row)
    return row


@transaction.atomic
def decline_offer(enrolment, *, actor, now=None, request=None) -> Enrolment:
    """`offered → expired`: no la vol. La plaça passa al següent de la llista."""
    now = now or timezone.now()
    activity, row = _locked_offer(enrolment, actor, now)
    enrolments.change_status(
        row, S.EXPIRED, actor=actor, reason=_("No ha acceptat la plaça oferta."), request=request
    )
    row.offer_expires_at = None
    row.save(update_fields=["status", "offer_expires_at", "updated_at"])
    offer_free_places(activity, actor=audit.system(ORIGIN), now=now)
    return row


# --- La cua: terminis ----------------------------------------------------------------------------


@transaction.atomic
def _run_activity(activity_id, now) -> dict:
    done = {"expired_unpaid": 0, "confirmed": 0, "expired_offers": 0, "offered": 0}
    system = audit.system(ORIGIN)
    activity = Activity.objects.select_for_update(of=("self",)).get(pk=activity_id)
    rows = Enrolment.objects.select_for_update(of=("self",)).filter(activity=activity)
    for row in rows.filter(status=S.PENDING_PAYMENT, payment_due_at__lte=now).select_related(
        "charge"
    ):
        if row.charge_id and row.charge.status == Charge.Status.PAID:
            # Pagat, però el 02 encara no ho sabia: es confirma, no caduca.
            if activity_charges.confirm_paid(row.charge_id) is not None:
                done["confirmed"] += 1
            continue
        enrolments.change_status(row, S.EXPIRED, actor=system, reason=UNPAID_REASON)
        row.payment_due_at = None
        row.save(update_fields=["status", "payment_due_at", "updated_at"])
        if row.charge_id and row.charge.status == Charge.Status.PENDING:
            charges.cancel(row.charge, UNPAID_REASON, by=system)
        done["expired_unpaid"] += 1
    for row in rows.filter(status=S.OFFERED, offer_expires_at__lte=now):
        enrolments.change_status(
            row, S.EXPIRED, actor=system, reason=_("No ha acceptat la plaça oferta a temps.")
        )
        row.offer_expires_at = None
        row.save(update_fields=["status", "offer_expires_at", "updated_at"])
        done["expired_offers"] += 1
    done["offered"] = len(offer_free_places(activity, actor=system, now=now))
    return done


def run_deadlines(now=None) -> dict:
    """Fa caducar les inscripcions sense pagar i les ofertes sense acceptar, i ofereix les places
    lliures (CA-M02-09). Una transacció per activitat. Torna quantes n'ha fet de cada."""
    now = now or timezone.now()
    due = Enrolment.objects.filter(
        status=S.PENDING_PAYMENT, payment_due_at__lte=now
    ) | Enrolment.objects.filter(status=S.OFFERED, offer_expires_at__lte=now)
    waiting = Enrolment.objects.filter(
        status=S.WAITLISTED,
        activity__status=Activity.Status.OPEN,
        activity__registration_closes_at__gt=now,
    )
    ids = set(due.values_list("activity_id", flat=True)) | set(
        waiting.values_list("activity_id", flat=True)
    )
    total = {"expired_unpaid": 0, "confirmed": 0, "expired_offers": 0, "offered": 0}
    for activity_id in sorted(ids):
        for key, value in _run_activity(activity_id, now).items():
            total[key] += value
    return total


# --- A mà (AC16) ---------------------------------------------------------------------------------


@transaction.atomic
def move(enrolment, position, *, by, reason, request=None) -> Enrolment:
    """Canvia la posició d'algú a la llista d'espera, amb motiu (RN-M02-09)."""
    permissions.require(by, permissions.WAITLIST)
    if not (reason or "").strip():
        raise ValidationError(_("Per canviar l'ordre de la llista d'espera cal un motiu."))
    activity = enrolments.lock(enrolment.activity)
    rows = list(enrolments.waitlist(activity).select_for_update(of=("self",)))
    row = next((r for r in rows if r.pk == enrolment.pk), None)
    if row is None:
        raise ValidationError(_("Aquesta inscripció no és a la llista d'espera."))
    if isinstance(position, bool) or not isinstance(position, int):
        raise ValidationError(_("La posició ha de ser un número."))
    if not 1 <= position <= len(rows):
        raise ValidationError(_("La posició ha de ser entre 1 i %(last)s.") % {"last": len(rows)})
    old = row.waitlist_position
    if old == position:
        return row
    rows.remove(row)
    rows.insert(position - 1, row)
    for index, other in enumerate(rows, start=1):
        if other.waitlist_position != index:
            Enrolment.objects.filter(pk=other.pk).update(waitlist_position=index)
    audit.record(
        MOVED,
        actor=by,
        target=row,
        field="waitlist_position",
        old=old,
        new=position,
        reason=reason.strip(),
        request=request,
    )
    row.refresh_from_db()
    return row


@transaction.atomic
def offer_to(enrolment, *, by, reason="", now=None, request=None) -> Enrolment:
    """Ofereix una plaça lliure a algú de la llista d'espera. Si no és el primer, cal un motiu."""
    permissions.require(by, permissions.WAITLIST)
    now = now or timezone.now()
    activity = enrolments.lock(enrolment.activity)
    row = Enrolment.objects.select_for_update(of=("self",)).get(pk=enrolment.pk)
    if row.status != S.WAITLISTED:
        raise ValidationError(_("Aquesta inscripció no és a la llista d'espera."))
    if not enrolments.is_open(activity, now):
        raise enrolments.ActivityNotOpen(
            _("Amb les inscripcions tancades no es pot oferir cap plaça. Reobre-les abans.")
        )
    if enrolments.occupied(activity) >= activity.max_places:
        raise ValidationError(_("No hi ha cap plaça lliure per oferir."))
    if row.waitlist_position != 1 and not (reason or "").strip():
        raise ValidationError(_("Per oferir una plaça saltant l'ordre de la llista cal un motiu."))
    _offer(row, activity, actor=by, now=now, reason=(reason or "").strip(), request=request)
    _renumber(activity)
    return row
