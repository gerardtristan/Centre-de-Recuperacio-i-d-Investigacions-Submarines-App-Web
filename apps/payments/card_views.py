"""`/socis/pagaments/targeta/`: guardar una targeta per a les quotes (T-M05a-12; P-M05a-D;
RN-M05a-10 i 12; CA-M05a-15; wireframe `socis.html#pagaments-targeta`).

- Només el soci de la sessió (cap identificador a la ruta), com la pàgina del mandat; si el
  proveïdor no guarda targetes, «no trobat» (CA-M05a-01, L-M05a-09).
- La targeta s'escriu a la pàgina del proveïdor; aquí no arriba cap número. La tornada del
  navegador no guarda res: només diu que s'espera la confirmació del proveïdor.
- Sessió recent (RN-M05a-12): la contrasenya, i el codi si el compte té TOTP, com per al mandat.
"""

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from apps.accounts import reauth

from . import cards, preferences
from .forms import RecentAuthForm
from .mandate_views import _own_member, _reauth_error
from .models import FeeMethod
from .providers.base import ProviderError


@sensitive_post_parameters("password", "code")
@never_cache
@require_http_methods(["GET", "POST"])
def saved_card_view(request):
    member, account = _own_member(request), request.user
    if FeeMethod.SAVED_CARD not in preferences.offered_methods():
        raise Http404
    minutes = settings.MANDATE_REAUTH_MINUTES
    form = RecentAuthForm(
        request.POST if request.method == "POST" else None,
        has_totp=account.has_totp,
        ask_password=not reauth.is_recent(request, minutes),
    )
    error = None
    if request.method == "POST" and form.is_valid():
        if _reauth_error(request, form, minutes) is None:
            try:
                return redirect(cards.start_setup(member, account))
            except ProviderError:
                error = _("Ara no es pot guardar la targeta. Torna-ho a provar més tard.")
        form.data = form.data.copy()
        form.data.pop("code", None)
    back = request.GET.get("tornada")
    context = {
        "card": preferences.active_card(member),
        "form": form,
        "waiting": back == "ok" and cards.waiting(member.person),
        "not_saved": back == "ko",
        "error": error,
    }
    return render(request, "payments/saved_card.html", context)


@sensitive_post_parameters("password", "code")
@never_cache
@require_http_methods(["GET", "POST"])
def saved_card_remove_view(request):
    """«Esborra la targeta» (T-M05a-12c; P-132, opció A): com «Revoca el mandat», confirmació i,
    si la sessió no és recent, la contrasenya (i el codi si el compte té TOTP). Funciona encara que
    el proveïdor ja no guardi targetes. Sense targeta activa no hi ha res a esborrar."""
    member, account = _own_member(request), request.user
    card = preferences.active_card(member)
    if card is None:
        return redirect("payments:fee_method")
    minutes = settings.MANDATE_REAUTH_MINUTES
    form = RecentAuthForm(
        # Amb la sessió recent, el POST no porta cap camp: el formulari ha d'estar lligat igualment.
        request.POST if request.method == "POST" else None,
        has_totp=account.has_totp,
        ask_password=not reauth.is_recent(request, minutes),
    )
    if request.method == "POST" and form.is_valid():
        if _reauth_error(request, form, minutes) is None:
            cards.remove_card(member, by=account)
            messages.success(
                request,
                _(
                    "Targeta acabada en %(last4)s esborrada. A partir d'ara pagaràs cada quota "
                    "amb targeta, Bizum o transferència quan es generi."
                )
                % {"last4": card.last4},
            )
            return redirect("payments:fee_method")
        form.data = form.data.copy()
        form.data.pop("code", None)
    return render(request, "payments/saved_card_remove.html", {"card": card, "form": form})
