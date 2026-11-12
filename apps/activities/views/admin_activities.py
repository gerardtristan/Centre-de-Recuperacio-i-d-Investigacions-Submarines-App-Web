"""Activitats a l'administració (T-M02-06; P-M02-B; RN-M02-02, RN-M02-06 i RN-M02-20; CA-M02-02 i
CA-M02-03): llistat, fitxa, crear i editar un curs o una sortida, publicar, tancar i reobrir
inscripcions, marcar com a feta, cancel·lar amb motiu, sessions amb instructors i programa del
dia.

- **Permís:** AC7 (`activities.manage`). Es comprova abans que el mètode i, de nou, a cada servei.
  Sense permís, sempre «no trobat», també per a una activitat que no existeix: la resposta no diu
  si hi és.
- **Per objecte:** una sessió només s'obre dins de la seva activitat; amb l'identificador d'una
  altra activitat, «no trobat».
- **Dades personals:** la fitxa només mostra el nom de la persona responsable i el dels
  instructors. Les llistes desplegables només ofereixen persones que poden fer aquell paper.
- Passar llista, participants i avaluació no són aquí (T-M02-16, T-M02-17 i T-M02-24): l'instructor
  encara no té cap pantalla en aquest mòdul.
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core.charges import euros
from apps.core.permissions import permission_required

from .. import catalogue, duplicate, services, sessions, states
from ..forms import (
    ActivityForm,
    DuplicateForm,
    ProgrammeForm,
    ReasonForm,
    ReopenForm,
    SessionForm,
)
from ..models import Activity, Session
from ..permissions import MANAGE
from . import run, see_other

S = Activity.Status
K = Activity.Kind
PAGE_SIZE = 25
ADD_TITLES = {K.COURSE: _("Curs nou"), K.OUTING: _("Sortida nova")}
FILTERS = (
    ("", _("Totes")),
    ("vives", _("En preparació o en marxa")),
    (S.DRAFT, S.DRAFT.label),
    (S.OPEN, S.OPEN.label),
    (S.REGISTRATION_CLOSED, S.REGISTRATION_CLOSED.label),
    (S.IN_PROGRESS, S.IN_PROGRESS.label),
    (S.DONE, S.DONE.label),
    (S.CANCELLED, S.CANCELLED.label),
)


def _activity(pk):
    return get_object_or_404(
        Activity.objects.select_related(
            "catalogue_entry",
            "outing_type",
            "subtype",
            "project",
            "department",
            "responsible",
            "min_level",
        ),
        pk=pk,
    )


def _session(activity, session_pk):
    # Per objecte: la sessió ha de ser d'aquesta activitat.
    return get_object_or_404(Session, pk=session_pk, activity=activity)


def _to_detail(activity):
    return see_other("administration:activity_detail", activity.pk)


@never_cache
@permission_required(MANAGE)
@require_GET
def activities_view(request):
    state, kind = request.GET.get("estat", "vives"), request.GET.get("classe", "")
    activities = Activity.objects.select_related("catalogue_entry", "outing_type")
    if state == "vives":
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
        "filtered": bool(kind) or state != "vives",
    }
    return render(request, "activities/activity_list.html", context)


def _create(request, kind):
    form = ActivityForm(
        request.POST if request.method == "POST" else None, kind=kind, user=request.user
    )
    if request.method == "POST" and form.is_valid():
        data = form.service_data()
        create = services.create_course if kind == K.COURSE else services.create_outing
        created = []
        saved = run(
            request,
            form,
            lambda: created.append(create(by=request.user, request=request, **data)),
            _("Activitat creada en esborrany. Afegeix-hi les sessions o el programa i publica-la."),
        )
        if saved:
            return _to_detail(created[0])
    context = {"form": form, "title": ADD_TITLES[kind], "kind": kind, "activity": None}
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


def _steps(activity, today):
    """Què es pot fer ara amb l'activitat (només per mostrar els botons: el servei ho decideix)."""
    targets = states.allowed_targets(activity)
    reachable_done = S.DONE in targets or (
        activity.kind == K.COURSE and activity.status in (S.OPEN, S.REGISTRATION_CLOSED)
    )
    return {
        "editable": states.is_editable(activity),
        "publish": activity.status == S.DRAFT,
        "close": activity.status == S.OPEN,
        "reopen": activity.status == S.REGISTRATION_CLOSED,
        "done": reachable_done and today >= states.last_day(activity),
        "cancel": S.CANCELLED in targets,
    }


