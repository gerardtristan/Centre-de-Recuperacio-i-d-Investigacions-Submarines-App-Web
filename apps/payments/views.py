"""Vistes del 05b: la notificació del proveïdor (05a), la pantalla de pagament del soci i la
consulta d'estat amb HTMX (T-M05b-04; P-M05b-A, passos 1, 4 i 6; M05b-8, «Rutes»), i la pàgina
de pagament del proveïdor fals.

La pantalla del soci només mostra l'estat que diu el servidor (`payment_status`): la tornada
del navegador (`?tornada=ok`) no canvia res ni dona res per pagat (CA-M05b-02, RN-M05b-05).
Per objecte (M05b-4): cadascú només veu i paga els seus càrrecs; un d'un altre o que no
existeix és «no trobat» en tots dos casos, i l'intent queda al registre (com CA-M01-25)."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core import audit, charges
from apps.core.models import Charge

from . import attempts, checkout, webhooks
from .models import PaymentAttempt, Receipt
from .providers import base, fake, get_provider
from .providers.base import ProviderError, ProviderNotConfigured


@csrf_exempt  # Servidor a servidor: l'autenticació és la firma del proveïdor, no una sessió.
@login_not_required  # Ruta pública declarada (RN-40; M05a-8).
@require_POST
def provider_notification(request, provider_code: str):
    try:
        provider = get_provider()
    except ProviderNotConfigured:
        raise Http404 from None
    if provider.code != provider_code:
        raise Http404
    return HttpResponse(status=webhooks.receive(provider, request).http_status)


def _not_found(request, model, pk):
    audit.record(
        audit.Action.PERSONAL_AREA_NOT_FOUND,
        actor=request.user,
        target=model.objects.filter(pk=pk).first(),
        details={"object": model._meta.label_lower, "id": pk},
        request=request,
    )
    raise Http404


def _own_charge(request, charge_id) -> Charge:
    charge = Charge.objects.filter(pk=charge_id, person=request.user.person).first()
    return charge or _not_found(request, Charge, charge_id)


def _offers_bizum() -> bool:
    """Les pantalles només ofereixen el que el proveïdor declara (`capabilities`)."""
    try:
        return get_provider().capabilities().bizum
    except ProviderError:
        return False


def _status_context(charge):
    return {
        "charge": charge,
        "status": checkout.payment_status(charge),
        "bizum": _offers_bizum(),
    }


@never_cache
@require_GET
def charge_view(request, charge_id):
    """`/socis/pagaments/{càrrec}/`: la pantalla de pagament i on torna el navegador
    (`?tornada=ok` o `ko`), que no es llegeix: només val el que diu el servidor."""
    charge = _own_charge(request, charge_id)
    context = {**_status_context(charge), "amount": charges.euros(charge.amount_cents)}
    return render(request, "payments/charge.html", context)


@never_cache
@require_POST
def pay_view(request, charge_id, method):
    """«Paga amb targeta» o «Paga amb Bizum» (P-M05b-A i B, passos 1 i 2): el navegador va a la
    pàgina del proveïdor. Amb un intent en curs no se'n comença cap altre (RN-M05b-04; P-83,
    opció per defecte): la pantalla explica que s'espera la confirmació."""
    charge = _own_charge(request, charge_id)
    try:
        start = checkout.start_payment(charge, method, request.user)
    except attempts.AttemptInProgress:
        messages.error(
            request,
            _("El pagament anterior encara no s'ha tancat. Torna-ho a provar d'aquí a una estona."),
        )
        return redirect("payments:charge", charge.pk)
    except (attempts.AttemptAlreadyPaid, attempts.ChargeNotPayable):
        return redirect("payments:charge", charge.pk)
    except (attempts.MethodNotAllowed, ProviderError):
        unavailable = {
            PaymentAttempt.Method.CARD: _("Ara no es pot pagar amb targeta."),
            PaymentAttempt.Method.BIZUM: _("Ara no es pot pagar amb Bizum."),
        }
        messages.error(request, f"{unavailable[method]} {_('Torna-ho a provar més tard.')}")
        return redirect("payments:charge", charge.pk)
    # shortcut: sempre redirecció; el camp incrustat (`checkout.IFRAME`) arriba amb el proveïdor
    # real, si en té (P-45 punt 4). El proveïdor fals no en té.
    return HttpResponseRedirect(start.url)


@never_cache
@require_GET
def attempt_status_view(request, attempt_id):
    """`/socis/pagaments/{intent}/estat/` (HTMX): torna a dibuixar l'estat; mentre és en curs,
    el fragment es torna a demanar sol."""
    attempt = PaymentAttempt.objects.filter(
        pk=attempt_id, charge__person=request.user.person
    ).first()
    if attempt is None:
        _not_found(request, PaymentAttempt, attempt_id)
    return render(request, "payments/_status.html", _status_context(attempt.charge))


@never_cache
@require_GET
def receipt_view(request, attempt_id):
    """`/socis/pagaments/{intent}/rebut/` (RN-M05b-19): el rebut d'un pagament propi, que es desa
    com a PDF des del navegador (P-85). D'un altre, sense rebut o inexistent: «no trobat»."""
    receipt = (
        Receipt.objects.select_related("attempt__charge__department")
        .filter(attempt_id=attempt_id, attempt__charge__person=request.user.person)
        .first()
    )
    if receipt is None:
        _not_found(request, PaymentAttempt, attempt_id)
    charge = receipt.attempt.charge
    context = {
        "receipt": receipt,
        "charge": charge,
        "amount": charges.euros(charge.amount_cents),
        "club_tax_id": settings.CLUB_TAX_ID,
    }
    return render(request, "payments/receipt.html", context)


# --- Proveïdor fals: la pàgina on es «paga». Només amb l'entorn de proves -----------------------


@login_not_required  # Fa el paper d'una pàgina de fora de la plataforma: ruta pública declarada.
@never_cache
@require_http_methods(["GET", "POST"])
def fake_pay_view(request, order_id):
    try:
        provider = get_provider()
        order = provider.get_order(order_id)
    except ProviderError:
        raise Http404 from None
    if not isinstance(provider, fake.FakeProvider) or order.status != base.PENDING:
        raise Http404
    if request.method == "POST":
        results = {"pay": base.PAID, "deny": base.DENIED, "leave": base.PENDING}
        result = results.get(request.POST.get("resultat"))
        if result is None:
            raise Http404
        return HttpResponseRedirect(provider.complete(order_id, result))
    context = {
        "order": order,
        "amount": charges.euros(order.amount_cents),
        "bizum": provider.is_bizum(order_id),
    }
    return render(request, "payments/fake_pay.html", context)
