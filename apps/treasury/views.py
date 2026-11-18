"""Pantalles de tresoreria (T-M04-15, primer tall; C1 i C8 de M04-3): comptes amb el saldo calculat
i llista de moviments amb filtres. Només lectura: només GET, i l'únic formulari és el dels filtres.

- Permís T1 (`treasury.view`) al servidor; sense, «no trobat» (059). Ruta d'administració, amb TOTP.
- Cap IBAN: del compte només surten el nom, el tipus i els quatre darrers dígits (RN-T03).
- Cap nom de persona: el concepte del moviment no en porta (RNF-T4).
- Un moviment anul·lat continua a la llista, marcat (CA-T06.1, RN-T25).

«A revisar» (T-M04-14, C6; CA-T12.1, CA-T13.1): les línies de l'extracte amb el motiu, i el
formulari per excloure'n una (POST, T8 al servidor). Sense el concepte de la línia, que pot
portar noms de fora del club i només es veu a la conciliació (M04-4, per objecte).

Conciliació (T-M04-15, segon tall; C5 i C6; P-M04-E, passos 3 i 5): les línies dels extractes
vigents amb l'estat, el concepte (tapat per la importació) i els càrrecs proposats o casats.
«Confirma» (`reconciliation.confirm`) i «Desfés» amb motiu (`reconciliation.undo`) són POST amb
T4 al servidor; veure-la és T1. Del càrrec, el nom de la persona, el concepte i l'import (M04-4).
«Casa a mà» (T-M04-12e, `reconciliation.match`): T4 per veure-la i fer-la; cerca de càrrecs
pendents per referència o número de soci, revisió amb la suma i confirmació, tot per POST.
Una línia proposada amb una liquidació del proveïdor (T-M04-13b; P-M04-F, passos 3 i 4) es
confirma en dos passos: el GET mostra el brut, les comissions (amb el repartiment de cada
cobrament, VT-05) i el net, i el POST crida `settlements.confirm_line`; tot amb T4.

Exportació CSV (T-M04-16, C8; CA-T15.1): els moviments amb els mateixos filtres que la llista,
per POST i amb T9 al servidor; cada exportació queda al registre amb els filtres i les files.
"""

from urllib.parse import urlencode

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core import audit
from apps.core.charges import euros
from apps.core.imports import statement_lines
from apps.core.models import Department
from apps.core.permissions import has_perm, permission_required

from . import entry_views, exports, reconciliation, services, settlements
from .balances import balances
from .models import (
    CostCentre,
    Movement,
    ProviderSettlement,
    Reconciliation,
    StatementLineState,
    TreasuryAccount,
)

