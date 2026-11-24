"""Pantalla de l'estructura de la tresoreria (T-M04-22; P-410 i P-411): departaments (M7),
centres de cost (T3) i comptes (T2). Cada secció surt només amb el seu permís; el servei el
torna a comprovar. Les entrades del sistema no tenen cap acció i el servidor les protegeix.
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core import charges
from apps.core.models import Department
from apps.core.permissions import has_perm

from . import structure
from .models import CostCentre, TreasuryAccount

DEPARTMENTS = "core.departments.manage"  # M7
PAGE = "administration:treasury_structure"


class NameForm(forms.Form):
    name = forms.CharField(label=_("Nom"), max_length=80)


class CostCentreForm(NameForm):
    department = forms.ModelChoiceField(
        label=_("Departament"), queryset=Department.objects.filter(active=True).order_by("name")
    )


class AccountForm(NameForm):
    kind = forms.ChoiceField(
        label=_("Tipus"),
        choices=[(k.value, k.label) for k in structure.MANUAL_KINDS],
    )
    last4 = forms.CharField(
        label=_("Quatre darrers dígits"), required=False, max_length=4,
        help_text=_("Només per a un compte de banc. Mai l'IBAN sencer."),
    )  # fmt: skip


def _department_system(department):
    return department.name == Department.GENERAL


# Tipus d'entrada: (model, permís, formulari de creació, crear, reanomenar, desactivar, sistema).
KINDS = {
    "departament": (
        Department, DEPARTMENTS, NameForm,
        lambda d, by: charges.create_department(d["name"], by=by),
        charges.rename_department, charges.deactivate_department, _department_system,
    ),
    "centre": (
        CostCentre, structure.COST_CENTRES, CostCentreForm,
        lambda d, by: structure.create_cost_centre(d["department"], d["name"], by=by),
        structure.rename_cost_centre, structure.deactivate_cost_centre, structure.is_system,
    ),
    "compte": (
        TreasuryAccount, structure.ACCOUNTS, AccountForm,
        lambda d, by: structure.create_account(d["name"], d["kind"], last4=d["last4"], by=by),
        structure.rename_account, structure.deactivate_account, lambda _account: False,
    ),
}  # fmt: skip


def _kind(request, kind):
    if kind not in KINDS or not has_perm(request.user, KINDS[kind][1], write=True):
        raise Http404
    return KINDS[kind]


def _can(request):
    return {kind: has_perm(request.user, spec[1], write=True) for kind, spec in KINDS.items()}


@never_cache
@require_GET
def structure_view(request, forms_by_kind=None):
    can = _can(request)
    if not any(can.values()):
        raise Http404
    departments = Department.objects.order_by("name").prefetch_related("cost_centres")
    context = {
        "can": can,
        "departments": [
            {
                "department": d,
                "system": _department_system(d),
                "centres": [(c, structure.is_system(c)) for c in d.cost_centres.order_by("name")],
            }
            for d in departments
        ],
        "accounts": TreasuryAccount.objects.order_by("name") if can["compte"] else [],
        "forms": {
            kind: (forms_by_kind or {}).get(kind) or KINDS[kind][2](prefix=kind)
            for kind in KINDS
            if can[kind]
        },
    }
    return render(request, "treasury/structure.html", context)


@never_cache
@require_http_methods(["POST"])
def create_view(request, kind):
    spec = _kind(request, kind)
    form = spec[2](request.POST, prefix=kind)
    if form.is_valid():
        try:
            spec[3](form.cleaned_data, request.user)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, _("Desat. El canvi queda al registre."))
            return redirect(PAGE)
    request.method = "GET"  # la pàgina amb el formulari i els errors
    return structure_view(request, forms_by_kind={kind: form})


@never_cache
@require_http_methods(["GET", "POST"])
def edit_view(request, kind, pk):
    model, _perm, _form, _create, rename, deactivate, system = _kind(request, kind)
    obj = get_object_or_404(model, pk=pk)
    if system(obj):
        raise Http404  # P-411: cap acció sobre una entrada del sistema
    form = NameForm(request.POST or None, initial={"name": obj.name})
    if request.method == "POST":
        try:
            if "desactiva" in request.POST:
                deactivate(obj, by=request.user)
            elif form.is_valid():
                rename(obj, form.cleaned_data["name"], by=request.user)
            else:
                raise ValidationError(_("Cal un nom."))
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, _("Desat. El canvi queda al registre."))
            return redirect(PAGE)
    return render(request, "treasury/structure_edit.html", {"obj": obj, "form": form})
