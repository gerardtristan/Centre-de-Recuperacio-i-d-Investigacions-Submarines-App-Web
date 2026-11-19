"""Pantalles de tresoreria (T-M04-15, primer tall; C1 i C8 de M04-3): comptes amb el saldo calculat
i llista de moviments amb filtres. Només lectura: només GET, i l'únic formulari és el dels filtres.

- Permís T1 (`treasury.view`) al servidor; sense, «no trobat» (059). Ruta d'administració, amb TOTP.
- Cap IBAN: del compte només surten el nom, el tipus i els quatre darrers dígits (RN-T03).
- Cap nom de persona: el concepte del moviment no en porta (RNF-T4).
- Un moviment anul·lat continua a la llista, marcat (CA-T06.1, RN-T25).

«A revisar» (T-M04-14, C6; CA-T12.1, CA-T13.1): les línies de l'extracte amb el motiu, i el
formulari per excloure'n una (POST, T8 al servidor). Sense el concepte de la línia, que pot
portar noms de fora del club i només es veu a la conciliació (M04-4, per objecte). T-M04-14b
(P-191, opció per defecte): també les liquidacions «a revisar» (CA-T11.2), amb la referència i el
problema, i l'enllaç a «Liquidacions»; els intents del 05b, un enllaç a la seva llista (amb B6).
T-M04-14c (P-390, resposta B): «Tanca…» porta a la confirmació amb nota obligatòria (T10 amb
edició, `settlements.close_review`); la tancada passa a «Tancades». Cap diner no es mou.

Conciliació (T-M04-15, segon tall; C5 i C6; P-M04-E, passos 3 i 5): les línies dels extractes
vigents amb l'estat, el concepte (tapat per la importació) i els càrrecs proposats o casats.
«Confirma» (`reconciliation.confirm`) i «Desfés» amb motiu (`reconciliation.undo`) són POST amb
T4 al servidor; veure-la és T1. Del càrrec, el nom de la persona, el concepte i l'import (M04-4).
«Casa a mà» (T-M04-12e, `reconciliation.match`): T4 per veure-la i fer-la; cerca de càrrecs
pendents per referència o número de soci, revisió amb la suma i confirmació, tot per POST.
«Casa amb moviments» (T-M04-12f, `reconciliation.match_movements`): igual, amb els moviments del
banc que ja hi són, i les liquidacions rebudes amb el net exacte (P-395); cap diner no es mou.
Una línia proposada amb una liquidació del proveïdor (T-M04-13b; P-M04-F, passos 3 i 4) es
confirma en dos passos: el GET mostra el brut, les comissions (amb el repartiment de cada
cobrament, VT-05) i el net, i el POST crida `settlements.confirm_line`; tot amb T4.

Panell de la conciliació (T-DX-72): a l'escriptori, «Casa a mà», «Casa amb moviments» i «Revisa i
confirma» es carreguen amb HTMX (capçalera `HX-Request`) des de les mateixes vistes, amb el mateix
permís, el mateix POST amb CSRF i les mateixes comprovacions; en reben només el cos (`_page`).
Sense JavaScript, la pàgina sencera, com abans. El panell no és cap control.

Exportació CSV (T-M04-16, C8; CA-T15.1): els moviments amb els mateixos filtres que la llista,
per POST i amb T9 al servidor; cada exportació queda al registre amb els filtres i les files.
"""

from urllib.parse import urlencode

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, DurationField, ExpressionWrapper, Value
from django.db.models.functions import Greatest, Least
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core import audit, charges
from apps.core.charges import euros
from apps.core.imports import statement_lines
from apps.core.models import AuditEntry, Department
from apps.core.permissions import has_perm, permission_required

from . import entry_views, exports, reconciliation, services, settlements
from .balances import balances
from .models import (
    CostCentre,
    Movement,
    ProviderSettlement,
    Reconciliation,
    SettlementReviewClosure,
    StatementLineState,
    TreasuryAccount,
)

