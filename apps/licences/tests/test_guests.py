"""Llicència per a una persona de fora (T-M06-07b; P-M06-C, passos 3 i 4; RN-M06-03 i 04; decisió
021). Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.core import business_settings
from apps.core.models import Consent, GuestLink, LegalText, OutgoingEmail, Person
from apps.licences import guests, prices, services
from apps.licences.models import Licence

D = datetime.date
TODAY = D(2027, 3, 15)
URL = reverse("licences:guest_request")
EMAIL = "mar.convidada@example.org"


@pytest.fixture
def options(monkeypatch):
    values = {services.NON_MEMBERS_ENABLED: True}
    real_get = business_settings.get
    monkeypatch.setattr(
        business_settings, "get", lambda key, at=None: values.get(key, real_get(key, at))
    )
    return values


@pytest.fixture
def privacy(db):
    if not LegalText.objects.filter(kind="privacy").exists():
        LegalText.objects.create(kind="privacy", version=1, content="Política inventada.")


@pytest.fixture
def priced(annual, price_setter):
    prices.add_price(
        annual,
        federation_cost_cents=9000,
        non_member_surcharge_cents=2000,
        valid_from=D(2020, 1, 1),
        note="Tarifa inventada",
        actor=price_setter,
    )
    return annual


def data(**fields):
    values = {
        "first_name": "Mar",
        "last_name": "Convidada",
        "contact_email": EMAIL,
        "birth_date": D(1990, 5, 1),
        "accept_privacy": True,
    }
    values.update(fields)
    return values


def test_a_guest_gets_a_requested_licence_at_the_non_member_price_and_a_payment_link(
    options, privacy, priced
):
    licence = guests.request_as_guest(priced, data(), today=TODAY)
    assert (licence.status, licence.price_kind, licence.price_cents) == (
        "requested",
        "non_member",
        11000,
    )
    assert licence.charge.amount_cents == 11000 and licence.charge.status == "pending"
    person = licence.person
    assert person.origin == Person.Origin.GUEST and not hasattr(person, "account")
    assert Consent.objects.filter(person=person, legal_text__kind="privacy").exists()
    assert GuestLink.objects.filter(charge=licence.charge).count() == 1
    assert OutgoingEmail.objects.filter(template="enllac-convidat", to_address=EMAIL).exists()


def test_without_the_recipient_quota_no_link_is_sent(options, privacy, priced):
    licence = guests.request_as_guest(priced, data(), today=TODAY, send_link=False)
    assert not GuestLink.objects.filter(charge=licence.charge).exists()


def test_disabled_or_without_privacy_text_nothing_is_created(options, priced, db):
    with pytest.raises(ValidationError):  # cap política de privacitat vigent
        guests.request_as_guest(priced, data(), today=TODAY)
    options[services.NON_MEMBERS_ENABLED] = False
    with pytest.raises(services.NonMembersDisabled):
        guests.request_as_guest(priced, data(), today=TODAY)
    assert not Licence.objects.exists() and not Person.objects.filter(origin="guest").exists()


@pytest.mark.parametrize(
    "fields",
    [
        {"first_name": ""},
        {"contact_email": ""},
        {"birth_date": None},
        {"accept_privacy": False},
        {"birth_date": D(2010, 1, 1)},
        {"birth_date": D(2030, 1, 1)},
    ],
)
def test_minimum_data_adults_only_and_privacy(options, privacy, priced, fields):
    with pytest.raises(ValidationError):
        guests.request_as_guest(priced, data(**fields), today=TODAY)
    assert not Licence.objects.exists()


def test_the_page_is_not_found_while_disabled(client, db):
    assert client.get(URL).status_code == 404


def test_the_form_sends_and_answers_the_same_for_a_known_email(client, options, privacy, priced):
    post = {
        "tipus": priced.pk,
        "first_name": "Mar",
        "last_name": "Convidada",
        "contact_email": EMAIL,
        "birth_date": "1990-05-01",
        "accept_privacy": "on",
    }
    assert "Política inventada." in client.get(URL).content.decode()
    first = client.post(URL, post)
    assert first.status_code == 303
    assert "Sol·licitud enviada" in client.get(URL).content.decode()
    second = client.post(URL, post)  # el mateix correu: la mateixa resposta
    assert second.status_code == 303
    assert Licence.objects.filter(status="requested").count() == 2


def test_the_form_shows_the_errors(client, options, privacy, priced):
    post = {
        "tipus": priced.pk,
        "first_name": "Nen",
        "last_name": "Menor",
        "contact_email": "nen@example.org",
        "birth_date": "2015-01-01",
        "accept_privacy": "on",
    }
    html = client.post(URL, post).content.decode()
    assert "menors d&#x27;edat" in html or "menors d'edat" in html
    assert not Licence.objects.exists()


def test_t_m07_36_the_box_to_say_no_is_recorded(client, options, privacy, priced):
    from apps.website import clients

    post = {"tipus": priced.pk, "first_name": "Mar", "last_name": "Convidada",
            "contact_email": EMAIL, "birth_date": "1990-05-01", "accept_privacy": "on"}  # fmt: skip
    assert (
        "No vull rebre informació d&#x27;activitats del C.R.I.S."
        in client.get(URL).content.decode()
    )
    client.post(URL, post)
    assert not clients.objected(EMAIL)
    client.post(URL, {**post, clients.FIELD: "on"})
    assert clients.objected(EMAIL)
