"""Sessió obligatòria per defecte (RN-40) i separació de les dues entrades (RN-14).

Tota vista exigeix sessió. Una vista pública es declara de manera explícita amb
`django.contrib.auth.decorators.login_not_required`.

Les vistes de l'espai de noms `administration` exigeixen una sessió oberta per l'entrada
d'administració (amb TOTP); la resta, una sessió de l'àrea de socis. Una sessió no serveix
per a l'altra entrada.
"""

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.cache import add_never_cache_headers

from .security import AREA_ADMIN, AREA_PERSONAL
from .sessions import refresh_expiry, session_area_is_valid

ADMIN_NAMESPACE = "administration"
LOGIN_URL_NAMES = {AREA_PERSONAL: "accounts:login", AREA_ADMIN: "administration:login"}


def area_of(request) -> str:
    match = request.resolver_match
    if match and match.namespaces and match.namespaces[0] == ADMIN_NAMESPACE:
        return AREA_ADMIN
    return AREA_PERSONAL


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not getattr(view_func, "login_required", True):
            return None
        area = area_of(request)
        if not session_area_is_valid(request, area):
            return self.handle_no_permission(request, area)
        refresh_expiry(request, area)
        return None

    def handle_no_permission(self, request, area):
        login_url = reverse(LOGIN_URL_NAMES[area])
        # Una petició d'HTMX no ha d'encastar la pàgina d'entrada dins d'un fragment:
        # HTMX llegeix HX-Redirect i porta tota la pàgina a l'entrada.
        if request.headers.get("HX-Request"):
            response = HttpResponse(status=401)
            response["HX-Redirect"] = login_url
            return response
        if session_expired(request):
            # T-M01-38: pàgina «La sessió ha caducat» amb el botó per tornar a entrar. No diu
            # res del compte ni de la pàgina demanada; el «next» és el mateix que abans.
            login_redirect = redirect_to_login(request.get_full_path(), login_url)
            response = render(
                request,
                "accounts/session_expired.html",
                {"area": area, "login_url": login_redirect["Location"]},
                status=401,
            )
            add_never_cache_headers(response)
            return response
        return redirect_to_login(request.get_full_path(), login_url)


def session_expired(request) -> bool:
    """Hi havia una sessió i ja no val: el navegador porta la galeta d'una sessió que ja no
    existeix. Passa quan caduca per inactivitat, quan passen les 8 hores de l'administració
    (`session_area_is_valid` la tanca) i quan es tanquen les sessions d'un compte (contrasenya
    nova, restabliment, rol retirat). Qui no havia entrat mai, o ve de l'altra entrada amb una
    sessió vàlida, va directament a l'entrada, com fins ara."""
    return bool(request.COOKIES.get(settings.SESSION_COOKIE_NAME)) and (
        request.session.session_key is None
    )
