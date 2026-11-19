"""Vistes del 05b: la notificació del proveïdor (05a), la pantalla de pagament del soci i la
consulta d'estat amb HTMX (T-M05b-04; P-M05b-A, passos 1, 4 i 6; M05b-8, «Rutes»), i la pàgina
de pagament del proveïdor fals.

La pantalla del soci només mostra l'estat que diu el servidor (`payment_status`): la tornada
del navegador (`?tornada=ok`) no canvia res ni dona res per pagat (CA-M05b-02, RN-M05b-05).
Per objecte (M05b-4): cadascú només veu i paga els seus càrrecs; un d'un altre o que no
existeix és «no trobat» en tots dos casos, i l'intent queda al registre (com CA-M01-25).

Convidat (T-M05b-08; CA-M05b-09; decisió 021): `/pagaments/convidat/...`, rutes públiques
declarades. La credencial és l'enllaç de la 00 obert en aquest navegador
(`guest_links.for_request`, que el torna a comprovar a cada petició); el càrrec surt sempre de
l'enllaç, mai de l'adreça. Sense enllaç que funcioni, a la pàgina del convidat de la 00, que no
diu per què. El pagament segueix les mateixes regles que el del soci (`checkout.start_payment`
amb l'enllaç)."""

from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core import audit, charges, guest_links
from apps.core.models import Charge
from apps.treasury import services as treasury

from . import attempts, checkout, webhooks
from .models import PaymentAttempt, Receipt
from .providers import base, enabled_capabilities, fake, get_provider
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


def _offers(method) -> bool:
    """Les pantalles només ofereixen el que el proveïdor declara i el club té actiu (P-131)."""
    try:
        return getattr(enabled_capabilities(), method)
    except ProviderError:
        return False


def _transfer(status):
    """CA-M05b-10: mentre s'espera una transferència, l'IBAN del club, l'import i la referència
    del càrrec, cadascun amb el valor que copia el botó (l'import, sense el símbol de l'euro)."""
    attempt = status.attempt
    if status.state != checkout.IN_PROGRESS or attempt.method != PaymentAttempt.Method.TRANSFER:
        return None
    iban, cents = checkout.transfer_iban(), attempt.amount_cents
    return {
        "iban": iban,
        "iban_grouped": " ".join(iban[i : i + 4] for i in range(0, len(iban), 4)),
        "amount": charges.euros(cents),
        "amount_copy": f"{cents // 100},{cents % 100:02d}",
        "reference": treasury.transfer_reference(attempt.charge),
    }


def _urls(charge, attempt, guest):
    """Les adreces de la pantalla: les del soci porten el càrrec o l'intent; les del convidat, cap
    identificador (l'enllaç de la sessió diu quin càrrec és)."""
    if guest:
        names = ("pay_card", "pay_bizum", "pay_transfer", "status", "receipt")
        return {name: reverse(f"payments:guest_{name}") for name in names}
    urls = {
        f"pay_{m}": reverse(f"payments:pay_{m}", args=[charge.pk])
        for m in ("card", "bizum", "transfer")
    }
    if attempt is not None:
        urls["status"] = reverse("payments:attempt_status", args=[attempt.pk])
        urls["receipt"] = reverse("payments:receipt", args=[attempt.pk])
    return urls


def _status_context(charge, guest=False):
    status = checkout.payment_status(charge)
    return {
        "charge": charge,
        "status": status,
        "urls": _urls(charge, status.attempt, guest),
        "card": _offers("card"),
        "bizum": _offers("bizum"),
        "transfer_offered": bool(checkout.transfer_iban()),
        "transfer": _transfer(status),
    }


@never_cache
@require_GET
def charge_view(request, charge_id):
    """`/socis/pagaments/{càrrec}/`: la pantalla de pagament i on torna el navegador
    (`?tornada=ok` o `ko`), que no es llegeix: només val el que diu el servidor."""
    charge = _own_charge(request, charge_id)
    context = {**_status_context(charge), "amount": charges.euros(charge.amount_cents)}
    return render(request, "payments/charge.html", context)


