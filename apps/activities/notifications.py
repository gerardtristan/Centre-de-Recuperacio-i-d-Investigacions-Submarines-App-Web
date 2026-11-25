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

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.invitations import has_active_personal_account
from apps.core import audit, business_settings, charges, mail
from apps.members import recipients

from . import permissions
from .models import Activity, Enrolment, ReminderSent, Session

REMINDER_DAYS = "activities.reminder_days_before"  # VC-23
REMINDER = "recordatori-activitat"
OUTCOME = "resultat-curs"
CERTIFICATE = "certificat-emes"
REINFORCEMENT = "reforc-confirmat"
MESSAGE_SENT = "activities.message.sent"
LIVE = (Activity.Status.OPEN, Activity.Status.REGISTRATION_CLOSED, Activity.Status.IN_PROGRESS)


def _send(template, person, context) -> bool:
    to = recipients.email_for(person)
    if not to:
        return False
    return mail.queue_email(template, to=to, person=person, context=context) is not None


def _confirmed(activity):
    return Enrolment.objects.filter(activity=activity, status=Enrolment.Status.CONFIRMED)


def _remind(enrolment, session, context) -> bool:
    """Un recordatori un sol cop: la fila de `ReminderSent` i el correu van junts; si la fila ja hi
    és (restricció única), no s'envia res. Sense adreça, ni fila ni correu."""
    to = recipients.email_for(enrolment.person)
    if not to:
        return False
    try:
        with transaction.atomic():
            ReminderSent.objects.create(
                enrolment=enrolment, session=session, kind=ReminderSent.Kind.REMINDER
            )
            mail.queue_email(REMINDER, to=to, person=enrolment.person, context=context)
    except IntegrityError:
        return False
    return True


def send_reminders(today=None) -> int:
    """Els recordatoris d'avui. Torna quants correus s'han posat a la cua. Idempotent: tornar-la
    a executar no envia cap recordatori que ja s'hagi enviat."""
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
        sent += sum(_remind(row, session, context) for row in rows)
    outings = Activity.objects.filter(
        kind=Activity.Kind.OUTING, status__in=LIVE, starts_on=day
    ).select_related("place")
    for outing in outings:
        context = {"title": outing.title, "day": day, "time": "",
                   "place": outing.place.name if outing.place_id else ""}  # fmt: skip
        sent += sum(
            _remind(row, None, context) for row in _confirmed(outing).select_related("person")
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


# --- T-M02-21b: inscripció, programa i missatge ------------------------------------------------

CONFIRMED = "confirmacio-inscripcio"
PAYMENT = "termini-pagament"
OFFER = "oferta-placa"
CANCELLED = "cancellacio-inscripcio"
CHANGE = "canvi-programa"
MESSAGE = "missatge-activitat"
MAX_SUBJECT = 120
MAX_BODY = 4000


def _once(enrolment, kind, template, context) -> bool:
    """Un avís del cicle de la inscripció un sol cop (com el recordatori): la fila de
    `ReminderSent` i el correu van junts; si ja hi és, no s'envia res."""
    to = recipients.email_for(enrolment.person)
    if not to:
        return False
    try:
        with transaction.atomic():
            ReminderSent.objects.create(enrolment=enrolment, session=None, kind=kind)
            mail.queue_email(template, to=to, person=enrolment.person, context=context)
    except IntegrityError:
        return False
    return True


def on_confirmed(sender, enrolment, **kwargs) -> None:
    """Subscriptor de `extensions.enrolment_confirmed`: pagada, gratuïta o oferta acceptada."""
    activity = enrolment.activity
    context = {"title": activity.title, "starts_on": activity.starts_on}
    _once(enrolment, ReminderSent.Kind.CONFIRMED, CONFIRMED, context)


def notify_payment(enrolment) -> bool:
    """La plaça reservada i el termini per pagar-la. Sense compte personal actiu (un convidat, web o
    del taulell), la pantalla de pagament demana sessió: ja rep l'enllaç segur de convidat."""
    if not enrolment.charge_id or not has_active_personal_account(enrolment.person):
        return False
    link = settings.PUBLIC_SITE_URL + reverse("payments:charge", args=[enrolment.charge_id])
    context = {
        "title": enrolment.activity.title, "amount": charges.euros(enrolment.price_cents),
        "due_at": timezone.localtime(enrolment.payment_due_at), "link": link,
    }  # fmt: skip
    return _once(enrolment, ReminderSent.Kind.PAYMENT, PAYMENT, context)


def notify_offer(enrolment) -> bool:
    context = {"title": enrolment.activity.title,
               "expires_at": timezone.localtime(enrolment.offer_expires_at)}  # fmt: skip
    return _once(enrolment, ReminderSent.Kind.OFFER, OFFER, context)


def notify_cancelled(enrolment, *, by_club, reason="") -> bool:
    context = {"title": enrolment.activity.title, "by_club": by_club,
               "reason": reason if by_club else ""}  # fmt: skip
    return _once(enrolment, ReminderSent.Kind.CANCELLED, CANCELLED, context)


def _live_rows(activity, session=None):
    if session is not None and session.reinforcement_for_id:
        return [session.reinforcement_for]
    return Enrolment.objects.filter(activity=activity, status__in=Enrolment.LIVE).select_related(
        "person"
    )


def notify_change(session) -> int:
    """CA-M02-20: un canvi d'horari o de lloc d'una sessió (o una sessió cancel·lada) d'una
    activitat oberta, a tots els inscrits vius. Cada canvi és un avís nou."""
    activity = session.activity
    if activity.status not in LIVE:
        return 0
    context = {
        "title": activity.title, "day": timezone.localdate(session.starts_at),
        "time": timezone.localtime(session.starts_at).strftime("%H:%M"),
        "place": session.place.name, "cancelled": session.cancelled,
    }  # fmt: skip
    return sum(_send(CHANGE, row.person, context) for row in _live_rows(activity, session))


def send_message(activity, *, by, subject, body, request=None) -> int:
    """AC15: un missatge de l'organitzador a tots els inscrits vius de l'activitat. Queda al
    registre sense el text."""
    permissions.require(by, permissions.MESSAGE, activity, request=request)
    subject, body = (subject or "").strip(), (body or "").strip()
    if not subject or not body:
        raise ValidationError(_("Cal l'assumpte i el text del missatge."))
    if len(subject) > MAX_SUBJECT or len(body) > MAX_BODY:
        raise ValidationError(
            _("L'assumpte té %(s)s caràcters com a màxim i el text, %(b)s.")
            % {"s": MAX_SUBJECT, "b": MAX_BODY}
        )
    context = {"title": activity.title, "subject": subject, "body": body,
               "sender": str(by.person)}  # fmt: skip
    sent = sum(_send(MESSAGE, row.person, context) for row in _live_rows(activity))
    audit.record(MESSAGE_SENT, actor=by, target=activity, details={"emails": sent},
                 request=request)  # fmt: skip
    return sent
