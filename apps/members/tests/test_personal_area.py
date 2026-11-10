"""Àrea del soci amb el compte personal (T-M01-16; P12, P13; CA-M01-12, CA-M01-25; 061).

Perfil (telèfon, adreça i llengua, amb registre del valor anterior), les meves quotes i el detall
d'una quota pròpia; tot surt de la persona de la sessió. Només dades inventades.
"""

from datetime import UTC, date, datetime

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY
from apps.core import audit, charges, persons
from apps.core.models import AuditEntry, Charge, Payment, Person
from apps.members.models import AnnualFee, Member, MemberRequest, MembershipType
from conftest import PASSWORD

PROFILE = "members:profile"
FEES = "members:fees"
DETAIL = "members:fee_detail"
UPDATED = audit.Action.PROFILE_UPDATED
NOT_FOUND = audit.Action.PERSONAL_AREA_NOT_FOUND
TWO_LANGUAGES = [("ca", "Català"), ("es", "Castellano")]


def make_person(first, email_hint, **fields):
    defaults = {
        "last_name": "Prova",
        "origin": Person.Origin.WEB,
        "phone": "600000001",
        "address": "Carrer Inventat 1",
        "id_document_type": Person.DocumentType.DNI,
        "id_document_number": f"0000000{email_hint}",
    }
    return Person.objects.create(first_name=first, **{**defaults, **fields})


def make_account(person, email):
    account = Account.objects.create_personal(person, email, PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    return account


def make_member(person, number):
    return Member.objects.create(
        person=person,
        member_number=number,
        type=MembershipType.objects.get(code="full"),
        status=Member.Status.ACTIVE,
        joined_on=date(2019, 3, 12),
    )


def add_fee(member, concept, *, period=2026, cents=9000):
    charge = charges.create_charge(
        member.person,
        kind=Charge.Kind.FEE,
        amount_cents=cents,
        concept=concept,
        origin="members",
        by=audit.system("proves"),
    )
    return AnnualFee.objects.create(
        member=member,
        period=period,
        kind=AnnualFee.Kind.ANNUAL,
        charge=charge,
        due_on=date(period, 1, 1),
    )


def pay(fee, paid_at, *, amount=None):
    payment = Payment.objects.create(
        charge=fee.charge,
        method=Payment.Method.CARD,
        amount_cents=amount or fee.charge.amount_cents,
        paid_at=paid_at,
    )
    if amount is None:
        charges.mark_paid(fee.charge, payment, origin="provider", by=audit.system("proves"))
    return payment


@pytest.fixture
def anna(db):
    person = make_person("Anna", "1T", id_document_number="12345678Z")
    return make_account(person, "anna.soci@example.org")


@pytest.fixture
def other(db):
    """Un altre soci, amb dades sentinella: no han de sortir mai a l'àrea de l'Anna."""
    person = make_person("Sentinella", "2R", phone="699999999", address="Carrer Sentinella 9")
    account = make_account(person, "sentinella@example.org")
    member = make_member(person, 1999)
    return account, member


@pytest.fixture
def client_for(login_as):
    return lambda account: login_as(account, AREA_PERSONAL)


def entries(action):
    return AuditEntry.objects.filter(action=action).order_by("id")


# --- Accés -----------------------------------------------------------------------------------


@pytest.mark.parametrize("name,args", [(PROFILE, []), (FEES, []), (DETAIL, [1])])
def test_without_session_goes_to_the_personal_login(client, db, name, args):
    response = client.get(reverse(name, args=args))
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))


def test_admin_session_does_not_enter_the_personal_area(login_as, admin_account):
    client = login_as(admin_account, AREA_ADMIN)
    response = client.get(reverse(PROFILE))
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))


def test_session_expired_on_save_changes_nothing(client, anna):
    response = client.post(reverse(PROFILE), {"phone": "611111111", "address": ""})
    assert response.status_code == 302
    anna.person.refresh_from_db()
    assert anna.person.phone == "600000001"
    assert not entries(UPDATED).exists()


def test_profile_post_needs_csrf(anna):
    client = Client(enforce_csrf_checks=True)
    client.force_login(anna)
    session = client.session
    session[AREA_SESSION_KEY] = AREA_PERSONAL
    session.save()
    response = client.post(reverse(PROFILE), {"phone": "611111111"})
    assert response.status_code == 403
    anna.person.refresh_from_db()
    assert anna.person.phone == "600000001"


