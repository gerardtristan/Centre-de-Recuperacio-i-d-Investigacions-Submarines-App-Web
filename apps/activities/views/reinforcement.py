"""Classes de reforç (T-M02-18b; P-M02-F passos 2 a 4; RN-M02-14 i 15; CA-M02-18; AC10b i AC11).

- **Proposar** (AC10b, qui fa classe a l'activitat): des del full d'avaluació, una o més classes per
  a un alumne, amb un motiu pedagògic i **sense dades de salut** (RN-M02-17).
- **Classes de reforç del curs**: les propostes de l'activitat. Qui té AC11 (el responsable) les
  confirma, amb una sessió per classe (data, hores, lloc i instructor) i el càrrec del preu de
  reforç de la fitxa, o les rebutja amb motiu. Qui només té AC10b les veu.
- Els serveis de `reinforcement` tornen a comprovar els permisos; sense, «no trobat».
"""

import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core.charges import euros
from apps.core.models import Person

from .. import permissions, reinforcement, sessions
from ..models import Activity, Enrolment, Place, ReinforcementRequest, Session
from ..permissions import REINFORCEMENT_DECIDE, REINFORCEMENT_PROPOSE, can
from . import see_other

PAGE = "administration:reinforcement_list"
REASON_HELP = gettext_lazy("Pedagògic. Sense dades de salut.")


def _course(pk, user, request):
    activity = get_object_or_404(
        Activity.objects.select_related("catalogue_entry"), pk=pk, kind=Activity.Kind.COURSE
    )
    if not can(user, REINFORCEMENT_DECIDE):
        permissions.require(user, REINFORCEMENT_PROPOSE, activity, write=False, request=request)
    return activity


@never_cache
@require_http_methods(["GET", "POST"])
def propose_view(request, pk, enrolment_pk):
    activity = get_object_or_404(Activity, pk=pk, kind=Activity.Kind.COURSE)
    permissions.require(request.user, REINFORCEMENT_PROPOSE, activity, request=request)
    enrolment = get_object_or_404(
        Enrolment.objects.select_related("person"), pk=enrolment_pk, activity=activity
    )
    error = None
    if request.method == "POST":
        try:
            classes = int(request.POST.get("classes", ""))
        except ValueError:
            classes = 0
        try:
            reinforcement.propose(
                enrolment, by=request.user, classes=classes,
                reason=request.POST.get("motiu", ""), request=request,
            )  # fmt: skip
        except ValidationError as exc:
            error = " ".join(exc.messages)
        else:
            messages.success(request, _("Proposta de reforç enviada al responsable."))
            return see_other(PAGE, activity.pk)
    context = {
        "activity": activity,
        "enrolment": enrolment,
        "error": error,
        "max_classes": reinforcement.MAX_CLASSES,
        "reason_help": REASON_HELP,
        "data": request.POST,
    }
    return render(request, "activities/reinforcement_propose.html", context)


def _moment(day, time):
    return timezone.make_aware(datetime.datetime.combine(day, time))


def _sessions_data(post, count):
    """Una entrada per classe a partir del formulari; un camp que falta o mal escrit, error."""
    data = []
    for n in range(1, count + 1):
        try:
            day = datetime.date.fromisoformat(post.get(f"dia-{n}", ""))
            start = datetime.time.fromisoformat(post.get(f"inici-{n}", ""))
            end = datetime.time.fromisoformat(post.get(f"final-{n}", ""))
            place = Place.objects.get(pk=post.get(f"lloc-{n}"))
            teacher = sessions.instructor_people().get(pk=post.get(f"instructor-{n}"))
        except (ValueError, Place.DoesNotExist, Person.DoesNotExist):
            raise ValidationError(
                _("Omple la data, les hores, el lloc i l'instructor de la classe %(n)s.") % {"n": n}
            ) from None
        data.append({
            "kind": post.get(f"classe-{n}", ""), "starts_at": _moment(day, start),
            "ends_at": _moment(day, end), "place": place, "instructors": [teacher],
        })  # fmt: skip
    return data


def _decide(request, activity):
    proposal = get_object_or_404(
        ReinforcementRequest, pk=request.POST.get("proposta"), enrolment__activity=activity
    )
    try:
        if "rebutja" in request.POST:
            reinforcement.reject(
                proposal, by=request.user, reason=request.POST.get("motiu", ""), request=request
            )
            messages.success(request, _("Proposta rebutjada."))
        else:
            reinforcement.confirm(
                proposal, by=request.user, request=request,
                sessions_data=_sessions_data(request.POST, proposal.classes),
            )  # fmt: skip
            messages.success(request, _("Reforç confirmat: s'han creat les classes."))
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))


@never_cache
@require_http_methods(["GET", "POST"])
def list_view(request, pk):
    activity = _course(pk, request.user, request)
    can_decide = can(request.user, REINFORCEMENT_DECIDE)
    if request.method == "POST":
        if not can_decide:
            permissions.require(request.user, REINFORCEMENT_DECIDE, request=request)
        _decide(request, activity)
        return see_other(PAGE, activity.pk)
    proposals = list(
        ReinforcementRequest.objects.filter(enrolment__activity=activity)
        .select_related("enrolment__person", "proposed_by__person")
        .order_by("-created_at", "-id")
    )
    for proposal in proposals:
        proposal.numbers = range(1, proposal.classes + 1)  # una sessió per classe
    price = reinforcement.price_for(activity)
    context = {
        "activity": activity,
        "proposals": proposals,
        "can_decide": can_decide,
        "price": price,
        "price_label": None if price is None else euros(price),
        "places": Place.objects.filter(active=True).order_by("name"),
        "teachers": sessions.instructor_people().order_by("first_name", "last_name"),
        "kinds": Session.Kind.choices,
        "reason_help": REASON_HELP,
    }
    return render(request, "activities/reinforcement_list.html", context)
