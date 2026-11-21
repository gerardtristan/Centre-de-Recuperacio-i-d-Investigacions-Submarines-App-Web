"""Activitats a l'administració (T-M02-06a; vistes portades de la branca aparcada sobre els serveis
de `master`): llistat i fitxa. Crear i editar (amb el lloc, el preu estàndard i el motiu,
RN-M02-40 i 41) és la T-M02-06b.

- **Permís:** AC7 (`activities.manage`). El decorador el comprova abans que res i el servei, de
  nou. Sense permís, sempre «no trobat», també per a una activitat que no existeix.
- **Dades personals:** la fitxa només mostra el nom de la persona responsable i el dels
  instructors; cap inscrit.
- Publicar, tancar, cancel·lar, sessions, programa i duplicar són de la T-M02-06c.
"""

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.core.charges import euros
from apps.core.permissions import has_perm, permission_required

from .. import sessions, states
from ..models import Activity, SpecialitiesRule
from ..permissions import MANAGE

MARGIN_VIEW = "expenses.margin.view"  # MG6: el marge és del 09; aquí només l'enllaç
S = Activity.Status
K = Activity.Kind
PAGE_SIZE = 25
LIVE = "vives"
FILTERS = (
    ("", _("Totes")),
    (LIVE, _("En preparació o en marxa")),
    *((status.value, status.label) for status in S),
)


def _activity(pk):
    related = ("catalogue_entry", "outing_type", "subtype", "project", "department")
    return get_object_or_404(
        Activity.objects.select_related(*related, "responsible", "min_level", "place"), pk=pk
    )


@never_cache
@permission_required(MANAGE)
@require_GET
def activities_view(request):
    state, kind = request.GET.get("estat", LIVE), request.GET.get("classe", "")
    activities = Activity.objects.select_related("catalogue_entry", "outing_type", "place")
    if state == LIVE:
        activities = activities.filter(status__in=states.EDITABLE_STATUSES)
    elif state in S.values:
        activities = activities.filter(status=state)
    else:
        state = ""
    if kind in K.values:
        activities = activities.filter(kind=kind)
    else:
        kind = ""
    page = Paginator(activities.order_by("starts_on", "pk"), PAGE_SIZE).get_page(
        request.GET.get("pagina")
    )
    context = {
        "page": page,
        "state": state,
        "kind": kind,
        "filters": FILTERS,
        "kinds": (("", _("Cursos i sortides")), *K.choices),
        "filtered": bool(kind) or state != LIVE,
    }
    return render(request, "activities/activity_list.html", context)


def _standard(activity):
    """La còpia estàndard del preu, si n'hi ha i és diferent del preu de l'activitat (RN-M02-41)."""
    member, non_member = (
        activity.standard_price_member_cents,
        activity.standard_price_non_member_cents,
    )
    if member is None or (member, non_member) == (
        activity.price_member_cents,
        activity.price_non_member_cents,
    ):
        return None
    return {"member": euros(member), "non_member": euros(non_member)}


@never_cache
@permission_required(MANAGE)
@require_GET
def activity_detail_view(request, pk):
    activity = _activity(pk)
    without_instructor = set(
        sessions.sessions_without_instructor(timezone.now())
        .filter(activity=activity)
        .values_list("pk", flat=True)
    )
    session_rows = [
        {
            "session": session,
            "instructors": list(session.instructors.all()),
            "needs_instructor": session.pk in without_instructor,
        }
        for session in activity.sessions.select_related("place").prefetch_related("instructors")
    ]
    context = {
        "activity": activity,
        "price_member": euros(activity.price_member_cents),
        "price_non_member": euros(activity.price_non_member_cents),
        "standard": _standard(activity),
        "session_rows": session_rows,
        "needs_instructor": bool(without_instructor),
        "blocks": activity.programme_blocks.select_related("place"),
        "specialities": [entry.name for entry in activity.required_specialities.all()],
        "any_speciality": activity.specialities_rule == SpecialitiesRule.ANY,
        "margin_link": has_perm(request.user, MARGIN_VIEW, activity),
    }
    return render(request, "activities/activity_detail.html", context)
