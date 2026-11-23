"""Revisió final dels permisos del 06 a totes les vistes i serveis (T-M06-25; CA-M06-16 i 33;
CA-RP-13; RN-RP-22). Cada vista d'administració, per a cada rol: «no trobat» si i només si el rol
no té el permís a la matriu vigent (que la prova per cel·la de `core` compara amb la 059). Els
serveis amb actor comproven el mateix permís que la vista. Només dades inventades."""

import datetime

import pytest
from django.http import Http404
from django.urls import reverse

from apps.core.models import Role
from apps.core.permissions import has_perm
from apps.core.tests.test_guest_links import admin_client
from apps.licences import prices

pytestmark = pytest.mark.django_db
R = Role.Code
D = datetime.date

# (nom de la ruta, mètode, permís, escriure, necessita una llicència pagada)
VIEWS = [
    ("administration:licences", "get", "licences.list", False, False),
    ("administration:licences_prices", "get", "licences.prices", False, False),
    ("administration:licences_prices", "post", "licences.prices", True, False),
    ("administration:licences_export", "post", "licences.file", True, False),
    ("administration:licences_file", "post", "licences.file", True, True),
    ("administration:licences_activate", "get", "licences.file", True, True),
]


@pytest.mark.parametrize("role", list(R))
@pytest.mark.parametrize(("name", "method", "code", "write", "needs_licence"), VIEWS)
def test_each_admin_view_follows_the_matrix(
    make_admin,
    make_licence,
    role,
    name,
    method,
    code,
    write,
    needs_licence,
):
    account = make_admin(role)
    args = [make_licence(status="paid").pk] if needs_licence else []
    response = getattr(admin_client(account), method)(reverse(name, args=args))
    allowed = has_perm(account, code, write=write)
    assert (response.status_code == 404) is (not allowed), (role, name, method)


def test_without_the_admin_area_every_view_is_closed(client, make_licence):
    licence = make_licence(status="paid")
    for name, method, _code, _write, needs_licence in VIEWS:
        args = [licence.pk] if needs_licence else []
        response = getattr(client, method)(reverse(name, args=args))
        assert response.status_code in (302, 404), name


def test_the_personal_page_needs_a_session(client):
    response = client.get(reverse("licences:mine"))
    assert response.status_code == 302


@pytest.mark.parametrize("role", [R.SECRETARY, R.COURSES_MANAGER, R.BOARD, R.INSTRUCTOR])
def test_a_price_without_lc8_is_not_found_in_the_service(make_admin, annual, role):
    # Error trobat a la T-M06-25: la vista ho comprovava, però el servei no.
    with pytest.raises(Http404):
        prices.add_price(
            annual, federation_cost_cents=9000, non_member_surcharge_cents=2000,
            valid_from=D(2027, 1, 1), note="Prova", actor=make_admin(role),
        )  # fmt: skip
    assert not annual.prices.exists()
