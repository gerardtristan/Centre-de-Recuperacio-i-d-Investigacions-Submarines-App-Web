"""Llistat de pagaments i «a revisar» del tresorer (T-M05b-16; C de M05b-3; B6 de M05b-4).

- Permís B6 (`payments.view`) al servidor; sense, «no trobat». Ruta d'administració, amb TOTP.
  El llistat és només GET; tancar un «a revisar» demana B6 amb edició, POST amb CSRF i una nota.
- «A revisar» té el que avui queda marcat: els intents «a revisar» (import o càrrec que no
  quadren, duplicats i la xarxa de seguretat; CA-M05b-05, 07 i 33), les notificacions del
  proveïdor que no s'han pogut casar amb cap intent i les transferències conciliades sense rebut
  (P-137). Un intent «a revisar» es tanca amb una nota (T-M05b-16b; P-82, opció per defecte):
  surt de la llista oberta i passa a «Tancats», però l'intent no canvia d'estat ni es mou cap
  diner (`reviews.close`).
- El nom del pagador només surt a qui pot consultar el llistat de socis (P4, «dades mínimes» n'hi
  ha prou; P-247). El servidor no el passa a la plantilla si no. Cap IBAN ni dada de targeta: el
  05b no en té cap.
"""

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.charges import euros
from apps.core.models import AuditEntry, Charge, Payment
from apps.core.permissions import has_perm, permission_required

from . import reviews
from .models import PaymentAttempt, ProviderEvent, ReviewClosure

VIEW = "payments.view"  # B6
NAMES = "members.list"  # P4: qui pot veure el nom del pagador (P-247)
PER_PAGE = 50
CLOSED_SHOWN = 50  # shortcut: només els tancaments més recents; si en calen més, paginar-los
S = PaymentAttempt.Status


class AttemptFilterForm(forms.Form):
    estat = forms.ChoiceField(
        label=_("Estat"), required=False, choices=[("", _("Tots")), *S.choices]
    )


def _row(attempt, names):
    return {
        "attempt": attempt,
        "amount": euros(attempt.amount_cents),
        "payer": attempt.charge.person if names else None,
    }


def transfers_without_receipt():
    """P-137: càrrecs pagats per una transferència conciliada sense cap intent pagat, i per
    tant sense rebut. Surten de la llista quan l'intent i el rebut existeixen."""
    return (
        Charge.objects.filter(
            status=Charge.Status.PAID,
            payments__method=Payment.Method.TRANSFER,
            payments__cancellation__isnull=True,
        )
        .exclude(attempts__status=S.PAID)
        .select_related("person")
        .distinct()
        .order_by("-updated_at", "-pk")
    )


@never_cache
@permission_required(VIEW)
@require_GET
def payments_view(request):
    names = has_perm(request.user, NAMES)
    # Una decisió («Pagat» o «Fallit») treu l'intent d'«a revisar» a la mateixa transacció: tot
    # intent «a revisar» és obert. Els tancats «sense decisió» (T-M05b-16b) hi surten marcats.
    latest = ReviewClosure.objects.filter(attempt=OuterRef("pk")).order_by("-closed_at", "-pk")
    attempts = PaymentAttempt.objects.select_related("charge__person").annotate(
        closure_outcome=Subquery(latest.values("outcome")[:1])
    )
    review = [_row(a, names) for a in attempts.filter(status=S.TO_REVIEW).order_by("-updated_at")]
    can_close = has_perm(request.user, VIEW, write=True)
    closures = ReviewClosure.objects.select_related("attempt__charge__person", "closed_by__person")
    closed = [
        {**_row(c.attempt, names), "closure": c}
        for c in closures.order_by("-closed_at", "-pk")[:CLOSED_SHOWN]
    ]
    # La nota és text lliure: només amb P4 o a qui pot tancar (B6 amb edició); la resta, «—».
    notes = _notes([row["closure"].pk for row in closed]) if names or can_close else {}
    for row in closed:
        row["note"] = notes.get(str(row["closure"].pk), "")
    # Les «error» no: la xarxa de seguretat les torna a provar (T-M05b-05).
    events = ProviderEvent.objects.filter(result=ProviderEvent.Result.TO_REVIEW).order_by(
        "-received_at"
    )
    receipts = [
        {"charge": c, "amount": euros(c.amount_cents), "payer": c.person if names else None}
        for c in transfers_without_receipt()
    ]

    form = AttemptFilterForm(request.GET or None)
    status = form.cleaned_data["estat"] if form.is_valid() else ""
    listed = attempts.filter(status=status) if status else attempts
    page = Paginator(listed.order_by("-created_at", "-pk"), PER_PAGE).get_page(
        request.GET.get("pagina")
    )
    context = {
        "names": names,
        "review": review,
        "closed": closed,
        "closed_total": closures.count(),
        "closed_shown": CLOSED_SHOWN,
        "can_close": can_close,
        "events": [
            {"event": e, "amount": euros(e.amount_cents) if e.amount_cents is not None else ""}
            for e in events
        ],
        "receipts": receipts,
        "form": form,
        "page": page,
        "rows": [_row(a, names) for a in page],
    }
    return render(request, "payments/payments.html", context)


