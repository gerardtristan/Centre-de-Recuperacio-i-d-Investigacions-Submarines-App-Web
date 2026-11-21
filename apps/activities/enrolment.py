"""Inscriure's a una activitat, places i llista d'espera (T-M02-11 i T-M02-12; P-M02-C passos 3 a
5; RN-M02-04, RN-M02-07, RN-M02-10 i RN-M02-11; CA-M02-06, 08, 12, 13, 28, 29 i 40). Portat de la
branca aparcada.

`enrol(activitat, persona, channel=…, actor=…)` és l'única manera de crear una inscripció:

1. **Oberta** (decisió 103): l'activitat és `open` i la data límit no ha passat (es mira l'hora,
   no si la cua ja l'ha tancada). Omplir les places **no** la tanca: qui arriba després va a la
   llista d'espera. Després del tancament no hi entra ningú, ni a la llista d'espera.
2. **Una de viva per persona** (CA-M02-13).
3. **Preu** (RN-M02-04): el de soci de l'activitat si `members.is_member` el dia d'inscriure's; si
   no, el de no soci, i només si l'activitat és oberta a no socis (RN-M02-11, CA-M02-10). Es copia
   a la inscripció i no canvia.
4. **Requisits** (`requirements.check`): en mode `block`, el que no es compleix ho impedeix; en
   mode `warn`, s'inscriu i el que el responsable ha de veure queda a `requirements_warning`
   (llicència en tràmit, titulació del club sense verificar, edat desconeguda…).
5. **Places** (RN-M02-07): amb la fila de l'activitat bloquejada (`SELECT … FOR UPDATE`) es compten
   les inscripcions que ocupen plaça. Si n'hi ha: `pending_payment` amb el càrrec «inscripció» de
   la 00 (import, departament i centre de cost de l'activitat) i el termini de pagament de
   l'activitat; si és gratuïta, `confirmed` sense càrrec (L-M02-06). Si no n'hi ha, o si ja hi ha
   gent esperant: `waitlisted`, al final de la llista (la plaça que s'allibera és per al primer de
   la llista, RN-M02-09, no per a qui arriba després).

El pagament és el camí del 05b sobre el càrrec (`payments:charge`); quan el càrrec és pagat, la
confirma `charges.on_charge_paid` (T-M02-10).

**Concrecions:** una persona anonimitzada no es pot inscriure; el canal `account` exigeix el
compte personal de la mateixa persona; el canal `desk`, el permís AC5 amb edició.

**Fora d'aquesta peça:** caducitat i ofertes de plaça (T-M02-13), ordenar la llista a mà (AC16),
convidats i la pantalla presencial (T-M02-14), cancel·lacions (T-M02-15) i avisos (T-M02-21).
"""

import datetime

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
from .charges import CHARGE_ORIGIN
from .models import Activity, Enrolment

S = Enrolment.Status
CREATED = "activities.enrolment.created"


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
    """S'hi pot inscriure gent ara mateix: oberta i amb la data límit per venir (103)."""
    now = now or timezone.now()
    return activity.status == Activity.Status.OPEN and activity.registration_closes_at > now


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
    else:  # el convidat arriba amb la T-M02-14
        raise ValidationError(_("Canal d'inscripció desconegut."))


def _warning_text(result) -> str:
    return "\n".join(
        f"{check.label}. {check.detail}" if check.detail else check.label
        for check in result.warnings
    )


def concept(activity) -> str:
    text = _("Inscripció: %(title)s") % {"title": activity.title}
    return text[: Charge._meta.get_field("concept").max_length]


def take_place(enrolment, activity, *, actor, now) -> str:
    """Dona una plaça a la inscripció i torna l'estat que li toca: `pending_payment`, amb el
    càrrec i el termini de pagament, o `confirmed` si és gratuïta. No desa ni comprova les
    places: ho fa qui la crida, amb la fila de l'activitat bloquejada."""
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
        cost_centre=activity.cost_centre,
    )
    enrolment.payment_due_at = now + datetime.timedelta(hours=activity.payment_window_hours)
    return S.PENDING_PAYMENT


def lock(activity) -> Activity:
    """La fila de l'activitat, bloquejada fins al final de la transacció (RN-M02-07)."""
    return Activity.objects.select_for_update(of=("self",)).get(pk=activity.pk)


@transaction.atomic
def enrol(activity, person, *, channel, actor, answers=None, now=None, request=None) -> Enrolment:
    """Inscriu `person` a `activity` (M02-8). Torna la inscripció: amb el càrrec pendent,
    confirmada si és gratuïta o a la llista d'espera. `answers`: respostes ja validades de les
    preguntes d'altres mòduls, per clau de secció (`extensions.register_enrolment_section`)."""
    _check_actor(channel, actor, person)
    now = now or timezone.now()
    locked = lock(activity)
    if not is_open(locked, now):
        raise ActivityNotOpen(_("Aquesta activitat no té les inscripcions obertes."))
    if person.status == Person.Status.ANONYMISED:
        raise EnrolmentError(_("Aquesta persona no es pot inscriure."))
    live = Enrolment.objects.filter(activity=locked, person=person, status__in=Enrolment.LIVE)
    if live.exists():
        raise AlreadyEnrolled(_("Ja hi ha una inscripció d'aquesta persona a l'activitat."))
    price_kind, price_cents = _price(locked, person, timezone.localdate(now))
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
    waiting = waitlist(locked)
    if occupied(locked) < locked.max_places and not waiting.exists():
        enrolment.status = take_place(enrolment, locked, actor=actor, now=now)
    else:
        enrolment.status = S.WAITLISTED
        enrolment.waitlist_position = (waiting.aggregate(n=Max("waitlist_position"))["n"] or 0) + 1
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
