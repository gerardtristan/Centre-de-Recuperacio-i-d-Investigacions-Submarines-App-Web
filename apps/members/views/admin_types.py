"""Administració: tipus de soci (T-M01-52; 091, RN-M01-107). Seguretat: veure-la demana
`settings.section.members` (sense permís, «no trobat»); els formularis només surten a qui pot
editar, però el control és el servei (`apps.members.types`), que torna «no trobat» i deixa
l'intent al registre."""

from decimal import Decimal

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.members import settings as member_settings
from apps.members import types
from apps.members.models import Member, MembershipType
from apps.members.views.personal import euros


class TypeForm(forms.Form):
    name = forms.CharField(label=gettext_lazy("Nom"), max_length=60)
    full_rights = forms.BooleanField(
        label=gettext_lazy("De ple dret"),
        required=False,
        help_text=gettext_lazy(
            "Pot passar a simpatitzant en renovar i rep l'avís de renovació; s'hi arriba amb el "
            "canvi a ple dret i el seu suplement. Demana 14 anys com a mínim."
        ),
    )
    min_age = forms.IntegerField(
        label=gettext_lazy("Edat mínima"),
        min_value=0,
        max_value=120,
        initial=0,
        help_text=gettext_lazy("Anys complerts el dia de la sol·licitud."),
    )


class NewTypeForm(TypeForm):
    code = forms.CharField(
        label=gettext_lazy("Codi"),
        max_length=20,
        validators=[RegexValidator(r"^[a-z][a-z0-9-]*$")],
        help_text=gettext_lazy(
            "Minúscules, xifres i guions, començant per una lletra. No es pot canviar."
        ),
    )
    price = forms.DecimalField(
        label=gettext_lazy("Quota anual"),
        min_value=Decimal("0.01"),
        decimal_places=2,
        localize=True,
        help_text=gettext_lazy("En euros. Després es canvia als ajustos, amb data i nota."),
    )
    field_order = ["name", "code", "price", "full_rights", "min_age"]


class EditTypeForm(TypeForm):
    active = forms.BooleanField(
        label=gettext_lazy("Actiu"),
        required=False,
        help_text=gettext_lazy("Un tipus inactiu no surt a l'alta ni als canvis de tipus."),
    )


def _view_or_404(request):
    if not types.can_view(request.user):
        raise Http404
    if request.method == "POST":  # abans de validar res; el servei ho torna a comprovar
        types.check_can_edit(request.user, request)


def _save(form, action):
    """Crida el servei; un error de validació queda al formulari i no es desa res."""
    try:
        return action(**form.cleaned_data)
    except ValidationError as exc:
        for field, errors in exc.update_error_dict({}).items():
            form.add_error(field if field in form.fields else None, errors)
    return None


@never_cache
@require_http_methods(["GET", "POST"])
def types_view(request):
    _view_or_404(request)
    form = NewTypeForm(request.POST or None)
    if form.is_bound and form.is_valid():
        price = int(form.cleaned_data.pop("price") * 100)
        created = _save(
            form,
            lambda **data: types.create(
                **data, annual_fee_cents=price, by=request.user, request=request
            ),
        )
        if created:
            messages.success(request, _("Tipus creat amb el seu preu."))
            return redirect("administration:membership_types")
    current = Count("members", filter=~Q(members__status=Member.Status.LEFT))
    rows = [
        (t, euros(member_settings.annual_fee_cents(t)), member_settings.price_key(t))
        for t in MembershipType.objects.annotate(n_members=current).order_by("-active", "pk")
    ]
    context = {"rows": rows, "form": form, "editable": types.can_edit(request.user)}
    return render(request, "members/membership_types.html", context)


@never_cache
@require_http_methods(["GET", "POST"])
def type_edit_view(request, pk):
    _view_or_404(request)
    membership_type = get_object_or_404(MembershipType, pk=pk)
    initial = {f: getattr(membership_type, f) for f in ("name", "full_rights", "min_age", "active")}
    form = EditTypeForm(request.POST or None, initial=initial)
    in_use = types.has_members(membership_type)
    for name in ("full_rights", "min_age", "active") if in_use else ():
        form.fields[name].disabled = True  # P-374 i P-375; el servei ho torna a comprovar
    if form.is_bound and form.is_valid():
        saved = _save(
            form,
            lambda **data: types.update(membership_type, **data, by=request.user, request=request),
        )
        if saved:
            messages.success(request, _("Tipus desat. El canvi queda al registre."))
            return redirect("administration:membership_types")
    context = {
        "type": membership_type,
        "form": form,
        "editable": types.can_edit(request.user),
        "has_members": in_use,
    }
    return render(request, "members/membership_type_edit.html", context)