# --- Perfil: veure ---------------------------------------------------------------------------


def test_profile_shows_only_own_data_with_masked_document(client_for, anna, other):
    make_member(anna.person, 427)
    html = client_for(anna).get(reverse(PROFILE)).content.decode()
    assert "Anna Prova" in html
    assert "·····678Z" in html
    assert "12345678Z" not in html
    assert "427" in html
    assert "anna.soci@example.org" in html
    for leak in ("Sentinella", "699999999", "Carrer Sentinella 9", "1999", "000000002R"):
        assert leak not in html


def test_profile_response_is_not_cached(client_for, anna):
    response = client_for(anna).get(reverse(PROFILE))
    assert "no-store" in response["Cache-Control"]


def test_person_without_member_has_a_profile_without_number(client_for, anna):
    response = client_for(anna).get(reverse(PROFILE))
    assert response.status_code == 200
    assert "Número de soci" not in response.content.decode()


def test_profile_lists_only_own_requests(client_for, anna, other):
    MemberRequest.objects.create(
        kind=MemberRequest.Kind.JOIN,
        person=anna.person,
        requested_type=MembershipType.objects.get(code="full"),
        channel=MemberRequest.Channel.WEB,
        birth_date=date(1990, 1, 1),
    )
    MemberRequest.objects.create(
        kind=MemberRequest.Kind.LEAVE,
        person=other[1].person,
        member=other[1],
        channel=MemberRequest.Channel.WEB,
        request_reason="Motiu sentinella",
    )
    html = client_for(anna).get(reverse(PROFILE)).content.decode()
    assert "Alta" in html and "Pendent" in html
    assert "Baixa" not in html
    assert "Motiu sentinella" not in html


def test_profile_without_requests_says_so(client_for, anna):
    assert "No tens cap sol·licitud." in client_for(anna).get(reverse(PROFILE)).content.decode()


# --- Perfil: editar (HU-M01-08, registre amb el valor anterior) ------------------------------


def test_member_updates_phone_and_address_with_audit(client_for, anna):
    client = client_for(anna)
    response = client.post(
        reverse(PROFILE), {"phone": "+34 611-11.11.11", "address": "Carrer Nou 2"}
    )
    assert response.status_code == 302
    assert response["Location"] == reverse(PROFILE)
    person = Person.objects.get(pk=anna.person.pk)
    assert person.phone == "+34611111111"
    assert person.address == "Carrer Nou 2"
    logged = {e.field: e for e in entries(UPDATED)}
    assert set(logged) == {"phone", "address"}
    assert logged["phone"].old_value == "600000001"
    assert logged["phone"].new_value == "+34611111111"
    assert logged["address"].old_value == "Carrer Inventat 1"
    for entry in logged.values():
        assert entry.actor_account == anna
        assert entry.target_type == "core.person"
        assert entry.target_id == str(person.pk)
    assert "Canvis desats." in client.get(reverse(PROFILE)).content.decode()


def test_saving_without_changes_leaves_no_entry(client_for, anna):
    client = client_for(anna)
    client.post(reverse(PROFILE), {"phone": "600000001", "address": "Carrer Inventat 1"})
    assert not entries(UPDATED).exists()
    assert "No has canviat cap dada." in client.get(reverse(PROFILE)).content.decode()


def test_address_can_be_emptied(client_for, anna):
    client_for(anna).post(reverse(PROFILE), {"phone": "600000001", "address": ""})
    anna.person.refresh_from_db()
    assert anna.person.address == ""


@pytest.mark.parametrize("phone", ["", "123", "abc"])
def test_invalid_phone_is_rejected_and_nothing_changes(client_for, anna, phone):
    response = client_for(anna).post(reverse(PROFILE), {"phone": phone, "address": "X"})
    assert response.status_code == 200
    assert 'aria-invalid="true"' in response.content.decode()
    anna.person.refresh_from_db()
    assert anna.person.phone == "600000001"
    assert anna.person.address == "Carrer Inventat 1"
    assert not entries(UPDATED).exists()


