"""«La meva llicència» (vistes v3; T-M06-06 i 08; LC1, «Propi» de LC3; HU-M06-01 i 03). Només
dades inventades."""

import datetime

import pytest
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_PERSONAL
from apps.core.models import Charge
from apps.licences import personal_views, prices, services
from apps.licences.models import Licence

URL = reverse("licences:mine")
PASSWORD = "contrasenya-de-proves-1954"  # noqa: S105 (dada inventada de proves)


@pytest.fixture
def member(monkeypatch):
    state = {"member": True}
    monkeypatch.setattr(services, "is_member", lambda person, on=None: state["member"])
    monkeypatch.setattr(personal_views, "is_member", lambda person, on=None: state["member"])
    return state


@pytest.fixture
def client_of(login_as, make_person):
    def make(first="Marta", last="Soler", email="marta@example.org"):
        account = Account.objects.create_personal(make_person(first, last), email, PASSWORD)
        account.status = Account.Status.ACTIVE
        account.save()
        return account, login_as(account, AREA_PERSONAL)

    return make


@pytest.fixture
def priced(annual, price_setter):
    prices.add_price(annual, federation_cost_cents=9000, non_member_surcharge_cents=2000,
                     valid_from=datetime.date(2020, 1, 1), note="Tarifa inventada",
                     actor=price_setter)  # fmt: skip
    return annual


def test_a_member_sees_the_offer_and_requests_it(client_of, member, priced):
    account, client = client_of()
    html = client.get(URL).content.decode()
    assert "La meva llicència" in html and "90,00 €" in html
    response = client.post(URL, {"d-tipus": priced.pk, "demana": "1"})
    licence = Licence.objects.get(person=account.person)
    assert response.status_code == 302
    assert response["Location"] == reverse("payments:charge", args=[licence.charge_id])
    assert licence.charge.status == Charge.Status.PENDING


def test_a_second_request_shows_the_error(client_of, member, priced):
    _account, client = client_of()
    client.post(URL, {"d-tipus": priced.pk, "demana": "1"})
    html = client.post(URL, {"d-tipus": priced.pk, "demana": "1"}).content.decode()
    assert "Ja tens una llicència d&#x27;aquest tipus en curs." in html
    assert "Sol·licitada: falta pagar-la" in html and "Paga-la" in html


def test_next_year_before_the_opening_is_rejected(client_of, member, priced, monkeypatch):
    _account, client = client_of()
    real = services.business_settings.get

    def fake_get(key, at=None):
        return "12-31" if key == services.NEXT_YEAR_OPENS_ON else real(key, at)

    monkeypatch.setattr(services.business_settings, "get", fake_get)
    html = client.post(URL, {"d-tipus": priced.pk, "d-any_vinent": "on", "demana": "1"}).content
    assert "Encara no es pot demanar la llicència de l&#x27;any vinent." in html.decode()


def test_a_non_member_gets_no_offer_while_the_option_is_off(client_of, member, priced):
    member["member"] = False
    _account, client = client_of()
    assert "no hi ha cap llicència que puguis demanar" in client.get(URL).content.decode()


def test_declare_an_existing_one(client_of, member, priced):
    account, client = client_of()
    data = {"j-tipus": priced.pk, "j-numero": "F-31", "j-venciment": "2099-12-31", "declara": "1"}
    response = client.post(URL, data, follow=True)
    licence = Licence.objects.get(person=account.person)
    assert (licence.origin, licence.status, licence.federation_number) == (
        "external",
        "active",
        "F-31",
    )
    assert "Llicència registrada." in response.content.decode()


def test_an_expired_declaration_shows_the_error(client_of, member, priced):
    _account, client = client_of()
    data = {"j-tipus": priced.pk, "j-numero": "F-31", "j-venciment": "2000-01-01", "declara": "1"}
    html = client.post(URL, data).content.decode()
    assert "La data de la llicència no pot ser passada." in html


def test_only_my_licences(client_of, member, priced, make_licence, make_person):
    make_licence(person=make_person("Altra", "Persona"), federation_number="F-ALTRA",
                 status="active", origin="external", price_kind=None, price_cents=None)  # fmt: skip
    _account, client = client_of()
    html = client.get(URL).content.decode()
    assert "F-ALTRA" not in html and "Encara no tens cap llicència" in html


def test_without_a_session_it_asks_to_log_in(client):
    response = client.get(URL)
    assert response.status_code == 302 and "/entrar/" in response["Location"]


def test_options_on_show_the_non_member_price_and_single_day_types(
    client_of, member, priced, monkeypatch
):
    member["member"] = False
    real = services.business_settings.get
    on = {services.NON_MEMBERS_ENABLED, services.DAY_ENABLED}
    monkeypatch.setattr(
        services.business_settings, "get", lambda key, at=None: True if key in on else real(key, at)
    )
    day = Licence._meta.get_field("licence_type").related_model.objects.create(
        name="Un dia sense preu (inventat)", category="amateur", validity_rule="single_day"
    )
    _account, client = client_of()
    html = client.get(URL).content.decode()
    assert "110,00 €" in html  # no soci: federació + recàrrec
    assert f'value="{day.pk}"' in html  # el tipus d'un dia es pot triar
    assert (
        "<strong>Un dia sense preu (inventat)</strong>" not in html
    )  # però sense preu no s'ofereix


def test_t_m07_36_a_member_can_say_no_when_requesting(client_of, member, priced):
    from apps.website import clients

    account, client = client_of()
    client.post(URL, {"d-tipus": priced.pk, "d-" + clients.FIELD: "on", "demana": "1"})
    assert clients.objected(account.login)
