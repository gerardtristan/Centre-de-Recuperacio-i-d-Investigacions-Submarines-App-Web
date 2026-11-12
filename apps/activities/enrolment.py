"""Inscripcions, places i llista d'espera (T-M02-11 i T-M02-12; P-M02-C passos 4 a 6; RN-M02-03,
RN-M02-04, RN-M02-07, RN-M02-10 i RN-M02-11; CA-M02-06, 08, 10, 12, 13 i 40; L-M02-06).

`enrol(activitat, persona, channel=…, actor=…)` és l'única manera de crear una inscripció:

1. **Oberta** (decisió 088). Només s'hi pot inscriure gent mentre l'activitat és `open` i la data
   límit no ha passat (es mira l'hora, no si la cua ja l'ha tancada). Omplir les places **no** la
   tanca: qui arriba després va a la llista d'espera. Després del tancament no hi entra ningú, ni a
   la llista d'espera.
2. **Una de viva per persona** (CA-M02-13).
3. **Preu** (RN-M02-04): de soci si `members.is_member` el dia de la inscripció; si no, de no soci,
   i només si l'activitat és oberta a no socis (RN-M02-11, CA-M02-10). Es copia a la inscripció.
4. **Requisits** (RN-M02-10; `requirements.check`): en mode `block` es rebutja; en mode `warn`
   s'inscriu i el que no complia queda a `requirements_warning` perquè el responsable ho vegi.
5. **Places** (RN-M02-07): amb la fila de l'activitat bloqueda (`SELECT … FOR UPDATE`) es compten
   les inscripcions que ocupen plaça. Si n'hi ha de lliures i ningú no espera: `pending_payment`
   amb el càrrec «inscripció» (import, activitat i departament de l'activitat) i el termini de
   pagament; si és gratuïta, `confirmed` sense càrrec (L-M02-06). Si no: `waitlisted`, a la cua.

**Concrecions d'implementació** (dins de les regles; al diari de la T-M02-11)

- Si hi ha gent esperant, qui arriba es posa a la cua encara que en aquell moment hi hagi una
  plaça lliure: la plaça és per al primer de la llista (RN-M02-09), no per a qui arriba després.
- Una persona anonimitzada no es pot inscriure.
- El canal `account` exigeix que el compte sigui el personal de la mateixa persona; el canal
  `desk`, el permís AC5 amb edició.

**Fora d'aquesta peça:** la pantalla de pagament i la confirmació quan arriba el pagament (05b;
`apps.activities.charges.on_charge_paid` ja sap què fer quan el càrrec és pagat), terminis,
ofertes i caducitat (T-M02-13), convidats i inscripció presencial des d'una pantalla (T-M02-14),
cancel·lacions (T-M02-15) i avisos (T-M02-21).
"""

import datetime
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import Account
from apps.core import audit, charges
from apps.core.models import Charge, Person
from apps.members import services as members

from . import extensions, permissions, requirements
from .models import Activity, Enrolment

S = Enrolment.Status
CHARGE_ORIGIN = "activities"
ORIGIN = "activities.enrolment"

CREATED = "activities.enrolment.created"
STATUS_CHANGED = "activities.enrolment.status_changed"


class EnrolmentError(ValidationError):
    """Error de domini d'una inscripció, amb el missatge per a la persona."""


class ActivityNotOpen(EnrolmentError):
    pass


class AlreadyEnrolled(EnrolmentError):
    pass


class NonMembersNotAllowed(EnrolmentError):
    pass


class RequirementsNotMet(EnrolmentError):
    def __init__(self, message, checks=()):
        super().__init__(message)
        self.checks = tuple(checks)


@dataclass(frozen=True)
class Quote:
    """El que li correspon a una persona si s'inscriu ara: preu i requisits. No reserva res."""

    price_kind: str
    price_cents: int
    requirements: requirements.Result

    @property
    def price(self) -> str:
        return charges.euros(self.price_cents)

    @property
    def free(self) -> bool:
        return self.price_cents == 0


# --- Lectures ------------------------------------------------------------------------------------


def occupied(activity) -> int:
    """Places ocupades (RN-M02-07): pendents de pagament, confirmades i ofertes."""
    return Enrolment.objects.filter(activity=activity, status__in=Enrolment.OCCUPYING).count()


def free_places(activity) -> int:
    return max(0, activity.max_places - occupied(activity))


