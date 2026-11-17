"""Pantalla de retornats de l'administració (`/gestio/pagaments/retornats`; P-M05b-F; B4 de
M05b-4; T-M05b-27).

- Permís B4 (`payments.returns`) al servidor, a totes les rutes; sense, «no trobat». Registrar i
  decidir demanen el permís amb edició i són POST amb CSRF.
- El tresorer registra el retorn amb la referència del rebut (l'identificador d'extrem a extrem
  de l'extracte o del fitxer del banc), el codi de motiu i la comissió, si n'hi ha. Si queda un
  reintent possible, el rebut surt a «Per decidir» amb la proposta; si no, l'alternativa ja
  s'ha enviat (P-292).
- Cap IBAN ni nom a la pantalla: el número de soci, el concepte i l'import (minimització).
- Fitxer de retornats del banc (pain.002; T-M05b-12b): pujar-lo i confirmar-lo demanen B4 amb
  edició. Es llegeix en memòria i fins a 1 MB, com l'extracte (RN-101), i no es desa.
"""

from decimal import Decimal

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.charges import RETURNS  # B4
from apps.core.files import BANK_RETURNS_TYPES, validate_upload
from apps.core.models import Charge
from apps.core.permissions import has_perm, permission_required, require_perm
from apps.core.views.bank_statement import _InMemory

from . import bank_returns, returns
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


def _page(request, form=None, *, file_preview=None, file_error=None, status=200):
    pending = (
        DirectDebitItem.objects.filter(
            status=DirectDebitItem.Status.RETURNED,
            attempt__charge__status=Charge.Status.RETURNED,
        )
        .select_related("attempt__charge", "mandate__member")
        .order_by("returned_on", "pk")
    )
    context = {
        "form": form or ReturnForm(),
        "pending": [(item, returns.can_retry(item)) for item in pending],
        "can_manage": has_perm(request.user, RETURNS, write=True),
        "file_preview": file_preview,
        "file_error": file_error,
    }
    return render(request, "payments/returns.html", context, status=status)


@never_cache
@permission_required(RETURNS)
@require_http_methods(["GET", "POST"])
def returns_view(request):
    form = ReturnForm(request.POST or None)
    if request.method == "POST":
        require_perm(request, RETURNS, write=True)
        if form.is_valid() and _register(request, form):
            return redirect("administration:payments_returns")
    return _page(request, form)


@csrf_exempt
@never_cache
@permission_required(RETURNS, write=True)
@require_POST
def returns_file_view(request):
    handler = _InMemory(request)
    request.upload_handlers = [handler]  # abans que res llegeixi el POST
    return _upload_returns_file(request, handler)


@csrf_protect
def _upload_returns_file(request, handler):
    files = request.FILES.getlist("fitxer")
    if handler.too_large:
        return _page(request, file_error=_("El fitxer supera la mida màxima d'1 MB."), status=413)
    if len(files) != 1:
        return _page(request, file_error=_("Tria un sol fitxer."), status=400)
    try:
        validate_upload(files[0], allowed=BANK_RETURNS_TYPES)
        preview = bank_returns.preview(files[0].read(), by=request.user)
    except ValidationError as exc:
        return _page(request, file_error=exc.messages[0], status=400)
    except bank_returns.Rejected as exc:
        return _page(request, file_error=exc.message, status=400)
    return _page(request, file_preview=preview)


@never_cache
@permission_required(RETURNS, write=True)
@require_POST
def returns_file_confirm_view(request):
    try:
        results = bank_returns.confirm(request.POST.get("testimoni", ""), by=request.user)
    except bank_returns.Stale:
        messages.error(
            request,
            _("La previsualització ha caducat o algun rebut ha canviat. Torna a pujar el fitxer."),
        )
    else:
        messages.success(
            request,
            _(
                "Fitxer registrat: %(total)s retorns. A «Per decidir» hi ha els que esperen la "
                "teva decisió; als altres ja s'ha aplicat l'alternativa de pagament."
            )
            % {"total": sum(results.values())},
        )
    return redirect("administration:payments_returns")


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