VIEW = "treasury.view"  # T1; també T10, «Veure la llista "a revisar"» (P-190)
EXPORT = "treasury.export"  # T9, «Exportar moviments en CSV» (M04-4)
EXPORTED = "treasury.movements_exported"
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
    cost_centre = forms.ModelChoiceField(
        CostCentre.objects.select_related("department").order_by("department__name", "name"),
        label=_("Centre de cost"),
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
    context = {
        "form": form,
        "on": on,
        "rows": rows,
        "has_movements": has_movements,
        "can_transfer": has_perm(request.user, services.TRANSFER, write=True),
        "can_count": has_perm(request.user, services.CASH_COUNT, write=True),
    }
    return render(request, "treasury/accounts.html", context)


def _filtered(form):
    """Els moviments dels filtres vàlids: els no vàlids surten com a error i no filtren."""
    data = {}
    if form.is_bound:
        form.is_valid()
        data = form.cleaned_data
    movements = Movement.objects.all()
    for field in ("account", "department", "cost_centre"):
        if data.get(field):
            movements = movements.filter(**{field: data[field]})
    if data.get("date_from"):
        movements = movements.filter(value_date__gte=data["date_from"])
    if data.get("date_to"):
        movements = movements.filter(value_date__lte=data["date_to"])
    return movements, data


@never_cache
@permission_required(VIEW)
@require_GET
def movements_view(request):
    form = MovementFilterForm(request.GET or None)
    movements, _data = _filtered(form)
    movements = movements.with_reversal().select_related("account", "department", "cost_centre")
    page = Paginator(movements.order_by("-value_date", "-recorded_at", "-id"), PER_PAGE).get_page(
        request.GET.get("pagina")
    )
    can_reverse = has_perm(request.user, services.REVERSE, write=True)
    rows = [
        {
            "movement": m,
            "amount": _signed(m),
            "reversible": can_reverse and m.kind in entry_views.REVERSIBLE,
        }
        for m in page
    ]
    can_export = has_perm(request.user, EXPORT)
    context = {"form": form, "page": page, "rows": rows, "can_export": can_export}
    return render(request, "treasury/movements.html", context)


@never_cache
@permission_required(EXPORT)
@require_POST
def export_view(request):
    movements, data = _filtered(MovementFilterForm(request.POST))
    content, total = exports.movements_csv(movements)
    response = HttpResponse(content, content_type="text/csv; charset=utf-8")
    today = timezone.localdate()
    response["Content-Disposition"] = f'attachment; filename="moviments-{today:%Y-%m-%d}.csv"'
    filters = {field: request.POST[field] for field in data if data[field]}
    audit.record(
        EXPORTED, actor=request.user, details={"filters": filters, "rows": total}, request=request
    )
    return response


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
    # Només aquests dos destins: cap redirecció oberta.
    if request.POST.get("des_de") == "conciliacio":
        return redirect("administration:treasury_reconciliation")
    return redirect("administration:treasury_review")


@never_cache
@permission_required(VIEW)
@require_GET
def reconciliation_view(request):
    reconciliation.refresh()  # els càrrecs canvien: les propostes es calculen abans de mostrar-les
    states = (
        StatementLineState.objects.filter(statement_line__in=statement_lines())
        .select_related("statement_line", "proposed_settlement")
        .prefetch_related("proposed_charges__person")
        .order_by("-statement_line__value_date", "-statement_line__pk")
    )
    page = Paginator(states, PER_PAGE).get_page(request.GET.get("pagina"))
    live = {
        found.statement_line_id: found
        for found in Reconciliation.objects.filter(
            statement_line__in=[state.statement_line_id for state in page], undo__isnull=True
        ).select_related("settlement")
    }
    rows = [
        {
            "state": state,
            "line": state.statement_line,
            "amount": euros(state.statement_line.amount_cents),
            "charges": [
                {"charge": charge, "amount": euros(charge.amount_cents)}
                for charge in state.proposed_charges.all()
            ],
            "reconciliation": live.get(state.statement_line_id),
        }
        for state in page
    ]
    context = {
        "page": page,
        "rows": rows,
        "can_reconcile": has_perm(request.user, reconciliation.RECONCILE, write=True),
    }
    return render(request, "treasury/reconciliation.html", context)


def _back_to_reconciliation(request, action, success):
    try:
        action()
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, success)
    return redirect("administration:treasury_reconciliation")


@never_cache
@permission_required(reconciliation.RECONCILE, write=True)
@require_POST
def confirm_view(request, line_id):
    line = get_object_or_404(statement_lines(), pk=line_id)
    return _back_to_reconciliation(
        request,
        lambda: reconciliation.confirm(line, by=request.user),
        _("Conciliació confirmada: els càrrecs consten com a pagats i l'ingrés és al banc."),
    )


@never_cache
@permission_required(reconciliation.RECONCILE, write=True)
@require_POST
def undo_view(request, reconciliation_id):
    found = get_object_or_404(Reconciliation, pk=reconciliation_id)
    done = _("Conciliació desfeta: els càrrecs tornen a estar pendents i l'ingrés s'ha compensat.")
    if found.settlement and found.settlement.source != ProviderSettlement.Source.REMITTANCE:
        done = _("Conciliació desfeta: la liquidació torna a «rebuda» i el traspàs s'ha compensat.")
    return _back_to_reconciliation(
        request,
        lambda: reconciliation.undo(found, reason=request.POST.get("motiu", ""), by=request.user),
        done,
    )


