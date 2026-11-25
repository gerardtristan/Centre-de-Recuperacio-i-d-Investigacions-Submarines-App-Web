"""Resultats ambientals d'una sortida i fitxa de projecte (T-M02-20b; AC14; CA-M02-21;
RN-M02-23). Amb «Cons.» (la junta) només es veu; amb edició es registra i es corregeix. El servei
(`environment.py`) torna a comprovar el permís i les regles. No es publica res.

Fotos (CA-M02-22; P-41 oberta): només amb `activities.environment_photos_enabled` encès; pujar-les
(autor i permís d'ús obligatoris) i retirar-les amb motiu, amb AC14; la junta les veu. S'obren
per la vista de fitxers privats, que torna a comprovar el permís i l'interruptor."""

from decimal import Decimal

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core.permissions import permission_required

from .. import environment, environment_photos
from ..forms import EnvironmentalResultForm
from ..models import Activity, EnvironmentalPhoto, EnvironmentalProject
from ..permissions import ENVIRONMENT, can
from . import see_other


class PhotoForm(forms.Form):
    photo = forms.FileField(label=gettext_lazy("Foto (JPEG o PNG)"))
    author = forms.CharField(label=gettext_lazy("Autor de la foto"), max_length=120)
    usage_permission = forms.BooleanField(
        label=gettext_lazy("L'autor ha donat permís perquè el club la faci servir internament"),
        error_messages={"required": gettext_lazy("Cal el permís d'ús de l'autor.")},
    )
    shows_people = forms.BooleanField(label=gettext_lazy("S'hi veuen persones"), required=False)
    people_consent = forms.BooleanField(
        label=gettext_lazy("Tinc el consentiment de les persones que hi surten"), required=False
    )


class RetirePhotoForm(forms.Form):
    reason = forms.CharField(label=gettext_lazy("Motiu de la retirada"), max_length=300)


def _environmental(pk):
    activity = get_object_or_404(Activity.objects.select_related("outing_type", "project"), pk=pk)
    if not environment.is_environmental(activity):
        raise Http404
    return activity


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
    if environment_photos.enabled():
        context["photos"] = environment_photos.photos_for(activity)
        writer = can(request.user, ENVIRONMENT)
        context["photo_form"] = PhotoForm() if writer and result is not None else None
        context["retire_form"] = RetirePhotoForm() if writer else None
    return render(request, "activities/environment_results.html", context)


@never_cache
@permission_required(ENVIRONMENT)
@require_GET
def project_view(request, pk):
    project = get_object_or_404(EnvironmentalProject.objects.select_related("department"), pk=pk)
    context = {"project": project, "summary": environment.project_summary(project)}
    return render(request, "activities/project_detail.html", context)


@never_cache
@permission_required(ENVIRONMENT, write=True)
@require_POST
def photo_upload_view(request, pk):
    activity = _environmental(pk)
    form = PhotoForm(request.POST, request.FILES)
    if form.is_valid():
        data = form.cleaned_data
        try:
            environment_photos.upload(
                activity, data["photo"], by=request.user, author=data["author"],
                usage_permission=data["usage_permission"], shows_people=data["shows_people"],
                people_consent=data["people_consent"], request=request,
            )  # fmt: skip
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
        else:
            messages.success(request, _("Foto desada."))
    else:
        messages.error(request, " ".join(e for errors in form.errors.values() for e in errors))
    return see_other("administration:activity_environment", activity.pk)


@never_cache
@permission_required(ENVIRONMENT, write=True)
@require_POST
def photo_retire_view(request, pk, photo_id):
    activity = _environmental(pk)
    photo = get_object_or_404(EnvironmentalPhoto, pk=photo_id, result__activity=activity)
    form = RetirePhotoForm(request.POST)
    try:
        if not form.is_valid():
            raise ValidationError(_("Cal el motiu de la retirada."))
        environment_photos.retire(
            photo, by=request.user, reason=form.cleaned_data["reason"], request=request
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, _("Foto retirada."))
    return see_other("administration:activity_environment", activity.pk)
