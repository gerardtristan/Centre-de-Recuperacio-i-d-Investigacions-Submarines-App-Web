"""Catàlegs de cursos i d'especialitats a l'administració (T-M02-05b; P-M02-A; RN-M02-01 i 05;
CA-M02-01 i 26; AC6).

- **Permís:** AC6 (`activities.catalogue.manage`) per veure-ho i editar-ho; sense, «no trobat».
  Els serveis de `catalogue` el tornen a comprovar.
- Un preu nou és una versió amb data d'entrada en vigor (avui o després) i motiu; no canvia cap
  activitat ja creada i el servei avisa el tresorer i la junta (RN-AJ-04).
- Una fitxa no s'esborra: es desactiva i deixa de sortir en crear activitats.
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core.charges import euros
from apps.core.permissions import permission_required

from .. import catalogue
from ..forms import CataloguePriceForm, EntryForm, OutingTypeForm, ProjectForm, SubtypeForm
from ..models import (
    EnvironmentalProject,
    EnvironmentalSubtype,
    OutingType,
    RequirementsMode,
    TrainingCatalogueEntry,
)
from ..permissions import CATALOGUE, FIRST_LICENCE_VIEW, can
from . import see_other


def _prices(row) -> dict:
    reinforcement = row.reinforcement_price_cents
    return {
        "includes_first_licence": getattr(row, "includes_first_licence", False),
        "member": euros(row.price_member_cents),
        "non_member": euros(row.price_non_member_cents),
        "reinforcement": None if reinforcement is None else euros(reinforcement),
    }


def _attempt(request, form, action, success) -> bool:
    """Desa amb el servei; una regla que no es compleix surt al formulari, sense desar res."""
    if not form.is_valid():
        return False
    try:
        action(form.cleaned_data)
    except ValidationError as error:
        form.add_error(None, error)
        return False
    messages.success(request, success)
    return True


@never_cache
@permission_required(CATALOGUE, write=True)
@require_http_methods(["GET", "POST"])
def catalogue_view(request):
    """Les fitxes i, a la mateixa pàgina, els tipus de sortida, els subtipus de medi ambient i els
    projectes (T-M02-05c): crear-ne, activar o desactivar tipus i subtipus i canviar el mode de
    requisits d'un tipus (RN-M02-29; les sortides ja creades no canvien)."""
    post = request.POST if request.method == "POST" else None
    forms_ = {
        "tipus": OutingTypeForm(post if post and "nou_tipus" in post else None),
        "subtipus": SubtypeForm(post if post and "nou_subtipus" in post else None),
        "projecte": ProjectForm(post if post and "nou_projecte" in post else None),
    }
    if post is not None and _post_classification(request, post, forms_):
        return see_other("administration:catalogue")
    today = timezone.localdate()
    # shortcut: una consulta de preu per fitxa; si n'hi ha centenars, anotar-ho a la consulta
    rows = [
        {"entry": entry, **_prices(catalogue.price_on(entry, today))}
        for entry in TrainingCatalogueEntry.objects.order_by("kind", "-active", "name")
    ]
    context = {
        "rows": rows,
        "types": OutingType.objects.select_related("default_department").order_by("name"),
        "subtypes": EnvironmentalSubtype.objects.order_by("name"),
        "projects": EnvironmentalProject.objects.select_related("department").order_by("name"),
        "modes": RequirementsMode.choices,
        "forms": forms_,
    }
    return render(request, "activities/catalogue.html", context)


def _post_classification(request, post, forms_) -> bool:
    """Una acció sobre els tipus, els subtipus o els projectes. Torna si s'ha desat."""
    who = {"by": request.user, "request": request}
    if "actiu" in post:
        model = OutingType if post.get("classe") == "tipus" else EnvironmentalSubtype
        obj = get_object_or_404(model, pk=post.get("id"))
        catalogue.set_active(obj, post["actiu"] == "1", **who)
        messages.success(request, _("Desat. Les sortides ja creades no canvien."))
        return True
    if "mode" in post:
        outing_type = get_object_or_404(OutingType, pk=post.get("id"))
        try:
            catalogue.set_outing_type_mode(outing_type, post["mode"], **who)
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
        else:
            messages.success(request, _("Mode desat per a les sortides noves d'aquest tipus."))
        return True
    actions = {
        "tipus": lambda data: catalogue.create_outing_type(**who, **data),
        "subtipus": lambda data: catalogue.create_subtype(**who, **data),
        "projecte": lambda data: catalogue.create_project(**who, **data),
    }
    key = next((key for key in actions if f"nou_{key}" in post), None)
    return key is not None and _attempt(request, forms_[key], actions[key], _("Creat."))


@never_cache
@permission_required(CATALOGUE, write=True)
@require_http_methods(["GET", "POST"])
def entry_add_view(request):
    form = EntryForm(request.POST or None)
    created = []

    def create(data):
        created.append(catalogue.create_entry(by=request.user, request=request, **data))

    if request.method == "POST" and _attempt(request, form, create, _("Fitxa creada.")):
        return see_other("administration:catalogue_entry", created[0].pk)
    return render(request, "activities/catalogue_entry_add.html", {"form": form})


@never_cache
@permission_required(CATALOGUE, write=True)
@require_http_methods(["GET", "POST"])
def entry_detail_view(request, pk):
    entry = get_object_or_404(TrainingCatalogueEntry, pk=pk)
    post = request.POST if request.method == "POST" else None
    entry_form = EntryForm(post if post and "desa_fitxa" in post else None, entry=entry)
    price_form = CataloguePriceForm(
        post if post and "nou_preu" in post else None, entry=entry, user=request.user
    )
    if post is not None:
        if "activa" in post:
            active = post["activa"] == "1"
            catalogue.set_active(entry, active, by=request.user, request=request)
            messages.success(request, _("Fitxa activada.") if active else _("Fitxa desactivada."))
            return see_other("administration:catalogue_entry", entry.pk)
        who = {"by": request.user, "request": request}
        if "desa_fitxa" in post:
            saved = _attempt(
                request, entry_form,
                lambda data: catalogue.update_entry(entry, **who, **data),
                _("Canvis desats. Queden al registre amb el valor anterior."),
            )  # fmt: skip
        else:
            saved = _attempt(
                request, price_form,
                lambda data: catalogue.change_prices(entry, **who, **data),
                _("Preus desats. S'ha avisat el tresorer i la junta."),
            )  # fmt: skip
        if saved:
            return see_other("administration:catalogue_entry", entry.pk)
    today = timezone.localdate()
    context = {
        "entry": entry,
        "current": _prices(catalogue.price_on(entry, today)),
        "history": [
            {"row": row, **_prices(row)} for row in entry.prices.order_by("-valid_from", "-pk")
        ],
        "entry_form": entry_form,
        "first_licence": can(request.user, FIRST_LICENCE_VIEW),  # AC27 (RN-M02-57)
        "price_form": price_form,
        "today": today,
    }
    return render(request, "activities/catalogue_entry.html", context)
