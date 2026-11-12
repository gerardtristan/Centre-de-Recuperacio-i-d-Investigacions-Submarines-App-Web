"""Resultats ambientals i fitxa de projecte a l'administració (T-M02-20; P-M02-G; AC14;
RN-M02-23; CA-M02-21).

- **Permís:** AC14 (`activities.environment.manage`). Amb «Cons.» (la Junta, a la configuració
  inicial) es veu tot i no es desa res; amb edició, es registren els resultats. Es comprova abans
  que el mètode i, de nou, al servei. Sense permís, «no trobat».
- **Per objecte:** la pantalla de resultats només existeix per a una sortida de medi ambient; per a
  qualsevol altra activitat, «no trobat».
- **Dades personals:** cap, tret del nom de qui ha registrat els resultats.
- Res d'això es publica (RN-M02-23). Les fotos no hi són encara.
"""

from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.permissions import permission_required

from .. import environment
from ..forms import ResultsForm
from ..models import Activity, EnvironmentalProject, EnvironmentalResult
from ..permissions import ENVIRONMENT, can
from . import run, see_other


def _result_row(result):
    if result is None:
        return None
    return {
        "kilos": environment.kilos(result.waste_grams),
        "species": result.species.splitlines(),
        "observations": result.observations,
        "recorded_by": result.recorded_by.person,
        "recorded_at": result.recorded_at,
    }


@never_cache
@permission_required(ENVIRONMENT)
@require_GET
def environment_view(request):
    """Projectes amb el que acumulen i sortides de medi ambient amb els seus resultats."""
    projects = [
        {"project": project, "summary": environment.project_summary(project)}
        for project in EnvironmentalProject.objects.select_related("department")
    ]
    outings = (
        Activity.objects.filter(kind=Activity.Kind.OUTING, outing_type__is_environmental=True)
        .exclude(status__in=[Activity.Status.DRAFT, Activity.Status.CANCELLED])
        .select_related("outing_type", "subtype", "project")
        .order_by("-starts_on", "-pk")
    )
    recorded = dict(
        EnvironmentalResult.objects.filter(activity__in=outings).values_list(
            "activity_id", "waste_grams"
        )
    )
    rows = [
        {
            "activity": activity,
            "has_results": activity.pk in recorded,
            "kilos": environment.kilos(recorded.get(activity.pk)),
            "can_record": environment.can_record(activity),
        }
        for activity in outings
    ]
    context = {"projects": projects, "rows": rows, "can_edit": can(request.user, ENVIRONMENT)}
    return render(request, "activities/environment_list.html", context)


@never_cache
@permission_required(ENVIRONMENT)
@require_GET
def project_detail_view(request, pk):
    project = get_object_or_404(EnvironmentalProject.objects.select_related("department"), pk=pk)
    summary = environment.project_summary(project)
    rows = [
        {"activity": activity, "result": _result_row(result)}
        for activity, result in summary.outings
    ]
    context = {"project": project, "summary": summary, "rows": rows}
    return render(request, "activities/project_detail.html", context)


@never_cache
@permission_required(ENVIRONMENT)
@require_http_methods(["GET", "POST"])
def activity_results_view(request, pk):
    activity = get_object_or_404(
        Activity.objects.select_related("outing_type", "subtype", "project"), pk=pk
    )
    if not environment.is_environmental(activity):
        raise Http404  # només les sortides de medi ambient tenen aquesta pantalla
    result = environment.results_for(activity)
    can_edit = can(request.user, ENVIRONMENT)
    form = ResultsForm(request.POST if request.method == "POST" else None, result=result)
    if request.method == "POST":
        if not can_edit:
            raise Http404  # «Cons.» veu, però no desa
        if form.is_valid():
            saved = run(
                request,
                form,
                lambda: environment.record_results(
                    activity, by=request.user, request=request, **form.cleaned_data
                ),
                _("Resultats desats. Queden al registre d'activitat."),
            )
            if saved:
                return see_other("administration:activity_results", activity.pk)
    context = {
        "activity": activity,
        "form": form,
        "result": _result_row(result),
        "can_edit": can_edit,
        "can_record": environment.can_record(activity),
    }
    return render(request, "activities/activity_results.html", context)