@never_cache
@permission_required(MANAGE)
@require_GET
def activity_detail_view(request, pk):
    activity = _activity(pk)
    now = timezone.now()
    today = timezone.localdate(now)
    without_instructor = set(
        sessions.sessions_without_instructor(now)
        .filter(activity=activity)
        .values_list("pk", flat=True)
    )
    session_rows = [
        {
            "session": session,
            "instructors": list(session.instructors.all()),
            "needs_instructor": session.pk in without_instructor,
        }
        for session in activity.sessions.prefetch_related("instructors")
    ]
    catalogue_price = None
    if activity.kind == K.COURSE:
        current = catalogue.price_on(activity.catalogue_entry, today)
        if (current.member_cents, current.non_member_cents) != (
            activity.price_member_cents,
            activity.price_non_member_cents,
        ):
            catalogue_price = {
                "member": euros(current.member_cents),
                "non_member": euros(current.non_member_cents),
            }
    context = {
        "activity": activity,
        "price_member": euros(activity.price_member_cents),
        "price_non_member": euros(activity.price_non_member_cents),
        "catalogue_price": catalogue_price,
        "session_rows": session_rows,
        "needs_instructor": bool(without_instructor),
        "blocks": activity.programme_blocks.all(),
        "specialities": [entry.name for entry in activity.required_specialities.all()],
        "any_speciality": activity.specialities_rule == Activity.SpecialitiesRule.ANY,
        "steps": _steps(activity, today),
        "last_day": states.last_day(activity),
    }
    return render(request, "activities/activity_detail.html", context)


@never_cache
@permission_required(MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def activity_edit_view(request, pk):
    activity = _activity(pk)
    if not states.is_editable(activity):
        messages.error(
            request,
            _("Una activitat «%(status)s» ja no es pot editar.")
            % {"status": activity.get_status_display()},
        )
        return _to_detail(activity)
    form = ActivityForm(
        request.POST if request.method == "POST" else None, kind=activity.kind, activity=activity
    )
    if request.method == "POST" and form.is_valid():
        saved = run(
            request,
            form,
            lambda: services.update_activity(
                activity, by=request.user, request=request, **form.service_data()
            ),
            lambda changed: (
                _("Canvis desats. Queden al registre d'activitat amb el valor anterior.")
                if changed
                else _("No hi havia cap canvi per desar.")
            ),
        )
        if saved:
            return _to_detail(activity)
    context = {
        "form": form,
        "title": _("Edita l'activitat"),
        "kind": activity.kind,
        "activity": activity,
    }
    return render(request, "activities/activity_form.html", context)


STEPS = {
    "publica": (states.publish, _("Activitat publicada: ja té les inscripcions obertes.")),
    "tanca": (states.close_registration, _("Inscripcions tancades.")),
    "feta": (states.mark_done, _("Activitat marcada com a feta.")),
}


@never_cache
@permission_required(MANAGE, write=True)
@require_POST
def activity_step_view(request, pk):
    activity = _activity(pk)
    step = STEPS.get(request.POST.get("pas"))
    if step is None:
        messages.error(request, _("No s'ha pogut fer: torna-ho a provar des de la fitxa."))
        return _to_detail(activity)
    action, done = step
    try:
        action(activity, by=request.user, request=request)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, done)
    return _to_detail(activity)


