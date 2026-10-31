"""Sessió obligatòria per defecte (RN-40).

Tota vista exigeix sessió. Una vista pública s'ha de declarar de manera explícita
amb `django.contrib.auth.decorators.login_not_required`.
"""

from django.contrib.auth import middleware
from django.http import HttpResponse
from django.shortcuts import resolve_url


class LoginRequiredMiddleware(middleware.LoginRequiredMiddleware):
    def handle_no_permission(self, request, view_func):
        # Una petició d'HTMX no ha d'encastar la pàgina d'entrada dins d'un fragment:
        # HTMX llegeix HX-Redirect i porta tota la pàgina a l'entrada.
        if request.headers.get("HX-Request"):
            response = HttpResponse(status=401)
            response["HX-Redirect"] = resolve_url(self.get_login_url(view_func))
            return response
        return super().handle_no_permission(request, view_func)
