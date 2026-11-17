"""Pantalla de retornats de l'administració (`/gestio/pagaments/retornats`; P-M05b-F; B4 de
M05b-4; T-M05b-27).

- Permís B4 (`payments.returns`) al servidor, a totes les rutes; sense, «no trobat». Registrar i
  decidir demanen el permís amb edició i són POST amb CSRF.
- El tresorer registra el retorn amb la referència del rebut (l'identificador d'extrem a extrem
  de l'extracte o del fitxer del banc), el codi de motiu i la comissió, si n'hi ha. Si queda un
  reintent possible, el rebut surt a «Per decidir» amb la proposta; si no, l'alternativa ja
  s'ha enviat (P-292).
- Cap IBAN ni nom a la pantalla: el número de soci, el concepte i l'import (minimització).
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

from apps.core.charges import RETURNS  # B4
from apps.core.models import Charge
from apps.core.permissions import has_perm, permission_required, require_perm

from . import returns
from .models import DirectDebitItem

RESULTS = {
    returns.RETRY: gettext_lazy("Retorn registrat. Proposta: reintent a la remesa següent."),
    returns.ALTERNATIVE: gettext_lazy("Retorn registrat. Proposta: alternativa de pagament."),
    returns.SENT: gettext_lazy(
        "Retorn registrat. No queda cap reintent: s'ha aplicat l'alternativa de pagament i el "
        "soci la rep per correu si té adreça."
    ),
}


class ReturnForm(forms.Form):
    end_to_end_id = forms.CharField(
        label=gettext_lazy("Referència del rebut"),
        max_length=35,
        help_text=gettext_lazy("L'identificador d'extrem a extrem de l'extracte o del banc."),
    )
    reason_code = forms.CharField(
        label=gettext_lazy("Codi de motiu"),
        max_length=4,
        help_text=gettext_lazy("Quatre lletres o xifres, per exemple AM04."),
    )
    fee = forms.DecimalField(
        label=gettext_lazy("Comissió de retorn (€)"),
        required=False,
        min_value=Decimal("0.01"),
        max_digits=7,
        decimal_places=2,
        localize=True,
    )


def _register(request, form) -> bool:
    data = form.cleaned_data
    item = DirectDebitItem.objects.filter(
        end_to_end_id=data["end_to_end_id"].strip(), status=DirectDebitItem.Status.COLLECTED
    ).first()
    if item is None:
        form.add_error("end_to_end_id", _("No hi ha cap rebut cobrat amb aquesta referència."))
        return False
    fee = int(data["fee"] * 100) if data["fee"] is not None else None
    try:
        result = returns.register_return(item, data["reason_code"], fee_cents=fee, by=request.user)
    except ValidationError as error:
        form.add_error(None, " ".join(error.messages))
        return False
    messages.success(request, RESULTS[result])
    return True


@never_cache
@permission_required(RETURNS)
@require_http_methods(["GET", "POST"])
def returns_view(request):
    form = ReturnForm(request.POST or None)
    if request.method == "POST":
        require_perm(request, RETURNS, write=True)
        if form.is_valid() and _register(request, form):
            return redirect("administration:payments_returns")
    pending = (
        DirectDebitItem.objects.filter(
            status=DirectDebitItem.Status.RETURNED,
            attempt__charge__status=Charge.Status.RETURNED,
        )
        .select_related("attempt__charge", "mandate__member")
        .order_by("returned_on", "pk")
    )
    context = {
        "form": form,
        "pending": [(item, returns.can_retry(item)) for item in pending],
        "can_manage": has_perm(request.user, RETURNS, write=True),
    }
    return render(request, "payments/returns.html", context)


@never_cache
@permission_required(RETURNS, write=True)
@require_POST
def return_decision_view(request, item_id):
    """P-M05b-F, passos 4 i 5: reintent o alternativa (048)."""
    item = get_object_or_404(DirectDebitItem, pk=item_id)
    decision = request.POST.get("decision")
    if decision not in (returns.RETRY, returns.ALTERNATIVE):
        return redirect("administration:payments_returns")
    try:
        sent = returns.confirm(item, decision, by=request.user)
    except returns.RetryNotAllowed:
        messages.error(request, _("Aquest rebut ja no es pot tornar a passar pel banc."))
    except returns.NotReturned:
        messages.error(request, _("Aquest retorn ja està decidit."))
    else:
        if decision == returns.RETRY:
            messages.success(request, _("La quota entrarà a la remesa següent."))
        elif sent:
            messages.success(request, _("El soci rep l'alternativa de pagament per correu."))
        else:
            messages.error(request, _("El soci no té adreça: cal avisar-lo per una altra via."))
    return redirect("administration:payments_returns")