def _notes(closure_ids) -> dict[str, str]:
    """{tancament: nota}, de l'entrada del registre (`reviews.close`)."""
    entries = AuditEntry.objects.filter(
        action=reviews.CLOSED,
        target_type=ReviewClosure._meta.label_lower,
        target_id__in=[str(pk) for pk in closure_ids],
    )
    return dict(entries.values_list("target_id", "reason"))


OUTCOME_LABELS = {
    ReviewClosure.Outcome.PAID: _("Pagat: el proveïdor l'ha cobrat. Es registra el pagament."),
    ReviewClosure.Outcome.FAILED: _("Fallit: no s'ha cobrat. No es mou cap diner."),
}


class CloseForm(forms.Form):
    def __init__(self, *args, can_pay=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not can_pay:  # sense M14, «Pagat» no es pot triar (el servidor també ho comprova)
            self.fields["outcome"].choices = [
                c for c in self.fields["outcome"].choices if c[0] != ReviewClosure.Outcome.PAID
            ]

    outcome = forms.ChoiceField(
        label=_("Què ha passat"),
        choices=[(o.value, OUTCOME_LABELS[o]) for o in ReviewClosure.OUTCOMES],
        widget=forms.RadioSelect,
        error_messages={"required": _("Tria si s'ha pagat o ha fallat.")},
    )
    note = forms.CharField(
        label=_("Nota"),
        max_length=reviews.MAX_NOTE,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_(
            "Què has comprovat i què se n'ha fet (per exemple, «devolució feta des del "
            "proveïdor»). Queda al registre d'activitat. No hi posis dades personals: el número "
            "de càrrec ja identifica el cas."
        ),
        error_messages={"required": _("Cal una nota per tancar-lo.")},
    )


@never_cache
@permission_required(VIEW, write=True)
@require_http_methods(["GET", "POST"])
def review_close_view(request, attempt_id):
    """Pàgina de confirmació i decisió d'un intent «a revisar» (T-M05b-16b i 16c)."""
    attempt = get_object_or_404(
        PaymentAttempt.objects.select_related("charge__person"), pk=attempt_id, status=S.TO_REVIEW
    )
    can_pay = reviews.can_record_paid(request.user, attempt.charge)
    form = CloseForm(request.POST or None, can_pay=can_pay)
    if request.method == "POST" and form.is_valid():
        outcome = form.cleaned_data["outcome"]
        try:
            reviews.close(attempt, outcome=outcome, note=form.cleaned_data["note"], by=request.user)
        except reviews.NotClosable:
            messages.error(request, gettext("Aquest intent ja està tancat."))
        except reviews.PaidRefused as refused:
            form.add_error("outcome", str(refused))
        else:
            done = {
                ReviewClosure.Outcome.PAID: gettext(
                    "Intent tancat com a pagat: s'ha registrat el pagament."
                ),
                ReviewClosure.Outcome.FAILED: gettext(
                    "Intent tancat com a fallit. No s'ha mogut cap diner."
                ),
            }
            messages.success(request, done[outcome])
            return redirect("administration:payments_list")
        if not form.errors:
            return redirect("administration:payments_list")
    context = {"row": _row(attempt, has_perm(request.user, NAMES)), "form": form}
    context["can_pay"] = can_pay
    return render(request, "payments/review_close.html", context)