@never_cache
@permission_required(MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def activity_reopen_view(request, pk):
    activity = _activity(pk)
    form = ReopenForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        saved = run(
            request,
            form,
            lambda: states.reopen_registration(
                activity,
                by=request.user,
                closes_at=form.cleaned_data["closes_at"],
                request=request,
            ),
            _("Inscripcions reobertes."),
        )
        if saved:
            return _to_detail(activity)
    context = {"form": form, "activity": activity}
    return render(request, "activities/activity_reopen.html", context)


def _reason(request, activity, title, lead, button, action, done):
    form = ReasonForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        if run(request, form, lambda: action(form.cleaned_data["reason"]), done):
            return _to_detail(activity)
    context = {"form": form, "activity": activity, "title": title, "lead": lead, "button": button}
    return render(request, "activities/reason_form.html", context)


@never_cache
@permission_required(MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def activity_cancel_view(request, pk):
    activity = _activity(pk)
    return _reason(
        request,
        activity,
        _("Cancel·la l'activitat"),
        _("L'activitat queda cancel·lada i ja no es pot editar ni tornar a obrir."),
        _("Cancel·la l'activitat"),
        lambda reason: states.cancel(activity, by=request.user, reason=reason, request=request),
        _("Activitat cancel·lada. Queda al registre d'activitat amb el motiu."),
    )


# --- Sessions -------------------------------------------------------------------------------------


def _session_form(request, activity, session, title):
    form = SessionForm(request.POST if request.method == "POST" else None, session=session)
    if request.method == "POST" and form.is_valid():
        data = dict(form.cleaned_data)
        people = list(data.pop("instructors"))

        def save():
            if session is None:
                return sessions.add_session(
                    activity, by=request.user, instructors=people, request=request, **data
                )
            changed = sessions.update_session(session, by=request.user, request=request, **data)
            moved = sessions.set_instructors(session, people, by=request.user, request=request)
            return changed or moved

        saved = run(
            request,
            form,
            save,
            lambda result: (
                _("Sessió desada. Queda al registre d'activitat.")
                if result
                else _("No hi havia cap canvi per desar.")
            ),
        )
        if saved:
            return _to_detail(activity)
    context = {"form": form, "activity": activity, "session": session, "title": title}
    return render(request, "activities/session_form.html", context)


@never_cache
@permission_required(MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def session_add_view(request, pk):
    return _session_form(request, _activity(pk), None, _("Afegeix una sessió"))


@never_cache
@permission_required(MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def session_edit_view(request, pk, session_pk):
    activity = _activity(pk)
    return _session_form(request, activity, _session(activity, session_pk), _("Edita la sessió"))


@never_cache
@permission_required(MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def session_cancel_view(request, pk, session_pk):
    activity = _activity(pk)
    session = _session(activity, session_pk)
    return _reason(
        request,
        activity,
        _("Cancel·la la sessió"),
        _("La sessió no s'esborra: queda cancel·lada amb el motiu i deixa de comptar."),
        _("Cancel·la la sessió"),
        lambda reason: sessions.cancel_session(
            session, by=request.user, reason=reason, request=request
        ),
        _("Sessió cancel·lada. Queda al registre d'activitat amb el motiu."),
    )


# --- Programa del dia -----------------------------------------------------------------------------


@never_cache
@permission_required(MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def activity_programme_view(request, pk):
    activity = _activity(pk)
    form = ProgrammeForm(
        request.POST if request.method == "POST" else None, blocks=activity.programme_blocks.all()
    )
    if request.method == "POST" and form.is_valid():
        saved = run(
            request,
            form,
            lambda: sessions.set_programme(
                activity, form.blocks(), by=request.user, request=request
            ),
            _("Programa desat."),
        )
        if saved:
            return _to_detail(activity)
    context = {"form": form, "activity": activity}
    return render(request, "activities/programme_form.html", context)


# --- Duplicar (T-M02-07) --------------------------------------------------------------------------


@never_cache
@permission_required(MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def activity_duplicate_view(request, pk):
    """Crea una còpia en esborrany amb les dates desplaçades (decisió 026; RN-M02-21)."""
    activity = _activity(pk)
    form = DuplicateForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        created = []
        saved = run(
            request,
            form,
            lambda: created.append(
                duplicate.duplicate(
                    activity, form.cleaned_data["new_start"], by=request.user, request=request
                )
            ),
            _("Còpia creada en esborrany. Revisa-la i publica-la quan estigui a punt."),
        )
        if saved:
            return _to_detail(created[0])
    context = {"form": form, "activity": activity}
    return render(request, "activities/activity_duplicate.html", context)
