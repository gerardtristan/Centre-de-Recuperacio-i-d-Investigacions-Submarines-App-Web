"""Pantalles d'administració del 03 (T-M03-19 i T-M03-22). Els serveis tornen a comprovar els
permisos; sense permís, «no trobat».

- Informes de material: material més usat (MT4), revisions properes (MT11) i les activitats amb
  material per veure'n el cost (MT12, per objecte). CSV i impressió del navegador.
- Cost de material d'una activitat (MT12): per número d'inscripció, sense noms (RN-M03-09).
- Cost d'ús per tipus (VC-28): el veu qui veu l'apartat «Material» dels ajustos i el canvia qui té
  `settings.edit.equipment.usage_rates`, amb data d'entrada en vigor, nota i avís.
"""

import datetime
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.activities.models import Activity
from apps.core.charges import euros
from apps.core.permissions import has_perm, request_permissions
from apps.members.roster import to_csv

from . import reports, usage_rates
from .models import EquipmentAssignment, EquipmentType

DATE = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class PeriodForm(forms.Form):
    des_de = forms.DateField(label=gettext_lazy("Des del"), widget=DATE)
    fins_a = forms.DateField(label=gettext_lazy("Fins al"), widget=DATE)

    def clean(self):
        data = super().clean()
        if data.get("des_de") and data.get("fins_a") and data["des_de"] > data["fins_a"]:
            raise ValidationError(_("La data d'inici no pot ser posterior a la de final."))
        return data


class UsageRateForm(forms.Form):
    tipus = forms.ModelChoiceField(
        label=gettext_lazy("Tipus de material"),
        queryset=EquipmentType.objects.filter(active=True).order_by("name"),
        empty_label=gettext_lazy("Tria…"),
    )
    cost = forms.DecimalField(
        label=gettext_lazy("Cost per dia (€)"), min_value=Decimal("0"), max_digits=7,
        decimal_places=2, localize=True,
    )  # fmt: skip
    des_de = forms.DateField(label=gettext_lazy("Vigent des del"), widget=DATE)
    nota = forms.CharField(label=gettext_lazy("Nota"), widget=forms.Textarea(attrs={"rows": 2}))


def _csv(name, headers, rows) -> HttpResponse:
    response = HttpResponse(to_csv(headers, rows), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{name}"'
    return response


@never_cache
@require_GET
def reports_view(request):
    perms = request_permissions(request)
    user = request.user
    can = {
        key: has_perm(user, code, permissions=perms)
        for key, code in (("used", reports.STOCK), ("reviews", reports.REVIEWS),
                          ("costs", reports.COSTS))
    }  # fmt: skip
    if not any(can.values()):
        raise Http404
    today = timezone.localdate()
    start, end = today - datetime.timedelta(days=365), today
    form = PeriodForm(request.GET or None, initial={"des_de": start, "fins_a": end})
    if form.is_bound and form.is_valid():
        start, end = form.cleaned_data["des_de"], form.cleaned_data["fins_a"]
    context = {"can": can, "form": form, "start": start, "end": end, "today": today}
    if can["used"]:
        used = [
            {**row, "origin": EquipmentAssignment.Origin(row["origin"]).label}
            for row in reports.most_used(start, end, viewer=user)
        ]
        if request.GET.get("format") == "csv":
            return _csv(
                f"material-mes-usat-{start:%Y%m%d}-{end:%Y%m%d}.csv",
                [_("Material"), _("D'on surt"), _("Vegades")],
                [[r["type"], r["origin"], r["uses"]] for r in used],
            )
        context["used"] = used
    if can["reviews"]:
        context["reviews"] = reports.upcoming_reviews(today, viewer=user).select_related("type")
    if can["costs"]:
        with_material = EquipmentAssignment.objects.values("activity_id")
        # shortcut: les 50 activitats amb material més recents; si en calen més, paginar
        recent = Activity.objects.filter(pk__in=with_material).order_by("-starts_on", "-pk")[:50]
        context["activities"] = [
            a for a in recent if has_perm(user, reports.COSTS, a, permissions=perms)
        ]
    return render(request, "equipment/reports.html", context)


@never_cache
@require_GET
def activity_cost_view(request, activity_id):
    activity = get_object_or_404(Activity, pk=activity_id)
    cost = reports.activity_costs(activity, viewer=request.user)  # MT12 per objecte
    rows = sorted(cost.per_participant.items())
    if request.GET.get("format") == "csv":
        return _csv(
            f"cost-material-activitat-{activity.pk}.csv",
            [_("Inscripció"), _("Cost de material (€)")],
            [[pk, euros(cents)] for pk, cents in rows],
        )
    context = {
        "activity": activity,
        "rows": [(pk, euros(cents)) for pk, cents in rows],
        "club": euros(cost.club_use_cents),
        "rental_cost": euros(cost.rental_cost_estimated_cents),
        "rental_price": euros(cost.rental_participant_cents),
        "rental_margin": euros(cost.rental_margin_cents),
        "negative_margin": cost.rental_margin_cents < 0,
    }
    return render(request, "equipment/activity_cost.html", context)


@never_cache
@require_http_methods(["GET", "POST"])
def usage_rates_view(request):
    rows = usage_rates.rates(viewer=request.user)  # «no trobat» sense l'apartat
    can_edit = has_perm(
        request.user, usage_rates.EDIT, write=True, permissions=request_permissions(request)
    )
    form = UsageRateForm(
        request.POST or None, initial={"des_de": timezone.localdate()} if can_edit else None
    )
    if request.method == "POST":
        if not can_edit:
            raise Http404
        if form.is_valid():
            data = form.cleaned_data
            try:
                usage_rates.set_rate(
                    data["tipus"], cost_per_day_cents=int(data["cost"] * 100),
                    valid_from=data["des_de"], note=data["nota"], by=request.user,
                )  # fmt: skip
            except ValidationError as error:
                form.add_error(None, error.messages)
            else:
                messages.success(request, _("Cost d'ús desat. S'ha avisat el tresorer i la junta."))
                return redirect("administration:equipment_usage_rates")
    context = {
        "rows": [
            {
                **r,
                "amount": euros(r["cents"]),
                "next": r["upcoming"] and euros(r["upcoming"].cost_per_day_cents),
            }
            for r in rows
        ],  # fmt: skip
        "can_edit": can_edit,
        "form": form,
    }
    return render(request, "equipment/usage_rates.html", context)
