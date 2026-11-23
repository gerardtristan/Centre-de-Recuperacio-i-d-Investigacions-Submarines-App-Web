"""Apartat «Llocs» dels ajustos del 02 (T-M02-39; RN-M02-38, 39 i 46; CA-M02-41, 42, 44 i 46).

- **Permisos:** veure la llista, els preus, l'historial i les notes demana AC21; crear, editar,
  desactivar i canviar el preu estàndard, AC22. Sense AC21, «no trobat». Amb AC21 i sense AC22,
  la pàgina surt sense cap control d'edició, i una petició d'edició és «no trobat» i queda al
  registre (CA-M02-46). Els serveis de `catalogue` ho tornen a comprovar.
- Un lloc no s'esborra mai: es desactiva (RN-M02-38). No hi ha cap ruta per esborrar-lo.
- El preu estàndard és una versió nova amb data i motiu; el servei avisa el tresorer (RN-AJ-04).
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core import audit
from apps.core.charges import euros
from apps.core.permissions import permission_required

from .. import catalogue
from ..forms import PlaceForm, PlacePriceForm
from ..models import Place
from ..permissions import PLACES_MANAGE, PLACES_VIEW, can
from . import see_other

EDIT_DENIED = "activities.place.edit_denied"  # CA-M02-46


def _can_edit(request) -> bool:
    return can(request.user, PLACES_MANAGE)


def _require_edit(request, place=None) -> None:
    """CA-M02-46: sense AC22, «no trobat»; un intent de desar (POST) queda al registre."""
    if _can_edit(request):
        return
    if request.method == "POST":
        details = {"permission": PLACES_MANAGE}
        audit.record(
            EDIT_DENIED, actor=request.user, target=place, details=details, request=request
        )
    raise Http404


def _price(price) -> dict | None:
    if price is None:
        return None
    return {
        "member": euros(price.price_member_cents),
        "non_member": euros(price.price_non_member_cents),
        "valid_from": price.valid_from,
    }


@never_cache
@permission_required(PLACES_VIEW)
@require_GET
def places_view(request):
    today = timezone.localdate()
    # shortcut: una consulta de preu per lloc; si n'hi ha centenars, anotar-ho a la consulta
    rows = [
        {"place": place, "price": _price(catalogue.place_price_on(place, today))}
        for place in Place.objects.order_by("-active", "name")
    ]
    context = {"rows": rows, "can_edit": _can_edit(request)}
    return render(request, "activities/places.html", context)


@never_cache
@permission_required(PLACES_VIEW)
@require_http_methods(["GET", "POST"])
def place_add_view(request):
    _require_edit(request)
    form = PlaceForm(request.POST or None, viewer=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                place = catalogue.create_place(
                    by=request.user, request=request,
                    name=form.cleaned_data["name"], notes=form.cleaned_data["notes"],
                )  # fmt: skip
                form.save_sections(place, request.user)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, _("Lloc creat. Ara hi pots posar el preu estàndard."))
            return see_other("administration:place_detail", place.pk)
    return render(request, "activities/place_add.html", {"form": form})


def _save_place(request, place, form) -> bool:
    if not form.is_valid():
        return False
    try:
        with transaction.atomic():
            catalogue.update_place(
                place, by=request.user, request=request,
                name=form.cleaned_data["name"], notes=form.cleaned_data["notes"],
            )  # fmt: skip
            form.save_sections(place, request.user)
    except ValidationError as error:
        form.add_error(None, error)
        return False
    messages.success(request, _("Canvis desats. Queden al registre amb el valor anterior."))
    return True


def _save_price(request, place, form) -> bool:
    if not form.is_valid():
        return False
    try:
        catalogue.change_place_price(place, by=request.user, request=request, **form.cleaned_data)
    except ValidationError as error:
        form.add_error(None, error)
        return False
    messages.success(request, _("Preu estàndard desat. S'ha avisat el tresorer."))
    return True


@never_cache
@permission_required(PLACES_VIEW)
@require_http_methods(["GET", "POST"])
def place_detail_view(request, pk):
    place = get_object_or_404(Place, pk=pk)
    post = request.POST if request.method == "POST" else None
    place_form = PlaceForm(post if post and "desa_lloc" in post else None, viewer=request.user,
                           place=place)  # fmt: skip
    price_form = PlacePriceForm(post if post and "nou_preu" in post else None)
    if post is not None:
        _require_edit(request, place)
        if "actiu" in post:
            active = post["actiu"] == "1"
            catalogue.set_active(place, active, by=request.user, request=request)
            messages.success(request, _("Lloc activat.") if active else _("Lloc desactivat."))
            return see_other("administration:place_detail", place.pk)
        saved = (
            _save_place(request, place, place_form)
            if "desa_lloc" in post
            else _save_price(request, place, price_form)
        )
        if saved:
            return see_other("administration:place_detail", place.pk)
    today = timezone.localdate()
    context = {
        "place": place,
        "price": _price(catalogue.place_price_on(place, today)),
        "history": [
            {"row": row, **_price(row)} for row in place.prices.order_by("-valid_from", "-pk")
        ],
        "can_edit": _can_edit(request),
        "place_form": place_form,
        "price_form": price_form,
        "today": today,
    }
    return render(request, "activities/place_detail.html", context)