@never_cache
@permission_required(reconciliation.RECONCILE, write=True)
@require_http_methods(["GET", "POST"])
def settlement_line_view(request, line_id):
    line = get_object_or_404(statement_lines(), pk=line_id)
    if request.method == "POST":
        chosen = request.POST.get("liquidacio", "")
        return _back_to_reconciliation(
            request,
            lambda: settlements.confirm_line(
                line, int(chosen) if chosen.isascii() and chosen.isdigit() else 0, by=request.user
            ),
            _("Liquidació conciliada: comissions apuntades i el net, del trànsit al banc."),
        )
    reconciliation.refresh()
    choices = reconciliation.settlement_choices(line)
    if not choices:
        messages.error(request, _("Aquesta línia no té cap liquidació proposada."))
        return redirect("administration:treasury_reconciliation")
    wanted = request.GET.get("liquidacio", "")
    settlement = next((s for s in choices if str(s.pk) == wanted), None)
    if settlement is None and len(choices) == 1:
        settlement = choices[0]
    if settlement is None:  # línia ambigua: primer, el tresorer en tria una (revisió de la #212)
        context = {
            "line": line,
            "amount": euros(line.amount_cents),
            "choices": [{"settlement": s, "net": euros(s.net_cents)} for s in choices],
        }
        return render(request, "treasury/settlement_confirm.html", context)
    split = [
        {"item": item, "amount": euros(item.amount_cents), "fee": euros(fee)}
        for item, fee in settlements.fee_split(settlement).items()
    ]
    context = {
        "settlement": settlement,
        "line": line,
        "amount": euros(line.amount_cents),
        "gross": euros(settlement.gross_cents),
        "net": euros(settlement.net_cents),
        "fees": euros(settlement.fees_cents),
        "items": len(split),
        "split": split,
    }
    return render(request, "treasury/settlement_confirm.html", context)


@never_cache
@permission_required(reconciliation.RECONCILE, write=True)
@require_http_methods(["GET", "POST"])
def match_view(request, line_id):
    line = get_object_or_404(statement_lines(), pk=line_id)
    data = request.POST if request.method == "POST" else request.GET
    query = data.get("cerca", "").strip()[:200]
    selected = data.getlist("carrec")
    # Un valor que no és un identificador buida la tria: el servei la rebutja sencera.
    ids = [
        int(value) for value in selected if value.isascii() and value.isdigit() and len(value) <= 18
    ]
    ids = ids if len(ids) == len(selected) else []
    context = {"line": line, "amount": euros(line.amount_cents), "query": query}
    if request.method == "GET":
        reconciliation.refresh()  # com la conciliació: l'estat de la línia, al dia
        context["problem"] = reconciliation.match_problem(line)
        found, context["more"] = ([], False)
        if not context["problem"]:  # sense formulari, tampoc no es busca res
            found, context["more"] = reconciliation.pending_charges(query)
        context["found"] = [
            {"charge": c, "amount": euros(c.amount_cents), "checked": c.pk in ids} for c in found
        ]
        return render(request, "treasury/match.html", context)
    try:
        if request.POST.get("confirma"):
            reconciliation.match(line, ids, by=request.user)
            messages.success(
                request, _("Línia casada: els càrrecs consten com a pagats i l'ingrés és al banc.")
            )
            return redirect("administration:treasury_reconciliation")
        matched = reconciliation.check_match(line, ids, by=request.user)
    except ValidationError as error:
        # Torna a la cerca amb la tria, perquè el tresorer la corregeixi.
        messages.error(request, " ".join(error.messages))
        url = reverse("administration:treasury_match_line", args=[line.pk])
        return redirect(f"{url}?{urlencode({'cerca': query, 'carrec': ids}, doseq=True)}")
    context["matched"] = [{"charge": c, "amount": euros(c.amount_cents)} for c in matched]
    return render(request, "treasury/match.html", context)
