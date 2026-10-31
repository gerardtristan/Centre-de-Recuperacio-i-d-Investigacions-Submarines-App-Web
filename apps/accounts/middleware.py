"""Sessió obligatòria per defecte (RN-40) i separació de les dues entrades (RN-14).

Tota vista exigeix sessió. Una vista pública es declara de manera explícita amb
`django.contrib.auth.decorators.login_not_required`.

Les vistes de l'espai de noms `administration` exigeixen una sessió oberta per l'entrada
d'administració (amb TOTP); la resta, una sessió de l'àrea de socis. Una sessió no serveix
per a l'altra entrada.
"""

from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.urls import reverse

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
        return redirect_to_login(request.get_full_path(), login_url)
