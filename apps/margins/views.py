"""Pantalla del marge d'una activitat (P-M09-D; RN-M09-01 a 07 i 12; MG5, MG6 i MG7). Sense permís o
fora de l'abast («les seves activitats»), «no trobat»: ho comproven el decorador i els serveis.

- Marge **previst** (activitat no tancada) i, si ja és feta, el **real** que es congelaria.
- Marge **congelat** (activitat tancada) amb els **ajustos posteriors** al costat (RN-M09-07).
- Costos previstos per categoria (MG5) i tancament econòmic amb els motius que l'impedeixen (MG7).

I la pantalla dels períodes (P-M09-G; T-M09-16): la llista, la llista de control del primer
període obert amb un motiu per element (RN-M09-26), tancar-lo (MG11), crear el següent (RN-M09-28)
i reobrir el darrer tancat amb motiu (MG12).
"""

from decimal import Decimal

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.activities.models import Activity
from apps.core.charges import euros
from apps.core.permissions import has_perm, request_permissions, require_perm
from apps.expenses.models import ExpenseCategory

from . import calc, closing, period_closing, planned, services
from .models import Period

VIEW = "expenses.margin.view"  # MG6
PAGE = "administration:activity_margin"
PERIODS = "administration:margin_periods"
MISSING_REASON = gettext_lazy("Resol-lo o escriu el motiu per portar-lo al període següent.")


class PlannedCostForm(forms.Form):
    category = forms.ModelChoiceField(
        label=gettext_lazy("Categoria"),
        queryset=ExpenseCategory.objects.filter(active=True),
        empty_label=gettext_lazy("Tria una categoria"),
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


# --- Períodes (P-M09-G; T-M09-16) --------------------------------------------------------------


class FirstPeriodForm(forms.Form):
    starts_on = forms.DateField(
        label=gettext_lazy("Comença el"),
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )


class ClosePeriodForm(forms.Form):
    """Un motiu per element de la llista de control (RN-M09-26): el camp porta la clau estable de
    l'element, no la posició, perquè un element nou no hereti el motiu d'un altre."""

    def __init__(self, items, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = items
        for item in items:
            self.fields[f"motiu-{item['key']}"] = forms.CharField(
                label=item["label"], required=False, max_length=500,
                help_text=gettext_lazy("Motiu per portar-lo al període següent."),
            )  # fmt: skip

    def exceptions(self) -> dict:
        data = self.cleaned_data
        return {
            i["key"]: data[f"motiu-{i['key']}"] for i in self.items if data[f"motiu-{i['key']}"]
        }


class ReopenPeriodForm(forms.Form):
    reason = forms.CharField(
        label=gettext_lazy("Motiu de la reobertura"), max_length=500,
        widget=forms.Textarea(attrs={"rows": 2}),
    )  # fmt: skip


@never_cache
@require_GET
def periods_view(request):
    require_perm(request, period_closing.CLOSE)
    return _periods_page(request)


def _periods_page(request, closing=None):
    """`closing`: (període, formulari amb errors) quan un tancament no ha anat bé: el formulari
    torna amb l'error a sota de cada camp i el resum d'Errata (design-system §6.10)."""
    perms = request_permissions(request)
    periods = list(Period.objects.order_by("-starts_on"))
    to_close = next((p for p in reversed(periods) if p.status == Period.Status.OPEN), None)
    last_closed = next((p for p in periods if p.status == Period.Status.CLOSED), None)
    can_close = has_perm(request.user, period_closing.CLOSE, write=True, permissions=perms)
    can_reopen = has_perm(request.user, period_closing.REOPEN, write=True, permissions=perms)
    can_create = can_close and (not periods or periods[0].starts_on <= timezone.localdate())
    items = period_closing.checklist(to_close) if to_close else []
    context = {
        "periods": periods,
        "to_close": to_close,
        "items": items,
        "close_form": ClosePeriodForm(items) if can_close and to_close else None,
        "next": period_closing.next_dates() if can_create else None,
        "first_form": FirstPeriodForm() if can_create and not periods else None,
        "can_create": can_create,
        "last_closed": last_closed if can_reopen else None,
        "reopen_form": ReopenPeriodForm() if can_reopen and last_closed else None,
    }
    if closing is not None:
        period, form = closing
        if to_close is not None and period.pk == to_close.pk:
            context["close_form"] = form
        else:  # un altre període (p. ex. ja tancat per una altra persona): el missatge a dalt
            messages.error(request, " ".join(e for errors in form.errors.values() for e in errors))
    return render(request, "margins/periods.html", context)


def _error(request, error: ValidationError) -> None:
    messages.error(request, " ".join(error.messages))


@never_cache
@require_POST
def period_create_view(request):
    require_perm(request, period_closing.CLOSE, write=True)
    form = FirstPeriodForm(request.POST)
    starts_on = form.cleaned_data["starts_on"] if form.is_valid() else None
    try:
        period = period_closing.create_next(by=request.user, starts_on=starts_on)
    except ValidationError as error:
        _error(request, error)
    else:
        messages.success(
            request,
            _("Període creat: del %(start)s al %(end)s.")
            % {"start": f"{period.starts_on:%d/%m/%Y}", "end": f"{period.ends_on:%d/%m/%Y}"},
        )
    return redirect(PERIODS)


@never_cache
@require_POST
def period_close_view(request, period_id):
    period = get_object_or_404(Period, pk=period_id)
    require_perm(request, period_closing.CLOSE, write=True)
    form = ClosePeriodForm(period_closing.checklist(period), request.POST)
    if form.is_valid():
        try:
            period_closing.close(period, by=request.user, exceptions=form.exceptions())
        except period_closing.PeriodNotReady as error:
            for item in error.items:  # l'error, a sota del camp de l'element (sense repetir-lo)
                form.add_error(f"motiu-{item['key']}", MISSING_REASON)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, _("Període tancat."))
            return redirect(PERIODS)
    return _periods_page(request, closing=(period, form))


@never_cache
@require_POST
def period_reopen_view(request, period_id):
    period = get_object_or_404(Period, pk=period_id)
    require_perm(request, period_closing.REOPEN, write=True)
    form = ReopenPeriodForm(request.POST)
    try:
        if not form.is_valid():
            raise ValidationError(_("Cal el motiu de la reobertura."))
        period_closing.reopen(period, by=request.user, reason=form.cleaned_data["reason"])
    except ValidationError as error:
        _error(request, error)
    else:
        messages.success(request, _("Període reobert."))
    return redirect(PERIODS)
