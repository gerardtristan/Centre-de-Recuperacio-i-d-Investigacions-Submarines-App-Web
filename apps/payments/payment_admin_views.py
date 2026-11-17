"""Llistat de pagaments i «a revisar» del tresorer (T-M05b-16; C de M05b-3; B6 de M05b-4).

- Permís B6 (`payments.view`) al servidor; sense, «no trobat». Ruta d'administració, amb TOTP.
  Només lectura: només GET, i l'únic formulari és el filtre.
- «A revisar» té el que avui queda marcat: els intents «a revisar» (import o càrrec que no
  quadren, duplicats i la xarxa de seguretat; CA-M05b-05, 07 i 33), les notificacions del
  proveïdor que no s'han pogut casar amb cap intent i les transferències conciliades sense rebut
  (P-137). Tancar-los no és d'aquí: d'«a revisar» encara no se'n surt (P-82).
- El nom del pagador només surt a qui pot consultar el llistat de socis (P4, «dades mínimes» n'hi
  ha prou; P-247). El servidor no el passa a la plantilla si no. Cap IBAN ni dada de targeta: el
  05b no en té cap.
"""

from django import forms
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.core.charges import euros
from apps.core.models import Charge, Payment
from apps.core.permissions import has_perm, permission_required

from .models import PaymentAttempt, ProviderEvent

VIEW = "payments.view"  # B6
NAMES = "members.list"  # P4: qui pot veure el nom del pagador (P-247)
PER_PAGE = 50
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
    attempts = PaymentAttempt.objects.select_related("charge__person")
    review = [_row(a, names) for a in attempts.filter(status=S.TO_REVIEW).order_by("-updated_at")]
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
