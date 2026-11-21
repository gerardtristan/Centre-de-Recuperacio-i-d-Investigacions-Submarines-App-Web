"""Pantalla del marge d'una activitat (P-M09-D; RN-M09-01 a 07 i 12; MG5, MG6 i MG7). Sense permís o
fora de l'abast («les seves activitats»), «no trobat»: ho comproven el decorador i els serveis.

- Marge **previst** (activitat no tancada) i, si ja és feta, el **real** que es congelaria.
- Marge **congelat** (activitat tancada) amb els **ajustos posteriors** al costat (RN-M09-07).
- Costos previstos per categoria (MG5) i tancament econòmic amb els motius que l'impedeixen (MG7).
"""

from decimal import Decimal

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from apps.activities.models import Activity
from apps.core.charges import euros
from apps.core.permissions import has_perm, request_permissions, require_perm
from apps.expenses.models import ExpenseCategory

from . import calc, closing, planned, services

VIEW = "expenses.margin.view"  # MG6
PAGE = "administration:activity_margin"


class PlannedCostForm(forms.Form):
    category = forms.ModelChoiceField(
        label=gettext_lazy("Categoria"), queryset=ExpenseCategory.objects.filter(active=True)
    )
    amount = forms.DecimalField(
        label=gettext_lazy("Import previst (€)"), min_value=Decimal("0"), max_digits=11,
        decimal_places=2, localize=True,
    )  # fmt: skip


def _lines(margin) -> dict:
    """Els imports de RN-M09-01, ja en euros, per a la plantilla."""
    pct = margin.margin_pct_tenths
    return {
        "income": euros(margin.income_enrolments_cents),
        "other_income": euros(margin.other_direct_income_cents),
        "costs": euros(margin.direct_costs_cents),
        "material": euros(margin.material_cost_cents),
        "margin": euros(margin.margin_cents),
        "negative": margin.margin_cents < 0,
        "pct": None if pct is None else f"{pct / 10:.1f}".replace(".", ","),
        "participants": margin.participants,
        "categories": [
            (name, euros(c)) for name, c in margin.breakdown["costs_by_category"].items()
        ],
        "rental": margin.breakdown["rental"]["cents"],
    }


@never_cache
@require_http_methods(["GET"])
def activity_view(request, activity_id):
    activity = get_object_or_404(Activity, pk=activity_id)
    perms = request_permissions(request)
    require_perm(request, VIEW, activity)
    snapshot = closing.current(activity)
    context = {"activity": activity, "snapshot": snapshot}
    if snapshot is not None:
        later = closing.later_adjustments(snapshot)
        context["frozen"] = {
            "margin": euros(snapshot.margin_cents),
            "negative": snapshot.margin_cents < 0,
            "closed_at": snapshot.closed_at,
            "later": euros(later.margin_effect_cents) if later.margin_effect_cents else None,
        }
    else:
        context["forecast"] = _lines(services.activity_margin(activity))
        if activity.status == Activity.Status.DONE:
            context["real"] = _lines(services.activity_margin(activity, calc.REAL))
    can_plan = activity.status != Activity.Status.CLOSED and has_perm(
        request.user, planned.PLANNED_COSTS, activity, write=True, permissions=perms
    )
    can_close = activity.status == Activity.Status.DONE and has_perm(
        request.user, closing.CLOSE, write=True, permissions=perms
    )
    context.update(
        planned=[(name, euros(c)) for name, c in planned.planned_costs(activity).items()],
        can_plan=can_plan,
        form=PlannedCostForm() if can_plan else None,
        can_close=can_close,
        blockers=closing.blockers(activity) if can_close else [],
    )
    return render(request, "margins/activity.html", context)


@never_cache
@require_POST
def planned_view(request, activity_id):
    activity = get_object_or_404(Activity, pk=activity_id)
    require_perm(request, planned.PLANNED_COSTS, activity, write=True)
    form = PlannedCostForm(request.POST)
    if form.is_valid():
        try:
            planned.set_planned_cost(
                activity, form.cleaned_data["category"],
                int(form.cleaned_data["amount"] * 100), by=request.user,
            )  # fmt: skip
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
        else:
            messages.success(request, _("Cost previst desat."))
    else:
        messages.error(request, _("Revisa la categoria i l'import."))
    return redirect(PAGE, activity_id=activity.pk)


@never_cache
@require_POST
def close_view(request, activity_id):
    activity = get_object_or_404(Activity, pk=activity_id)
    require_perm(request, closing.CLOSE, write=True)
    try:
        closing.close_activity(activity, by=request.user)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, _("Activitat tancada: el marge real queda congelat."))
    return redirect(PAGE, activity_id=activity.pk)