def waitlist(activity):
    """La llista d'espera, per ordre."""
    return Enrolment.objects.filter(activity=activity, status=S.WAITLISTED).order_by(
        "waitlist_position", "id"
    )


def is_open(activity, now=None) -> bool:
    """S'hi pot inscriure gent ara mateix: oberta i amb la data límit per venir (088)."""
    now = now or timezone.now()
    return activity.status == Activity.Status.OPEN and activity.registration_closes_at > now


def live_enrolment(activity, person) -> Enrolment | None:
    return Enrolment.objects.filter(
        activity=activity, person=person, status__in=Enrolment.LIVE
    ).first()


def enrolments(activity, statuses=None):
    """Inscripcions d'una activitat amb la persona (M02-8). Qui les mostri ha de comprovar abans
    el seu permís (AC8 i C3)."""
    rows = Enrolment.objects.filter(activity=activity).select_related("person", "charge")
    if statuses is not None:
        rows = rows.filter(status__in=statuses)
    return rows


def _price(activity, person, today) -> tuple[str, int]:
    if members.is_member(person, on=today):
        return Enrolment.PriceKind.MEMBER, activity.price_member_cents
    if not activity.open_to_non_members:
        raise NonMembersNotAllowed(
            _(
                "Aquesta activitat és només per a socis. Si vols participar-hi, primer t'has de "
                "fer soci del club."
            )
        )
    return Enrolment.PriceKind.NON_MEMBER, activity.price_non_member_cents


def quote(activity, person, *, today: datetime.date | None = None) -> Quote:
    """Preu i requisits per a aquesta persona. `NonMembersNotAllowed` si no s'hi pot inscriure
    perquè no és sòcia."""
    today = today or timezone.localdate()
    price_kind, price_cents = _price(activity, person, today)
    return Quote(price_kind, price_cents, requirements.check(activity, person))


# --- Inscriure's ---------------------------------------------------------------------------------


def _check_actor(channel, actor, person) -> None:
    if channel == Enrolment.Channel.ACCOUNT:
        own = (
            isinstance(actor, Account)
            and actor.kind == Account.Kind.PERSONAL
            and actor.person_id == person.pk
        )
        if not own:
            raise Http404
    elif channel == Enrolment.Channel.DESK:
        permissions.require(actor, permissions.ENROL_IN_PERSON)
    elif channel == Enrolment.Channel.GUEST:
        guest = (
            isinstance(actor, audit.Actor)
            and actor.kind == audit.AuditEntry.ActorKind.GUEST
            and actor.person is not None
            and actor.person.pk == person.pk
        )
        if not guest:
            raise Http404
    else:
        raise ValidationError(_("Canal d'inscripció desconegut."))


def _warning_text(result) -> str:
    lines = []
    for check in result.warnings:
        lines.append(f"{check.label}. {check.detail}".strip() if check.detail else check.label)
    return "\n".join(lines)


def _next_position(activity) -> int:
    last = Enrolment.objects.filter(activity=activity, status=S.WAITLISTED).aggregate(
        n=Max("waitlist_position")
    )["n"]
    return (last or 0) + 1


def concept(activity) -> str:
    text = _("Inscripció: %(title)s") % {"title": activity.title}
    return text[: Charge._meta.get_field("concept").max_length]


def take_place(enrolment, activity, *, actor, now) -> str:
    """Dona una plaça a una inscripció (nova, o que accepta una oferta) i torna l'estat que li
    toca: `pending_payment`, amb el càrrec i el termini de pagament, o `confirmed` si és
    gratuïta. No canvia l'estat, no desa ni comprova les places: ho fa qui la crida, amb la fila
    de l'activitat bloquejada."""
    enrolment.waitlist_position = None
    enrolment.offer_expires_at = None
    if enrolment.price_cents == 0:
        enrolment.payment_due_at = None
        return S.CONFIRMED
    enrolment.charge = charges.create_charge(
        enrolment.person,
        kind=Charge.Kind.ENROLMENT,
        amount_cents=enrolment.price_cents,
        concept=concept(activity),
        origin=CHARGE_ORIGIN,
        by=actor,
        department=activity.department,
        activity=activity,
    )
    enrolment.payment_due_at = now + datetime.timedelta(hours=activity.payment_window_hours)
    return S.PENDING_PAYMENT


def lock(activity) -> Activity:
    """La fila de l'activitat, bloquejada fins al final de la transacció (RN-M02-07)."""
    return Activity.objects.select_for_update(of=("self",)).get(pk=activity.pk)


