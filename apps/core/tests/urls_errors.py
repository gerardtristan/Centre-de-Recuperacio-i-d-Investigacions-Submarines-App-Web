"""Rutes de prova de les pàgines d'error (T-M01-47): les del projecte i dues vistes que fallen.

Només per a les proves (`@pytest.mark.urls`): cap configuració real les inclou.
"""

from django.contrib.auth.decorators import login_not_required
from django.http import Http404
from django.urls import path

from config.urls import urlpatterns as project_urlpatterns

INTERNAL_DETAIL = "detall-intern-que-no-ha-de-sortir"


@login_not_required
def broken(request):
    raise RuntimeError(INTERNAL_DETAIL)


@login_not_required
def missing(request):
    raise Http404(INTERNAL_DETAIL)


urlpatterns = [
    path("prova-error-500/", broken, name="prova_error_500"),
    path("prova-no-trobat/", missing, name="prova_no_trobat"),
    *project_urlpatterns,
]
