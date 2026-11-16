"""Pantalles «En construcció» (T-DX-03; design-system §6.9; P-90, resposta C).

- Només GET: cap mètode que escrigui no arriba mai a la vista.
- Amb SHOW_UNDER_CONSTRUCTION encès (local, proves), tothom les veu; apagat (producció), només un
  compte d'administrador amb el permís core.under_construction.view. Sense accés, 404.
- Prova comuna: totes les rutes marcades amb el decorador, a tota la plataforma, només accepten GET.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from django.test import RequestFactory, override_settings
from django.urls import URLPattern, URLResolver, get_resolver

from apps.core.models import Role, RolePermission
from apps.core.permission_catalog import CATALOG
from apps.core.under_construction import PERMISSION, under_construction

R = Role.Code
WRITE_METHODS = ("post", "put", "patch", "delete")


@under_construction
def sample(request):
    return HttpResponse("exemple")


def call(method, user):
    request = getattr(RequestFactory(), method)("/en-construccio/")
    request.user = user
    return sample(request)


@override_settings(SHOW_UNDER_CONSTRUCTION=True)
@pytest.mark.parametrize("method", WRITE_METHODS)
def test_no_write_method_reaches_the_view(method):
    assert call(method, AnonymousUser()).status_code == 405


@override_settings(SHOW_UNDER_CONSTRUCTION=True)
def test_with_the_setting_on_everyone_sees_it():
    assert call("get", AnonymousUser()).status_code == 200


@override_settings(SHOW_UNDER_CONSTRUCTION=False)
@pytest.mark.django_db
def test_with_the_setting_off_only_admins_with_the_permission_see_it(make_admin):
    with pytest.raises(Http404):
        call("get", AnonymousUser())
    secretary = make_admin(R.SECRETARY)
    with pytest.raises(Http404):
        call("get", secretary)  # cap rol no comença amb el permís (P-90)
    RolePermission.objects.create(
        role=Role.objects.get(code=R.SECRETARY), permission_code=PERMISSION, scope="all"
    )
    assert call("get", secretary).status_code == 200


def test_the_permission_starts_without_any_role():
    assert CATALOG[PERMISSION].initial == {}


def test_the_label_is_translatable_text_with_an_id():
    html = render_to_string("_en_construccio.html", {"id": "ec-prova"})
    assert 'class="en-construccio"' in html and 'id="ec-prova"' in html
    assert "En construcció" in html and "style=" not in html


def _views(patterns):
    for entry in patterns:
        if isinstance(entry, URLResolver):
            yield from _views(entry.url_patterns)
        elif isinstance(entry, URLPattern):
            yield entry


@override_settings(SHOW_UNDER_CONSTRUCTION=True)
def test_every_under_construction_route_only_accepts_get():
    marked = [
        p
        for p in _views(get_resolver().url_patterns)
        if getattr(p.callback, "under_construction", False)
    ]
    for pattern in marked:
        for method in WRITE_METHODS:
            request = getattr(RequestFactory(), method)("/")
            request.user = AnonymousUser()
            assert pattern.callback(request).status_code == 405, (pattern.name, method)