def _pay(request, charge, method, actor, back):
    """«Paga amb targeta» o «Paga amb Bizum» (P-M05b-A i B, passos 1 i 2): el navegador va a la
    pàgina del proveïdor. «Paga per transferència» (P-M05b-C): torna a la pantalla (`back`), que
    mostra les dades per fer-la. Amb un intent en curs no se'n comença cap altre (RN-M05b-04;
    P-83, opció per defecte): la pantalla explica que s'espera la confirmació."""
    try:
        start = checkout.start_payment(charge, method, actor)
    except attempts.AttemptInProgress:
        messages.error(
            request,
            _("El pagament anterior encara no s'ha tancat. Torna-ho a provar d'aquí a una estona."),
        )
        return back
    except (attempts.AttemptAlreadyPaid, attempts.ChargeNotPayable):
        return back
    except (attempts.MethodNotAllowed, ProviderError):
        unavailable = {
            PaymentAttempt.Method.CARD: _("Ara no es pot pagar amb targeta."),
            PaymentAttempt.Method.BIZUM: _("Ara no es pot pagar amb Bizum."),
            PaymentAttempt.Method.TRANSFER: _("Ara no es pot pagar per transferència."),
        }
        messages.error(request, f"{unavailable[method]} {_('Torna-ho a provar més tard.')}")
        return back
    if start.kind == checkout.TRANSFER_DETAILS:
        return back
    # shortcut: sempre redirecció; el camp incrustat (`checkout.IFRAME`) arriba amb el proveïdor
    # real, si en té (P-45 punt 4). El proveïdor fals no en té.
    return HttpResponseRedirect(start.url)


@never_cache
@require_POST
def pay_view(request, charge_id, method):
    charge = _own_charge(request, charge_id)
    return _pay(request, charge, method, request.user, redirect("payments:charge", charge.pk))


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
    back = reverse("payments:charge", args=[receipt.attempt.charge_id])
    return _render_receipt(request, receipt, back)


def _render_receipt(request, receipt, back, guest=False):
    charge = receipt.attempt.charge
    context = {
        "receipt": receipt,
        "charge": charge,
        "amount": charges.euros(charge.amount_cents),
        "club_tax_id": settings.CLUB_TAX_ID,
        "back": back,
        "guest": guest,
    }
    return render(request, "payments/receipt.html", context)


# --- Convidat (T-M05b-08): l'enllaç de la 00 obert en aquest navegador és la credencial ---------


def _guest(view):
    """Ruta pública declarada (RN-40) que només respon amb un enllaç que funciona. Sense, a la
    pàgina del convidat de la 00 (HTMX: HX-Redirect), que no diu si l'enllaç existeix."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        link = guest_links.for_request(request)
        if link is None:
            if request.headers.get("HX-Request"):
                response = HttpResponse(status=204)
                response["HX-Redirect"] = reverse("core:guest")
                return response
            return redirect("core:guest")
        response = view(request, link, *args, **kwargs)
        response["X-Robots-Tag"] = "noindex, nofollow"
        response["Referrer-Policy"] = "same-origin"
        return response

    return login_not_required(never_cache(wrapper))


@_guest
@require_GET
def guest_charge_view(request, link):
    """`/pagaments/convidat/`: la pantalla de pagament del càrrec de l'enllaç i on torna el
    navegador del proveïdor (CA-02.9: «s'està confirmant»; la tornada no canvia res)."""
    charge = link.charge
    context = {
        **_status_context(charge, guest=True),
        "amount": charges.euros(charge.amount_cents),
        "guest": True,
    }
    return render(request, "payments/charge.html", context)


@_guest
@require_POST
def guest_pay_view(request, link, method):
    return _pay(request, link.charge, method, link, redirect("payments:guest_charge"))


@_guest
@require_GET
def guest_status_view(request, link):
    return render(request, "payments/_status.html", _status_context(link.charge, guest=True))


@_guest
@require_GET
def guest_receipt_view(request, link):
    """CA-02.4: amb el càrrec pagat, el rebut del seu últim pagament. Sense rebut (per exemple,
    un pagament registrat a mà), a la pantalla, que en mostra l'estat."""
    receipt = (
        Receipt.objects.select_related("attempt__charge__department")
        .filter(attempt__charge=link.charge)
        .order_by("-pk")
        .first()
    )
    if receipt is None:
        return redirect("payments:guest_charge")
    return _render_receipt(request, receipt, reverse("payments:guest_charge"), guest=True)


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
