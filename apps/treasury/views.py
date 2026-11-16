"""Pantalles de tresoreria (T-M04-15, primer tall; C1 i C8 de M04-3): comptes amb el saldo calculat
i llista de moviments amb filtres. Només lectura: només GET, i l'únic formulari és el dels filtres.

- Permís T1 (`treasury.view`) al servidor; sense, «no trobat» (059). Ruta d'administració, amb TOTP.
- Cap IBAN: del compte només surten el nom, el tipus i els quatre darrers dígits (RN-T03).
- Cap nom de persona: el concepte del moviment no en porta (RNF-T4).
- Un moviment anul·lat continua a la llista, marcat (CA-T06.1, RN-T25).

«A revisar» (T-M04-14, C6; CA-T12.1, CA-T13.1): les línies de l'extracte amb el motiu, i el
formulari per excloure'n una (POST, T8 al servidor). Sense el concepte de la línia, que pot
portar noms de fora del club i només es veu a la conciliació (M04-4, per objecte).
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from apps.core.charges import euros
from apps.core.imports import statement_lines
from apps.core.models import Department
from apps.core.permissions import has_perm, permission_required

from . import reconciliation
from .balances import balances
from .models import Movement, TreasuryAccount

VIEW = "treasury.view"  # T1; també T10, «Veure la llista "a revisar"» (P-190)
PER_PAGE = 50


def _date_field(label):
    return forms.DateField(
        label=label, required=False, widget=forms.DateInput(attrs={"type": "date"})
    )


class BalanceDateForm(forms.Form):
    on = _date_field(_("Saldo a"))


class MovementFilterForm(forms.Form):
    account = forms.ModelChoiceField(
        TreasuryAccount.objects.order_by("name"),
        label=_("Compte"),
        required=False,
        empty_label=_("Tots"),
    )
    department = forms.ModelChoiceField(
        Department.objects.order_by("name"),
        label=_("Departament"),
        required=False,
        empty_label=_("Tots"),
    )
    date_from = _date_field(_("Des del dia"))
    date_to = _date_field(_("Fins al dia"))

    def clean(self):
        data = super().clean()
        start, end = data.get("date_from"), data.get("date_to")
        if start and end and start > end:
            self.add_error("date_to", _("Ha de ser igual o posterior a «Des del dia»."))
        return data


def _signed(movement) -> str:
    sign = "+" if movement.direction == Movement.Direction.IN else "−"
    return f"{sign}{euros(movement.amount_cents)}"


@never_cache
@permission_required(VIEW)
@require_GET
def accounts_view(request):
    form = BalanceDateForm(request.GET or None)
    on = (form.is_valid() and form.cleaned_data["on"]) or timezone.localdate()
    rows = [{"account": a, "balance": euros(a.balance_cents)} for a in balances(on)]
    has_movements = Movement.objects.exists()
    context = {"form": form, "on": on, "rows": rows, "has_movements": has_movements}
    return render(request, "treasury/accounts.html", context)


@never_cache
@permission_required(VIEW)
@require_GET
def movements_view(request):
    form = MovementFilterForm(request.GET or None)
    data = {}
    if form.is_bound:
        form.is_valid()  # els camps vàlids filtren; els no vàlids surten com a error i no filtren
        data = form.cleaned_data
    movements = Movement.objects.with_reversal().select_related(
        "account", "department", "cost_centre"
    )
    if data.get("account"):
        movements = movements.filter(account=data["account"])
    if data.get("department"):
        movements = movements.filter(department=data["department"])
    if data.get("date_from"):
        movements = movements.filter(value_date__gte=data["date_from"])
    if data.get("date_to"):
        movements = movements.filter(value_date__lte=data["date_to"])
    page = Paginator(movements.order_by("-value_date", "-recorded_at", "-id"), PER_PAGE).get_page(
        request.GET.get("pagina")
    )
    rows = [{"movement": m, "amount": _signed(m)} for m in page]
    return render(request, "treasury/movements.html", {"form": form, "page": page, "rows": rows})


@never_cache
@permission_required(VIEW)
@require_GET
def review_view(request):
    reconciliation.refresh()  # els càrrecs canvien: la llista es calcula abans de mostrar-la
    rows = [
        {
            "state": state,
            "line": state.statement_line,
            "amount": euros(state.statement_line.amount_cents),
        }
        for state in reconciliation.to_review()
    ]
    can_exclude = has_perm(request.user, reconciliation.EXCLUDE, write=True)
    return render(request, "treasury/review.html", {"rows": rows, "can_exclude": can_exclude})


@never_cache
@permission_required(reconciliation.EXCLUDE, write=True)
@require_POST
def exclude_view(request, line_id):
    line = get_object_or_404(statement_lines(), pk=line_id)
    try:
        reconciliation.exclude(line, reason=request.POST.get("motiu", ""), by=request.user)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, _("Línia exclosa. No s'ha creat cap moviment."))
    return redirect("administration:treasury_review")
