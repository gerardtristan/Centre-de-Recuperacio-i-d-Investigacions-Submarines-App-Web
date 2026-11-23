"""Activitats a l'administració (T-M02-06a i 06b; vistes portades de la branca aparcada sobre els
serveis de `master`): llistat i fitxa (06a), i crear i editar un curs o una sortida amb el lloc, el
preu estàndard i el motiu del preu diferent (06b; vistes de la T-M02-40, RN-M02-40 i 41).

- **Permís:** AC7 (`activities.manage`). El decorador el comprova abans que res i el servei, de
  nou. Sense permís, sempre «no trobat», també per a una activitat que no existeix.
- **Dades personals:** la fitxa només mostra el nom de la persona responsable i el dels
  instructors; cap inscrit. La llista de responsables només ofereix qui pot gestionar activitats.
- Publicar, tancar, cancel·lar, sessions, programa i duplicar són de la T-M02-06c.
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.charges import euros
from apps.core.permissions import has_perm, permission_required

from .. import enrolment, guests, material_cost, services, sessions, states
from ..forms import ActivityForm, GuestEnrolmentForm, MaterialCostForm
from ..models import Activity, SpecialitiesRule
from ..permissions import ENROL_IN_PERSON, MANAGE, MATERIAL_COST, MATERIAL_COST_FIELD, require
from . import see_other

MARGIN_VIEW = "expenses.margin.view"  # MG6: el marge és del 09; aquí només l'enllaç
S = Activity.Status
K = Activity.Kind
PAGE_SIZE = 25
ADD_TITLES = {K.COURSE: _("Curs nou"), K.OUTING: _("Sortida nova")}
ADDED = _("Activitat creada en esborrany. Afegeix-hi les sessions o el programa i publica-la.")
SAVED = _("Canvis desats. Queden al registre d'activitat amb el valor anterior.")
UNCHANGED = _("No hi havia cap canvi per desar.")
DESK_DONE = _("Inscripció feta. Si es paga, la persona rebrà al correu l'enllaç per pagar.")
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


def _to_detail(activity):
    return see_other("administration:activity_detail", activity.pk)


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


def _create(request, kind):
    post = request.POST if request.method == "POST" else None
    form = ActivityForm(post, kind=kind, user=request.user)
    if request.method == "POST" and form.is_valid():
        create = services.create_course if kind == K.COURSE else services.create_outing
        try:
            activity = create(by=request.user, request=request, **form.service_data())
        except ValidationError as error:  # una regla del servei: al formulari, sense desar res
            form.add_error(None, error)
        else:
            messages.success(request, ADDED)
            return _to_detail(activity)
    context = {"form": form, "title": ADD_TITLES[kind], "activity": None}
    return render(request, "activities/activity_form.html", context)


@never_cache
@permission_required(MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def activity_course_add_view(request):
    return _create(request, K.COURSE)


@never_cache
@permission_required(MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def activity_outing_add_view(request):
    return _create(request, K.OUTING)


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


def _material_cost(request, activity, form=None):
    """C7 per veure el cost previst; AC23 (per objecte) per canviar-lo (RN-M02-43, CA-M02-45)."""
    if not has_perm(request.user, MATERIAL_COST_FIELD, activity):
        return None
    if form is None and states.is_editable(activity):
        if has_perm(request.user, MATERIAL_COST, activity, write=True):
            cost = activity.material_cost_cents
            form = MaterialCostForm(initial={"cost": cost, "note": activity.material_cost_note})
    cost, standard = activity.material_cost_cents, activity.standard_material_cost_cents
    return {
        "cost": None if cost is None else euros(cost),
        "standard": None if standard is None else euros(standard),
        "differs": standard is not None and cost != standard,
        "form": form,
    }


DESK_LABELS = {
    "adult_declared": _("La persona diu que és major d'edat (pregunta-li-ho)"),
    "accept_privacy": _("Ha llegit i accepta la política de privacitat"),
}


def _desk_form(request, activity, data=None):
    """Inscripció presencial d'un convidat (T-M02-14; AC5): només si l'activitat és oberta a no
    socis i té les inscripcions obertes. Qui atén marca les caselles després de preguntar."""
    if data is None and not (
        has_perm(request.user, ENROL_IN_PERSON, write=True)
        and activity.open_to_non_members
        and enrolment.is_open(activity)
    ):
        return None
    form = GuestEnrolmentForm(data, min_age=activity.min_age, prefix="presencial")
    for name, label in DESK_LABELS.items():
        if name in form.fields:
            form.fields[name].label = label
    return form


def _detail(request, activity, material_form=None, desk_form=None):
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
        "editable": states.is_editable(activity),
        "margin_link": has_perm(request.user, MARGIN_VIEW, activity),
        "material": _material_cost(request, activity, material_form),
        "desk_form": desk_form or _desk_form(request, activity),
    }
    return render(request, "activities/activity_detail.html", context)


@never_cache
@permission_required(MANAGE)
@require_http_methods(["GET", "POST"])
def activity_detail_view(request, pk):
    """GET: la fitxa. POST: el cost de material previst (AC23 per objecte; T-M02-40c) o la
    inscripció presencial d'un convidat (AC5; T-M02-14)."""
    activity = _activity(pk)
    if request.method == "GET":
        return _detail(request, activity)
    if "inscripcio_presencial" in request.POST:
        return _enrol_at_desk(request, activity)
    # Fora del seu abast, «no trobat» i registre (el servei ho torna a mirar)
    require(request.user, MATERIAL_COST, activity, request=request)
    form = MaterialCostForm(request.POST)
    if form.is_valid():
        try:
            material_cost.set_material_cost(
                activity, form.cleaned_data["cost"], by=request.user, request=request,
                note=form.cleaned_data["note"],
            )  # fmt: skip
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, _("Cost de material previst desat. No canvia cap càrrec."))
            return _to_detail(activity)
    return _detail(request, activity, form)


def _enrol_at_desk(request, activity):
    require(request.user, ENROL_IN_PERSON, request=request)
    form = _desk_form(request, activity, request.POST)
    if form.is_valid():
        try:
            guests.enrol_guest(activity, form.cleaned_data, by=request.user, request=request)
        except ValidationError as error:
            form.add_error(None, error.messages[0])
        else:
            messages.success(request, DESK_DONE)
            return _to_detail(activity)
    return _detail(request, activity, desk_form=form)


@never_cache
@permission_required(MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def activity_edit_view(request, pk):
    activity = _activity(pk)
    post = request.POST if request.method == "POST" else None
    form = ActivityForm(post, kind=activity.kind, activity=activity, user=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            changed = services.update_activity(
                activity, by=request.user, request=request, **form.service_data()
            )
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, SAVED if changed else UNCHANGED)
            return _to_detail(activity)
    context = {"form": form, "title": _("Edita l'activitat"), "activity": activity}
    return render(request, "activities/activity_form.html", context)