def test_fields_outside_the_form_are_ignored(client_for, anna):
    """El nom, el document, el correu i la persona no es poden canviar des del perfil, encara
    que la petició els porti (manipulada)."""
    client_for(anna).post(
        reverse(PROFILE),
        {
            "phone": "600000001",
            "address": "Carrer Inventat 1",
            "first_name": "Manipulat",
            "id_document_number": "99999999R",
            "contact_email": "manipulat@example.org",
            "login": "manipulat@example.org",
            "person": "999",
        },
    )
    person = Person.objects.get(pk=anna.person.pk)
    assert person.first_name == "Anna"
    assert person.id_document_number == "12345678Z"
    assert person.contact_email == ""
    assert Account.objects.get(pk=anna.pk).login == "anna.soci@example.org"
    assert not entries(UPDATED).exists()


def test_member_cannot_edit_another_person_through_the_form(client_for, anna, other):
    client_for(anna).post(reverse(PROFILE), {"phone": "611111111", "address": "", "pk": "1"})
    other_person = Person.objects.get(pk=other[1].person.pk)
    assert other_person.phone == "699999999"
    assert other_person.address == "Carrer Sentinella 9"


# --- Llengua preferida (061) -----------------------------------------------------------------


def test_language_selector_hidden_with_one_active_language(client_for, anna):
    client = client_for(anna)
    assert 'name="preferred_language"' not in client.get(reverse(PROFILE)).content.decode()
    client.post(
        reverse(PROFILE),
        {"phone": "600000001", "address": "Carrer Inventat 1", "preferred_language": "es"},
    )
    anna.person.refresh_from_db()
    assert anna.person.preferred_language == "ca"
    assert not entries(UPDATED).exists()


@override_settings(LANGUAGES=TWO_LANGUAGES)
def test_language_selector_shown_and_saved_with_two_active_languages(client_for, anna):
    client = client_for(anna)
    assert 'name="preferred_language"' in client.get(reverse(PROFILE)).content.decode()
    client.post(
        reverse(PROFILE),
        {"phone": "600000001", "address": "Carrer Inventat 1", "preferred_language": "es"},
    )
    anna.person.refresh_from_db()
    assert anna.person.preferred_language == "es"
    entry = entries(UPDATED).get()
    assert (entry.field, entry.old_value, entry.new_value) == ("preferred_language", "ca", "es")


@override_settings(LANGUAGES=TWO_LANGUAGES)
def test_inactive_language_is_rejected(client_for, anna):
    response = client_for(anna).post(
        reverse(PROFILE),
        {"phone": "600000001", "address": "Carrer Inventat 1", "preferred_language": "fr"},
    )
    assert response.status_code == 200
    anna.person.refresh_from_db()
    assert anna.person.preferred_language == "ca"


def test_service_rejects_fields_outside_the_profile(anna):
    with pytest.raises(ValueError):
        persons.update_profile(anna.person, actor=anna, first_name="Manipulat")
    with pytest.raises(ValueError):
        persons.update_profile(anna.person, actor=anna, preferred_language="fr")
    assert Person.objects.get(pk=anna.person.pk).first_name == "Anna"
    assert not entries(UPDATED).exists()


# --- Les meves quotes (CA-M01-12, L-M01-09) --------------------------------------------------


def test_fees_page_lists_only_own_fees_with_state(client_for, anna, other):
    member = make_member(anna.person, 427)
    paid = add_fee(member, "Quota pròpia pagada", period=2025)
    pay(paid, datetime(2025, 3, 10, 10, tzinfo=UTC))
    add_fee(member, "Quota pròpia pendent", period=2026)
    add_fee(other[1], "Quota sentinella")
    html = client_for(anna).get(reverse(FEES)).content.decode()
    assert "Quota pròpia pagada" in html and "Pagada el 10/03/2025" in html
    assert "Quota pròpia pendent" in html and "Pendent" in html
    assert "90,00 €" in html
    assert "Quota sentinella" not in html


def test_fees_page_shows_the_fee_state_of_t_m01_15(client_for, anna):
    member = make_member(anna.person, 427)
    pay(add_fee(member, "Quota"), datetime(2026, 2, 3, 10, tzinfo=UTC))
    html = client_for(anna).get(reverse(FEES)).content.decode()
    assert "Pagada fins al 03/02/2027" in html


def test_partial_payment_has_no_invented_state(client_for, anna):
    """Pagaments parcials (P-61): ni «pagada fins al» ni cap import pendent calculat."""
    member = make_member(anna.person, 427)
    fee = add_fee(member, "Quota en tres pagaments", cents=9600)
    pay(fee, datetime(2026, 2, 3, 10, tzinfo=UTC), amount=3200)
    html = client_for(anna).get(reverse(FEES)).content.decode()
    assert "Pagada fins al" not in html
    assert "Sense dades de quota" in html
    assert "64,00" not in html


