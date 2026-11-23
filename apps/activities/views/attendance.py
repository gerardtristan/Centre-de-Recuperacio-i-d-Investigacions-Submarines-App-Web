"""Passar llista des del mòbil i incidències (T-M02-16b; P-M02-E; CA-M02-16 i 17; AC9).

- **«Passar llista»:** les sessions (cursos) i les sortides d'avui i de després on el compte té AC9
  per objecte: l'instructor, només les seves sessions. Pensada per a 390 px.
- **La llista:** els serveis de `attendance` (`roll`, `mark`, `incidents`, `add_incident`) tornen a
  comprovar AC9 per objecte; fora de l'abast, «no trobat» i l'intent queda al registre (CA-M02-16).
- **Sense cobertura** (CA-M02-17): `static/js/passar-llista.js` envia cada marca amb `fetch`; si
  falla, la fila diu «Pendent d'enviar» i es reenvia sola en tornar la connexió. La marca és
  idempotent al servidor: reenviar-la no duplica res. Sense JavaScript, el formulari funciona igual.
"""

import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from .. import attendance
from ..models import Activity, Enrolment, Incident, Session
from ..permissions import ATTENDANCE, can, sessions_for
from . import see_other

LIST_LIMIT = 20  # shortcut: les 20 primeres d'avui endavant; si en calen més, paginar


@never_cache
@require_GET
def sessions_view(request):
    user = request.user
    if not can(user, ATTENDANCE, write=False):
        raise Http404
    since = timezone.localdate() - datetime.timedelta(days=1)
    start = timezone.make_aware(datetime.datetime.combine(since, datetime.time.min))
    items = []
    sessions = (
        sessions_for(user, ATTENDANCE, write=False)
        .filter(
            cancelled=False, starts_at__gte=start, activity__status__in=attendance.ROLL_STATUSES
        )
        .select_related("activity", "place")
        .order_by("starts_at")[:LIST_LIMIT]
    )
    for session in sessions:
        items.append({"day": timezone.localdate(session.starts_at), "activity": session.activity,
                      "session": session})  # fmt: skip
    outings = Activity.objects.filter(
        kind=Activity.Kind.OUTING, starts_on__gte=since, status__in=attendance.ROLL_STATUSES
    ).order_by("starts_on")[:LIST_LIMIT]
    for outing in outings:
        if can(user, ATTENDANCE, outing, write=False):
            items.append({"day": outing.starts_on, "activity": outing, "session": None})
    items.sort(key=lambda item: item["day"])
    return render(request, "activities/attendance_sessions.html", {"items": items[:LIST_LIMIT]})


def _target(pk, session_pk):
    activity = get_object_or_404(Activity, pk=pk)
    session = None
    if session_pk is not None:
        session = get_object_or_404(Session, pk=session_pk, activity=activity)
    return activity, session


def _wants_json(request) -> bool:
    return "application/json" in request.headers.get("Accept", "")


def _mark(request, activity, session):
    enrolment = get_object_or_404(Enrolment, pk=request.POST.get("inscripcio"), activity=activity)
    present = {"1": True, "0": False}.get(request.POST.get("present"))
    try:
        attendance.mark(enrolment, session, present=present, by=request.user, request=request)
    except ValidationError as error:
        if _wants_json(request):
            return JsonResponse({"error": " ".join(error.messages)}, status=400)
        messages.error(request, " ".join(error.messages))
        return None
    if _wants_json(request):
        return JsonResponse({"present": present})
    return None


def _incident(request, activity, session):
    try:
        attendance.add_incident(
            activity, by=request.user, kind=request.POST.get("classe", ""),
            description=request.POST.get("descripcio", ""), session=session, request=request,
        )  # fmt: skip
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, _("Incidència registrada."))


@never_cache
@require_http_methods(["GET", "POST"])
def roll_view(request, pk, session_pk=None):
    activity, session = _target(pk, session_pk)
    # El servei comprova AC9 per objecte (i deixa l'intent al registre) abans que res.
    roll = attendance.roll(activity, session, viewer=request.user, request=request)
    if request.method == "POST":
        if "descripcio" in request.POST:
            _incident(request, activity, session)
        else:
            response = _mark(request, activity, session)
            if response is not None:
                return response
        args = (activity.pk, session.pk) if session else (activity.pk,)
        name = (
            "administration:attendance_roll_session"
            if session
            else "administration:attendance_roll"
        )
        return see_other(name, *args)
    context = {
        "roll": roll,
        "activity": activity,
        "session": session,
        "day": attendance.day_of(activity, session),
        "incidents": attendance.incidents(activity, session, viewer=request.user, request=request),
        "kinds": Incident.Kind.choices,
        "incident_help": attendance.INCIDENT_HELP,
    }
    return render(request, "activities/attendance_roll.html", context)