@transaction.atomic
def enrol(activity, person, *, channel, actor, answers=None, now=None, request=None) -> Enrolment:
    """Inscriu `person` a `activity` (M02-8). Torna la inscripció: amb càrrec, confirmada (si és
    gratuïta) o a la llista d'espera. `answers`: respostes ja validades de les preguntes d'altres
    mòduls, per clau de secció."""
    _check_actor(channel, actor, person)
    now = now or timezone.now()
    today = timezone.localdate(now)
    locked = lock(activity)
    if not is_open(locked, now):
        raise ActivityNotOpen(_("Aquesta activitat no té les inscripcions obertes."))
    if person.status == Person.Status.ANONYMISED:
        raise EnrolmentError(_("Aquesta persona no es pot inscriure."))
    if live_enrolment(locked, person) is not None:
        raise AlreadyEnrolled(_("Ja hi ha una inscripció d'aquesta persona a l'activitat."))
    price_kind, price_cents = _price(locked, person, today)
    result = requirements.check(locked, person)
    if not result.allowed:
        raise RequirementsNotMet(
            _("No es compleixen els requisits d'aquesta activitat: %(what)s")
            % {"what": "; ".join(check.label for check in result.blocking)},
            result.blocking,
        )
    enrolment = Enrolment(
        activity=locked,
        person=person,
        channel=channel,
        price_kind=price_kind,
        price_cents=price_cents,
        requirements_warning=_warning_text(result),
        created_by=actor if channel == Enrolment.Channel.DESK else None,
        created_at=now,
    )
    has_place = occupied(locked) < locked.max_places and not waitlist(locked).exists()
    if has_place:
        enrolment.status = take_place(enrolment, locked, actor=actor, now=now)
    else:
        enrolment.status = S.WAITLISTED
        enrolment.waitlist_position = _next_position(locked)
    enrolment.full_clean(exclude=["created_by", "charge"])
    enrolment.save()
    for section in extensions.enrolment_sections():
        data = (answers or {}).get(section.key)
        if data:
            section.save(enrolment, data)
    audit.record(
        CREATED,
        actor=actor,
        target=enrolment,
        details={
            "activity": locked.pk,
            "status": enrolment.status,
            "channel": channel,
            "price_kind": price_kind,
            "price_cents": price_cents,
            "charge": enrolment.charge_id,
            "waitlist_position": enrolment.waitlist_position,
            "requirements_warning": bool(enrolment.requirements_warning),
        },
        request=request,
    )
    if enrolment.status == S.CONFIRMED:
        extensions.enrolment_confirmed.send(sender=Enrolment, enrolment=enrolment)
    return enrolment


def change_status(enrolment, new_status, *, actor, reason="", details=None, request=None) -> None:
    """Canvia l'estat d'una inscripció ja bloquejada i en deixa el valor anterior al registre.
    Només per als serveis del 02: les transicions vàlides són les de RN-M02-03."""
    if (enrolment.status, new_status) not in TRANSITIONS:
        raise ValidationError(
            _("Una inscripció «%(current)s» no pot passar a «%(new)s».")
            % {"current": enrolment.get_status_display(), "new": S(new_status).label}
        )
    audit.record(
        STATUS_CHANGED,
        actor=actor,
        target=enrolment,
        field="status",
        old=enrolment.status,
        new=new_status,
        reason=reason,
        details=details,
        request=request,
    )
    enrolment.status = new_status


# RN-M02-03. Una inscripció confirmada no torna a pendent de pagament.
# Concreció: acceptar una oferta d'una activitat gratuïta confirma directament, sense càrrec
# (L-M02-06: «la llista d'espera funciona igual»).
TRANSITIONS = {
    (S.PENDING_PAYMENT, S.CONFIRMED),
    (S.PENDING_PAYMENT, S.EXPIRED),
    (S.PENDING_PAYMENT, S.CANCELLED),
    (S.WAITLISTED, S.OFFERED),
    (S.WAITLISTED, S.CANCELLED),
    (S.WAITLISTED, S.EXPIRED),
    (S.OFFERED, S.PENDING_PAYMENT),
    (S.OFFERED, S.CONFIRMED),  # només una activitat gratuïta (L-M02-06)
    (S.OFFERED, S.EXPIRED),
    (S.CONFIRMED, S.CANCELLED),
}
