"""Catàlegs a l'administració (T-M02-05; P-M02-A; RN-M02-01 i RN-M02-05; CA-M02-01 i CA-M02-26).

- **Dues pantalles separades:** «Catàleg de cursos» i «Catàleg d'especialitats» (RN-M02-01).
- **Preus:** tenen la seva pantalla, amb motiu i data d'entrada en vigor, i l'historial de
  versions. Canviar-los avisa per correu el tresorer i la junta (RN-AJ-04) i no toca cap
  activitat ja creada.
- **Tipus de sortida, subtipus i projectes:** s'afegeixen i es desactiven; res no s'esborra.
- **Permís:** AC6 (`activities.catalogue.manage`). Es comprova abans que el mètode i, de nou, al
  servei: amagar un botó no és cap control. Sense permís, sempre «no trobat».
- Cap d'aquestes pantalles mostra dades personals, tret del nom de qui ha canviat un preu.
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core.charges import euros
from apps.core.permissions import permission_required

from .. import catalogue
from ..forms import (
    DEFAULT_MODES,
    CatalogueEntryForm,
    LevelForm,
    OutingTypeForm,
    PriceChangeForm,
    ProjectForm,
    SubtypeForm,
)
from ..models import (
    CertificationLevel,
    EnvironmentalProject,
    EnvironmentalSubtype,
    OutingType,
    TrainingCatalogueEntry,
)
from ..permissions import CATALOGUE
from . import run, see_other

K = TrainingCatalogueEntry.Kind
LISTS = {
    K.COURSE: "administration:catalogue_courses",
    K.SPECIALITY: "administration:catalogue_specialities",
}
TITLES = {K.COURSE: _("Catàleg de cursos"), K.SPECIALITY: _("Catàleg d'especialitats")}
ADD_TITLES = {
    K.COURSE: _("Afegeix un curs al catàleg"),
    K.SPECIALITY: _("Afegeix una especialitat al catàleg"),
}
ADD_ROUTES = {
    K.COURSE: "administration:catalogue_course_add",
    K.SPECIALITY: "administration:catalogue_speciality_add",
}


def _price_row(price):
    if price is None:
        return None
    return {
        "member": euros(price.member_cents),
        "non_member": euros(price.non_member_cents),
        "reinforcement": (
            euros(price.reinforcement_cents) if price.reinforcement_cents is not None else ""
        ),
        "valid_from": price.valid_from,
    }


def _context(kind, **extra):
    return {"kind": kind, "list_title": TITLES[kind], "list_url": LISTS[kind], **extra}


@never_cache
@permission_required(CATALOGUE)
@require_GET
def catalogue_list_view(request, kind):
    today = timezone.localdate()
    rows = [
        {
            "entry": entry,
            "price": _price_row(catalogue.price_on(entry, today)),
            "next": _price_row(catalogue.next_price(entry, today)),
        }
        for entry in catalogue.entries(kind).select_related("department")
    ]
    context = _context(kind, rows=rows, add_url=ADD_ROUTES[kind], add_title=ADD_TITLES[kind])
    return render(request, "activities/catalogue_list.html", context)


@never_cache
@permission_required(CATALOGUE, write=True)
@require_http_methods(["GET", "POST"])
def catalogue_entry_add_view(request, kind):
    form = CatalogueEntryForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        saved = run(
            request,
            form,
            lambda: catalogue.create_entry(
                by=request.user, kind=kind, request=request, **form.cleaned_data
            ),
            _("Fitxa desada. Queda al registre d'activitat."),
        )
        if saved:
            return see_other(LISTS[kind])
    context = _context(kind, form=form, title=ADD_TITLES[kind], entry=None)
    return render(request, "activities/catalogue_entry_form.html", context)


@never_cache
@permission_required(CATALOGUE, write=True)
@require_http_methods(["GET", "POST"])
def catalogue_entry_edit_view(request, pk):
    entry = get_object_or_404(TrainingCatalogueEntry, pk=pk)
    form = CatalogueEntryForm(request.POST if request.method == "POST" else None, entry=entry)
    if request.method == "POST" and form.is_valid():
        saved = run(
            request,
            form,
            lambda: catalogue.update_entry(
                entry, by=request.user, request=request, **form.cleaned_data
            ),
            lambda changed: (
                _("Fitxa desada. Queda al registre d'activitat.")
                if changed
                else _("No hi havia cap canvi per desar.")
            ),
        )
        if saved:
            return see_other(LISTS[entry.kind])
    context = _context(entry.kind, form=form, title=_("Edita la fitxa"), entry=entry)
    return render(request, "activities/catalogue_entry_form.html", context)


@never_cache
@permission_required(CATALOGUE, write=True)
@require_http_methods(["GET", "POST"])
def catalogue_entry_prices_view(request, pk):
    entry = get_object_or_404(TrainingCatalogueEntry, pk=pk)
    today = timezone.localdate()
    current = catalogue.price_on(entry, today)
    form = PriceChangeForm(
        request.POST if request.method == "POST" else None, current=current, today=today
    )
    if request.method == "POST" and form.is_valid():
        saved = run(
            request,
            form,
            lambda: catalogue.change_prices(
                entry, by=request.user, request=request, **form.cleaned_data
            ),
            _(
                "Preus desats. S'ha avisat el tresorer i la junta, i les activitats ja creades "
                "no canvien."
            ),
        )
        if saved:
            return see_other(LISTS[entry.kind])
    versions = [
        {
            "member": euros(version.price_member_cents),
            "non_member": euros(version.price_non_member_cents),
            "reinforcement": (
                euros(version.reinforcement_price_cents)
                if version.reinforcement_price_cents is not None
                else ""
            ),
            "valid_from": version.valid_from,
            "note": version.note,
            "changed_by": version.changed_by.person if version.changed_by else None,
            "upcoming": version.valid_from > today,
        }
        for version in catalogue.price_versions(entry)
    ]
    context = _context(
        entry.kind, form=form, entry=entry, current=_price_row(current), versions=versions
    )
    return render(request, "activities/catalogue_prices.html", context)


def _toggle(request, obj, back, *back_args):
    active = request.POST.get("actiu") == "1"
    changed = catalogue.set_active(obj, active, by=request.user, request=request)
    if not changed:
        messages.info(request, _("No hi havia cap canvi per desar."))
    elif active:
        messages.success(request, _("«%(name)s» torna a estar disponible.") % {"name": obj.name})
    else:
        messages.success(
            request,
            _("«%(name)s» s'ha desactivat: ja no es pot triar per a activitats noves.")
            % {"name": obj.name},
        )
    return see_other(back, *back_args)


@never_cache
@permission_required(CATALOGUE, write=True)
@require_POST
def catalogue_entry_active_view(request, pk):
    entry = get_object_or_404(TrainingCatalogueEntry, pk=pk)
    return _toggle(request, entry, LISTS[entry.kind])


# --- Tipus de sortida i subtipus ------------------------------------------------------------------


@never_cache
@permission_required(CATALOGUE)
@require_http_methods(["GET", "POST"])
def outing_types_view(request):
    posted = request.POST if request.method == "POST" else None
    which = request.POST.get("form") if posted is not None else None
    type_form = OutingTypeForm(posted if which == "tipus" else None)
    subtype_form = SubtypeForm(posted if which == "subtipus" else None)
    if which == "tipus" and type_form.is_valid():
        if run(
            request,
            type_form,
            lambda: catalogue.create_outing_type(
                by=request.user, request=request, **type_form.cleaned_data
            ),
            _("Tipus de sortida afegit."),
        ):
            return see_other("administration:outing_types")
    elif which == "subtipus" and subtype_form.is_valid():
        if run(
            request,
            subtype_form,
            lambda: catalogue.create_subtype(
                by=request.user, request=request, **subtype_form.cleaned_data
            ),
            _("Subtipus afegit."),
        ):
            return see_other("administration:outing_types")
    elif posted is not None and which not in ("tipus", "subtipus"):
        messages.error(request, _("No s'ha pogut desar: torna-ho a provar des d'aquesta pantalla."))
    context = {
        "types": OutingType.objects.select_related("default_department"),
        "subtypes": EnvironmentalSubtype.objects.all(),
        "type_form": type_form,
        "subtype_form": subtype_form,
        "modes": DEFAULT_MODES,
    }
    return render(request, "activities/outing_types.html", context)


@never_cache
@permission_required(CATALOGUE, write=True)
@require_POST
def outing_type_active_view(request, pk):
    return _toggle(request, get_object_or_404(OutingType, pk=pk), "administration:outing_types")


@never_cache
@permission_required(CATALOGUE, write=True)
@require_POST
def outing_subtype_active_view(request, pk):
    return _toggle(
        request, get_object_or_404(EnvironmentalSubtype, pk=pk), "administration:outing_types"
    )


# --- Projectes de medi ambient --------------------------------------------------------------------


@never_cache
@permission_required(CATALOGUE)
@require_http_methods(["GET", "POST"])
def projects_view(request):
    form = ProjectForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        if run(
            request,
            form,
            lambda: catalogue.create_project(by=request.user, request=request, **form.cleaned_data),
            _("Projecte creat."),
        ):
            return see_other("administration:projects")
    context = {"projects": EnvironmentalProject.objects.select_related("department"), "form": form}
    return render(request, "activities/projects.html", context)


@never_cache
@permission_required(CATALOGUE)
@require_GET
def project_detail_view(request, pk):
    project = get_object_or_404(EnvironmentalProject.objects.select_related("department"), pk=pk)
    outings = project.activities.select_related("outing_type", "subtype").order_by("-starts_on")
    context = {"project": project, "outings": outings}
    return render(request, "activities/project_detail.html", context)


@never_cache
@permission_required(CATALOGUE, write=True)
@require_POST
def outing_type_mode_view(request, pk):
    """Canvia el mode de requisits per defecte d'un tipus de sortida (RN-M02-29; CA-M02-34)."""
    outing_type = get_object_or_404(OutingType, pk=pk)
    try:
        changed = catalogue.set_outing_type_mode(
            outing_type, request.POST.get("mode", ""), by=request.user, request=request
        )
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        if changed:
            messages.success(
                request,
                _("Mode per defecte de «%(name)s» desat. Les sortides ja creades no canvien.")
                % {"name": outing_type.name},
            )
        else:
            messages.info(request, _("No hi havia cap canvi per desar."))
    return see_other("administration:outing_types")


# --- Nivells de titulació (addenda de la 058) -----------------------------------------------------


@never_cache
@permission_required(CATALOGUE)
@require_http_methods(["GET", "POST"])
def certification_levels_view(request):
    form = LevelForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        if run(
            request,
            form,
            lambda: catalogue.create_level(by=request.user, request=request, **form.cleaned_data),
            _("Nivell afegit."),
        ):
            return see_other("administration:certification_levels")
    context = {"levels": catalogue.levels(), "form": form}
    return render(request, "activities/certification_levels.html", context)


@never_cache
@permission_required(CATALOGUE, write=True)
@require_POST
def certification_level_active_view(request, pk):
    level = get_object_or_404(CertificationLevel, pk=pk)
    return _toggle(request, level, "administration:certification_levels")