VIEW = "treasury.view"  # T1
EXPORT = "treasury.export"  # T9, «Exportar moviments en CSV» (M04-4)
EXPORTED = "treasury.movements_exported"
PER_PAGE = 50
CLOSED_SHOWN = 50  # shortcut: només els tancaments més recents; si en calen més, paginar-los


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
    movements = movements.with_reversal().select_related(
        "account", "department", "cost_centre", "payment"
    )
    page = Paginator(movements.order_by("-value_date", "-recorded_at", "-id"), PER_PAGE).get_page(
        request.GET.get("pagina")
    )
    can_reverse = has_perm(request.user, services.REVERSE, write=True)
    # P-12b: l'enllaç només a qui el pot obrir (M14); el control és a `files.can_access`.
    can_proof = has_perm(request.user, charges.MANUAL_PAYMENT)
    rows = [
        {
            "movement": m,
            "amount": _signed(m),
            "reversible": can_reverse and m.kind in entry_views.REVERSIBLE,
            "proof": can_proof and m.payment and m.payment.proof_id,
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
@permission_required(reconciliation.REVIEW)
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
    to_review = ProviderSettlement.objects.filter(
        status=ProviderSettlement.Status.TO_REVIEW, review_closure__isnull=True
    )
    can_close = has_perm(request.user, reconciliation.REVIEW, write=True)
    closures = SettlementReviewClosure.objects.select_related("settlement", "closed_by__person")
    closed = list(closures.order_by("-closed_at", "-pk")[:CLOSED_SHOWN])
    # La nota és text lliure: només la veu qui pot tancar (T10 amb edició); la resta, «—».
    notes = _closure_notes([c.pk for c in closed]) if can_close else {}
    context = {
        "rows": rows,
        "settlements": [
            {"settlement": s, "net": euros(s.net_cents), "problems": entry_views.problems_of(s)}
            for s in to_review.order_by("settled_on", "pk")
        ],
        "closed": [
            {"closure": c, "net": euros(c.settlement.net_cents), "note": notes.get(str(c.pk), "")}
            for c in closed
        ],
        "closed_total": closures.count(),
        "can_close": can_close,
        "can_exclude": has_perm(request.user, reconciliation.EXCLUDE, write=True),  # T8
        "can_reconcile": has_perm(request.user, reconciliation.RECONCILE, write=True),  # T4
        "can_view_accounts": has_perm(request.user, VIEW),  # on porta «Torna…» (T1)
        "can_view_payments": has_perm(request.user, "payments.view"),  # B6, només per a l'enllaç
    }
    return render(request, "treasury/review.html", context)


def _closure_notes(closure_ids) -> dict[str, str]:
    """{tancament: nota}, de l'entrada del registre (`settlements.close_review`)."""
    entries = AuditEntry.objects.filter(
        action=settlements.REVIEW_CLOSED,
        target_type=SettlementReviewClosure._meta.label_lower,
        target_id__in=[str(pk) for pk in closure_ids],
    )
    return dict(entries.values_list("target_id", "reason"))


class CloseReviewForm(forms.Form):
    note = forms.CharField(
        label=_("Nota"),
        max_length=settlements.MAX_NOTE,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_(
            "Què has comprovat i què se n'ha fet. Queda al registre d'activitat. No hi posis "
            "dades personals: la liquidació i la referència ja identifiquen el cas."
        ),
        error_messages={"required": _("Cal una nota per tancar-la.")},
    )


@never_cache
@permission_required(reconciliation.REVIEW, write=True)
@require_http_methods(["GET", "POST"])
def settlement_review_close_view(request, settlement_id):
    """Confirmació i tancament d'una liquidació «a revisar» (T-M04-14c; P-390, resposta B)."""
    settlement = get_object_or_404(
        ProviderSettlement,
        pk=settlement_id,
        status=ProviderSettlement.Status.TO_REVIEW,
        review_closure__isnull=True,
    )
    form = CloseReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            settlements.close_review(settlement, note=form.cleaned_data["note"], by=request.user)
        except settlements.NotClosable:
            messages.error(request, _("Aquesta liquidació ja està tancada."))
        else:
            messages.success(request, _("Liquidació tancada. No s'ha mogut cap diner."))
        return redirect("administration:treasury_review")
    context = {
        "settlement": settlement,
        "net": euros(settlement.net_cents),
        "problems": entry_views.problems_of(settlement),
        "form": form,
    }
    return render(request, "treasury/settlement_review_close.html", context)


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
    # Només aquests destins, i un que el compte pugui obrir (T10, T1): cap redirecció oberta.
    if request.POST.get("des_de") != "conciliacio" and has_perm(
        request.user, reconciliation.REVIEW
    ):
        return redirect("administration:treasury_review")
    if has_perm(request.user, VIEW):
        return redirect("administration:treasury_reconciliation")
    return redirect("administration:home")


# T-M04-14d (097, P-192): desfer una exclusió amb motiu, des de la conciliació, amb T8.
@never_cache
@permission_required(reconciliation.EXCLUDE, write=True)
@require_POST
def undo_exclusion_view(request, line_id):
    line = get_object_or_404(statement_lines(), pk=line_id)
    try:
        reconciliation.undo_exclusion(line, reason=request.POST.get("motiu", ""), by=request.user)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, _("Exclusió desfeta. La línia torna a estar oberta."))
    if has_perm(request.user, VIEW):
        return redirect("administration:treasury_reconciliation")
    return redirect("administration:home")


def _page(request, template, context):
    """T-DX-72: el panell de la conciliació demana la mateixa pàgina amb HTMX i en rep només el cos
    (`treasury/_panell.html`); sense JavaScript, la pàgina sencera."""
    panell = bool(request.headers.get("HX-Request"))
    base = "treasury/_panell.html" if panell else "base_admin.html"
    return render(request, template, {**context, "panell": panell, "base": base})


@never_cache
@permission_required(VIEW)
@require_GET
def reconciliation_view(request):
    if request.headers.get("HX-Request"):
        # Un pas del panell que acaba aquí (una redirecció) porta tota la pàgina: la conciliació no
        # s'encasta dins del panell, i els missatges es mostren en carregar-la.
        response = HttpResponse(status=204)
        response["HX-Redirect"] = request.get_full_path()
        return response
    reconciliation.refresh()  # els càrrecs canvien: les propostes es calculen abans de mostrar-les
    states = (
        StatementLineState.objects.filter(statement_line__in=statement_lines())
        .select_related("statement_line", "proposed_settlement")
        .prefetch_related("proposed_charges__person")
        .order_by("-statement_line__value_date", "-statement_line__pk")
    )
    page = Paginator(states, PER_PAGE).get_page(request.GET.get("pagina"))
    counts = dict(states.order_by().values_list("status").annotate(Count("pk")))
    live = {
        found.statement_line_id: found
        for found in Reconciliation.objects.filter(
            statement_line__in=[state.statement_line_id for state in page], undo__isnull=True
        )
        .select_related("settlement")
        .prefetch_related("matched_movements")
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
    S = StatementLineState.Status
    context = {
        "page": page,
        "rows": rows,
        "counts": {status: counts.get(status, 0) for status in S.values},
        "open": counts.get(S.PENDING, 0) + counts.get(S.PROPOSED, 0),
        "can_reconcile": has_perm(request.user, reconciliation.RECONCILE, write=True),
        "can_exclude": has_perm(request.user, reconciliation.EXCLUDE, write=True),
        "can_review": has_perm(request.user, reconciliation.REVIEW),
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
    if found.settlement and found.settlement.source != found.settlement.Source.REMITTANCE:
        done = _("Conciliació desfeta: la liquidació torna a «rebuda» i el traspàs s'ha compensat.")
    elif found.matched_movements.exists():  # T-M04-12f (P-394)
        done = _("Conciliació desfeta: la línia torna a «pendent». Els moviments no es toquen.")
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
        return _page(request, "treasury/settlement_confirm.html", context)
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
    return _page(request, "treasury/settlement_confirm.html", context)


def _ids(selected) -> list[int]:
    """Els identificadors triats. Un valor que no ho és buida la tria: el servei la rebutja."""
    ids = [int(v) for v in selected if v.isascii() and v.isdigit() and len(v) <= 18]
    return ids if len(ids) == len(selected) else []


@never_cache
@permission_required(reconciliation.RECONCILE, write=True)
@require_http_methods(["GET", "POST"])
def match_view(request, line_id):
    line = get_object_or_404(statement_lines(), pk=line_id)
    data = request.POST if request.method == "POST" else request.GET
    query = data.get("cerca", "").strip()[:200]
    ids = _ids(data.getlist("carrec"))
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
        return _page(request, "treasury/match.html", context)
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
    return _page(request, "treasury/match.html", context)


# T-M04-12f (CA-T07.2; P-394, P-395): casar una línia pendent amb moviments que ja hi són, o
# triar a mà una liquidació rebuda amb el net exacte (que es confirma a `settlement_line_view`).
@never_cache
@permission_required(reconciliation.RECONCILE, write=True)
@require_http_methods(["GET", "POST"])
def match_movements_view(request, line_id):
    line = get_object_or_404(statement_lines(), pk=line_id)
    data = request.POST if request.method == "POST" else request.GET
    ids = _ids(data.getlist("moviment"))
    context = {"line": line, "amount": euros(line.amount_cents)}
    if request.method == "GET":
        reconciliation.refresh()
        context["problem"] = reconciliation.match_problem(line, incoming=False)
        found = []
        if not context["problem"]:
            day = Value(line.value_date)
            distance = Greatest("value_date", day) - Least("value_date", day)
            found = list(
                reconciliation.matchable_movements(line)
                .select_related("account")
                .annotate(distance=ExpressionWrapper(distance, output_field=DurationField()))
                .order_by("distance", "-pk")[: reconciliation.SEARCH_LIMIT + 1]
            )
            context["settlements"] = [
                {"settlement": s, "net": euros(s.net_cents)}
                for s in reconciliation.settlement_choices(line, limit=reconciliation.SEARCH_LIMIT)
            ]
        # shortcut: els 20 més propers a la data de la línia, sense cerca; si no n'hi ha prou,
        # afegir-hi una cerca.
        context["more"] = len(found) > reconciliation.SEARCH_LIMIT
        context["found"] = [
            {"movement": m, "amount": euros(m.amount_cents), "checked": m.pk in ids}
            for m in found[: reconciliation.SEARCH_LIMIT]
        ]
        return _page(request, "treasury/match_movements.html", context)
    try:
        if request.POST.get("confirma"):
            reconciliation.match_movements(line, ids, by=request.user)
            messages.success(request, _("Línia casada amb els moviments. No s'ha mogut cap diner."))
            return redirect("administration:treasury_reconciliation")
        matched = reconciliation.check_match_movements(line, ids, by=request.user)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
        url = reverse("administration:treasury_match_movements", args=[line.pk])
        return redirect(f"{url}?{urlencode({'moviment': ids}, doseq=True)}")
    context["matched"] = [{"movement": m, "amount": euros(m.amount_cents)} for m in matched]
    return _page(request, "treasury/match_movements.html", context)
