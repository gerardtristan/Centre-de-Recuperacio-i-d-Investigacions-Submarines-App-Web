"""Resultats ambientals d'una sortida i fitxa de projecte (T-M02-20b; AC14; CA-M02-21;
RN-M02-23). Amb «Cons.» (la junta) només es veu; amb edició es registra i es corregeix. El servei
(`environment.py`) torna a comprovar el permís i les regles. No es publica res. Les fotos encara no
existeixen (CA-M02-22)."""

from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.permissions import permission_required

from .. import environment
from ..forms import EnvironmentalResultForm
from ..models import Activity, EnvironmentalProject
from ..permissions import ENVIRONMENT, can
from . import see_other


@never_cache
@permission_required(ENVIRONMENT)
@require_http_methods(["GET", "POST"])
def results_view(request, pk):
    activity = get_object_or_404(Activity.objects.select_related("outing_type", "project"), pk=pk)
    if not environment.is_environmental(activity):
        raise Http404
    result = environment.results_for(activity)
    editable = environment.can_record(activity) and can(request.user, ENVIRONMENT)
    form = None
    if request.method == "POST":
        form = EnvironmentalResultForm(request.POST)
        if form.is_valid():
            try:
                environment.record_results(
                    activity, by=request.user, request=request, **form.service_data()
                )
            except ValidationError as error:
                form.add_error(None, error)
            else:
                messages.success(request, _("Resultats desats."))
                return see_other("administration:activity_environment", activity.pk)
    elif editable:
        initial = {"species": "", "observations": ""}
        if result is not None:
            grams = result.waste_grams
            initial = {"kilos": None if grams is None else Decimal(grams) / 1000,
                       "species": result.species, "observations": result.observations}  # fmt: skip
        form = EnvironmentalResultForm(initial=initial)
    context = {
        "activity": activity,
        "result": result,
        "kilos": environment.kilos(result.waste_grams) if result else "",
        "form": form if editable or request.method == "POST" else None,
        "not_yet": not environment.can_record(activity),
    }
    return render(request, "activities/environment_results.html", context)


@never_cache
@permission_required(ENVIRONMENT)
@require_GET
def project_view(request, pk):
    project = get_object_or_404(EnvironmentalProject.objects.select_related("department"), pk=pk)
    context = {"project": project, "summary": environment.project_summary(project)}
    return render(request, "activities/project_detail.html", context)
