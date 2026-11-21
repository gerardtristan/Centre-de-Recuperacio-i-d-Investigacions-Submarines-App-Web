"""Vistes v2 del 06: tipus i preus (T-M06-02; P-M06-A; LC8; CA-M06-04, 05 i 21). Només dades
inventades."""

import pytest
from django.http import Http404
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.models import AuditEntry, OutgoingEmail, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.licences import types
from apps.licences.models import LicencePrice, LicenceType

R = Role.Code
URL = reverse("administration:licences_prices")
PRICE = {"p-tipus": "", "p-federacio": "90,00", "p-recarrec": "20,00", "p-des_de": "2026-01-01",
         "p-nota": "Tarifa de la federació (inventada)", "nou_preu": "1"}  # fmt: skip


@pytest.fixture
def as_role(login_as, make_admin):  # noqa: F811
    def login(role):
        return login_as(make_admin(role), AREA_ADMIN)

    return login


def test_the_treasurer_adds_a_price_and_the_page_shows_it(as_role, annual):
    client = as_role(R.TREASURER)
    response = client.post(URL, {**PRICE, "p-tipus": annual.pk})
    assert response.status_code == 302
    price = LicencePrice.objects.get()
    assert (price.federation_cost_cents, price.non_member_surcharge_cents) == (9000, 2000)
    html = main_of(client.get(URL).content.decode())
    assert "90,00" in html and "110,00" in html and "Tarifa de la federació (inventada)" in html


def test_ca_m06_05_a_price_without_a_note_is_rejected(as_role, annual):
    response = as_role(R.TREASURER).post(URL, {**PRICE, "p-tipus": annual.pk, "p-nota": ""})
    assert response.status_code == 200 and not LicencePrice.objects.exists()


def test_ca_m06_04_there_is_no_member_price_field(as_role):
    assert 'name="p-soci"' not in as_role(R.TREASURER).get(URL).content.decode()


def test_a_service_error_is_shown_on_the_form(as_role, annual, monkeypatch):
    from django.core.exceptions import ValidationError

    from apps.licences import prices

    def broken(*args, **kwargs):
        raise ValidationError("Error inventat del servei")

    monkeypatch.setattr(prices, "add_price", broken)
    response = as_role(R.TREASURER).post(URL, {**PRICE, "p-tipus": annual.pk})
    assert "Error inventat del servei" in response.content.decode()


def test_create_and_deactivate_a_type(as_role):
    client = as_role(R.PRESIDENT)
    data = {"t-nom": "Tècnic anual (inventat)", "t-categoria": "technical",
            "t-durada": "calendar_year", "nou_tipus": "1"}  # fmt: skip
    assert client.post(URL, data).status_code == 302
    licence_type = LicenceType.objects.get()
    assert client.post(URL, {"tipus": licence_type.pk, "actiu": "0"}).status_code == 302
    licence_type.refresh_from_db()
    assert not licence_type.active
    client.post(URL, {"tipus": licence_type.pk, "actiu": "1"})
    licence_type.refresh_from_db()
    assert licence_type.active
    assert AuditEntry.objects.filter(action=types.ACTION_ACTIVE).count() == 2


def test_ca_m06_21_no_single_day_type_while_disabled(as_role):
    data = {"t-nom": "Un dia (inventat)", "t-categoria": "amateur", "t-durada": "single_day",
            "nou_tipus": "1"}  # fmt: skip
    response = as_role(R.ADMINISTRATOR).post(URL, data)
    assert "La llicència d&#x27;un dia no està activada." in response.content.decode()
    assert not LicenceType.objects.exists()


def test_the_board_only_reads(as_role, annual):
    client = as_role(R.BOARD)
    html = main_of(client.get(URL).content.decode())
    assert annual.name in html and "Desa el preu" not in html and "Desactiva" not in html
    assert client.post(URL, {**PRICE, "p-tipus": annual.pk}).status_code == 404
    assert not LicencePrice.objects.exists() and not OutgoingEmail.objects.exists()


@pytest.mark.parametrize("role", [R.SECRETARY, R.INSTRUCTOR, R.COURSES_MANAGER])
def test_without_lc8_not_found(as_role, role):
    assert as_role(role).get(URL).status_code == 404


def test_the_type_services_check_the_permission(make_admin, annual):  # noqa: F811
    board = make_admin(R.BOARD)
    with pytest.raises(Http404):
        types.create_type(name="X", category="amateur", validity_rule="days_365", actor=board)
    with pytest.raises(Http404):
        types.set_active(annual, False, actor=board)