def test_member_without_fees_sees_the_empty_message(client_for, anna):
    make_member(anna.person, 427)
    html = client_for(anna).get(reverse(FEES)).content.decode()
    assert "Encara no tens cap quota." in html


def test_person_without_member_gets_not_found_for_fees(client_for, anna):
    assert client_for(anna).get(reverse(FEES)).status_code == 404


def test_no_receipt_is_offered(client_for, anna):
    """El rebut amb número és del 05b (RN-M05b-19): cap botó que encara no funcioni."""
    member = make_member(anna.person, 427)
    fee = add_fee(member, "Quota")
    pay(fee, datetime(2026, 2, 3, 10, tzinfo=UTC))
    client = client_for(anna)
    for url in (reverse(FEES), reverse(DETAIL, args=[fee.pk])):
        html = client.get(url).content.decode().lower()
        assert "rebut" not in html and "justificant" not in html


# --- Detall d'una quota i CA-M01-25 ----------------------------------------------------------


def test_own_fee_detail(client_for, anna):
    member = make_member(anna.person, 427)
    fee = add_fee(member, "Quota pròpia")
    pay(fee, datetime(2026, 2, 3, 10, tzinfo=UTC))
    response = client_for(anna).get(reverse(DETAIL, args=[fee.pk]))
    assert response.status_code == 200
    html = response.content.decode()
    assert "Quota pròpia" in html and "Targeta" in html and "Pagada el 03/02/2026" in html
    assert not entries(NOT_FOUND).exists()


def test_other_members_fee_is_not_found_and_logged(client_for, anna, other):
    make_member(anna.person, 427)
    foreign = add_fee(other[1], "Quota sentinella")
    client = client_for(anna)
    response = client.get(reverse(DETAIL, args=[foreign.pk]))
    missing = client.get(reverse(DETAIL, args=[foreign.pk + 1000]))
    assert response.status_code == missing.status_code == 404
    assert response.content == missing.content
    assert "Quota sentinella" not in response.content.decode()
    logged = list(entries(NOT_FOUND))
    assert len(logged) == 2
    assert logged[0].actor_account == anna
    assert (logged[0].target_type, logged[0].target_id) == ("members.annualfee", str(foreign.pk))
    assert logged[0].details == {"object": "members.annualfee", "id": foreign.pk}
    assert logged[1].target_id == ""
    assert logged[1].details["id"] == foreign.pk + 1000


def test_non_member_asking_for_a_fee_is_not_found_and_logged(client_for, anna, other):
    foreign = add_fee(other[1], "Quota sentinella")
    assert client_for(anna).get(reverse(DETAIL, args=[foreign.pk])).status_code == 404
    assert entries(NOT_FOUND).count() == 1


def test_personal_session_does_not_open_the_admin_record(client_for, anna, other):
    """L'altra via per URL: la fitxa de l'administració no s'obre amb el compte personal."""
    response = client_for(anna).get(reverse("administration:member_detail", args=[other[1].pk]))
    assert response.status_code == 302
    assert "Sentinella" not in response.content.decode()


# --- Navegació ------------------------------------------------------------------------------


def test_navigation_for_a_member(client_for, anna):
    make_member(anna.person, 427)
    html = client_for(anna).get(reverse(PROFILE)).content.decode()
    assert f'href="{reverse(PROFILE)}" aria-current="page"' in html
    assert f'href="{reverse(FEES)}"' in html


def test_navigation_without_member_has_no_fees_link(client_for, anna):
    html = client_for(anna).get(reverse("core:home")).content.decode()
    assert f'href="{reverse(PROFILE)}"' in html
    assert f'href="{reverse(FEES)}"' not in html


def test_navigation_has_no_links_to_pages_not_built_yet(client_for, anna):
    make_member(anna.person, 427)
    html = client_for(anna).get(reverse(PROFILE)).content.decode()
    # El carnet (T-M01-19), el canvi de tipus i la baixa (T-M01-17) ja hi són, i l'esborrat
    # (peça mínima de la T-M01-22); descarregar les dades encara no.
    assert "Descarrega les meves dades" not in html


def test_no_navigation_on_the_login_page(client, db):
    assert reverse(PROFILE) not in client.get(reverse("accounts:login")).content.decode()
