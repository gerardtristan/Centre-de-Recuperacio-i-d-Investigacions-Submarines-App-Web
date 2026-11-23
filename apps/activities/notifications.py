"""Avisos per correu a l'alumne (T-M02-21, primera part; RN-M02-19; P-M02-F passos 4 a 6).

- **Recordatori** (`send_reminders`, tasca diària): als inscrits confirmats, els dies de l'ajust
  `activities.reminder_days_before` (VC-23) abans de cada sessió d'un curs o de cada sortida. Una
  sessió de reforç només a l'alumne del reforç.
- **Resultat** (`notify_outcome`): apte o no apte, sense el motiu (en parla l'instructor).
- **Certificat** (`notify_certificate`): el número; el certificat es descarrega a la plataforma.
- **Reforç** (`notify_reinforcement`): les dates, les hores, el lloc i el preu de les classes.

L'adreça és la de `members.recipients.email_for` (el representant, si és menor); sense adreça, no
s'envia res. Cap dada d'altres persones; mai dades de salut ni adjunts. La safata de l'app
(RN-M02-19) espera un lloc d'avisos a l'àrea personal.
"""

import datetime

from django.utils import timezone

from apps.core import business_settings, charges, mail
from apps.members import recipients

from .models import Activity, Enrolment, Session

REMINDER_DAYS = "activities.reminder_days_before"  # VC-23
REMINDER = "recordatori-activitat"
OUTCOME = "resultat-curs"
CERTIFICATE = "certificat-emes"
REINFORCEMENT = "reforc-confirmat"
LIVE = (Activity.Status.OPEN, Activity.Status.REGISTRATION_CLOSED, Activity.Status.IN_PROGRESS)


def _send(template, person, context) -> bool:
    to = recipients.email_for(person)
    if not to:
        return False
    return mail.queue_email(template, to=to, person=person, context=context) is not None


def _confirmed(activity):
    return Enrolment.objects.filter(activity=activity, status=Enrolment.Status.CONFIRMED)


def send_reminders(today=None) -> int:
    """Els recordatoris d'avui. Torna quants correus s'han posat a la cua.
    shortcut: si la tasca es tornés a executar el mateix dia, es repetirien; cal un registre
    d'enviats si la cua deixa de garantir una execució per dia."""
    today = today or timezone.localdate()
    day = today + datetime.timedelta(days=business_settings.get(REMINDER_DAYS, today))
    start = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min))
    sent = 0
    sessions = Session.objects.filter(
        cancelled=False, activity__status__in=LIVE, starts_at__gte=start,
        starts_at__lt=start + datetime.timedelta(days=1),
    ).select_related("activity", "place", "reinforcement_for__person")  # fmt: skip
    for session in sessions:
        context = {
            "title": session.activity.title, "day": day,
            "time": timezone.localtime(session.starts_at).strftime("%H:%M"),
            "place": session.place.name,
        }  # fmt: skip
        if session.reinforcement_for_id:
            rows = [session.reinforcement_for]
        else:
            rows = _confirmed(session.activity).select_related("person")
        sent += sum(_send(REMINDER, row.person, context) for row in rows)
    outings = Activity.objects.filter(
        kind=Activity.Kind.OUTING, status__in=LIVE, starts_on=day
    ).select_related("place")
    for outing in outings:
        context = {"title": outing.title, "day": day, "time": "",
                   "place": outing.place.name if outing.place_id else ""}  # fmt: skip
        sent += sum(
            _send(REMINDER, row.person, context)
            for row in _confirmed(outing).select_related("person")
        )
    return sent


def notify_outcome(outcome) -> bool:
    enrolment = outcome.enrolment
    context = {"title": enrolment.activity.title, "passed": outcome.result == outcome.Result.PASS}
    return _send(OUTCOME, enrolment.person, context)


def notify_certificate(outcome) -> bool:
    enrolment = outcome.enrolment
    context = {"title": enrolment.activity.title, "number": outcome.certificate_number}
    return _send(CERTIFICATE, enrolment.person, context)


def notify_reinforcement(proposal, sessions) -> bool:
    enrolment = proposal.enrolment
    items = [
        {"day": timezone.localdate(s.starts_at),
         "time": timezone.localtime(s.starts_at).strftime("%H:%M"), "place": s.place.name}
        for s in sessions
    ]  # fmt: skip
    amount = charges.euros(proposal.price_cents) if proposal.price_cents else ""
    context = {"title": enrolment.activity.title, "sessions": items, "amount": amount}
    return _send(REINFORCEMENT, enrolment.person, context)
