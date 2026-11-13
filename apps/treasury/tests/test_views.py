"""Pantalles de tresoreria, primer tall de la T-M04-15 (C1 i C8 de M04-3; T1 de M04-4; CA-T02.1,
CA-T06.1, LT13; RN-T02, RN-T03, RNF-T4). Només lectura. Només dades inventades."""

import re
import time
from datetime import date

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core.models import Department, Role
from apps.core.tests.conftest import (
    main_of,
    make_admin,  # noqa: F401 (fixture)
)
from apps.treasury.balances import balances
from apps.treasury.models import CostCentre, Movement, TreasuryAccount
from apps.treasury.tests.test_record_income import PAID_AT, new_transit, paid, record

pytestmark = pytest.mark.django_db
ACCOUNTS = reverse("administration:treasury_accounts")
MOVEMENTS = reverse("administration:treasury_movements")
ROUTES = (ACCOUNTS, MOVEMENTS)
R = Role.Code
MANAGEMENT_ROLES = [code for code in R.values if code not in ("member", "visitor", "guest")]
WITH_T1 = {R.TREASURER, R.ADMINISTRATOR}  # matriu inicial de la 059
DAY = PAID_AT.date()  # la data de valor dels ingressos de `paid`


def client_for(account, area=AREA_ADMIN):
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = area
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return client_for(make_admin(R.TREASURER))


@pytest.fixture
def cash():
    return TreasuryAccount.objects.get(name="Caixa")


@pytest.fixture
def two_fees(make_person):
    """L'exemple del pla (M04-7): dues quotes amb targeta, 9000 i 3500 cèntims, al trànsit."""
    transit = new_transit()
    person = make_person("Núria", "Coll")
    record(paid(person, amount=9000))
    record(paid(person, amount=3500))
    return transit


def adjustment(cash, *, direction=Movement.Direction.OUT, amount=50, on=DAY, reverses=None):
    centre = CostCentre.objects.get(name="Ajustos de caixa")
    return Movement.objects.create(
        account=cash,
        direction=direction,
        amount_cents=amount,
        value_date=on,
        kind=Movement.Kind.REVERSAL if reverses else Movement.Kind.CASH_ADJUSTMENT,
        concept="Ajust d'arqueig de la caixa",
        department=centre.department,
        cost_centre=centre,
        reverses=reverses,
        reason="Recompte de proves",
    )


def page(client, url, **params):
    response = client.get(url, params)
    assert response.status_code == 200
    return main_of(response.content.decode())


# --- Permisos (T1; CA-RP-13; cap ruta pública) ------------------------------------------


@pytest.mark.parametrize("role", MANAGEMENT_ROLES)
@pytest.mark.parametrize("url", ROUTES)
def test_t1_cell_of_each_role(make_admin, role, url):  # noqa: F811
    response = client_for(make_admin(role)).get(url)
    assert response.status_code == (200 if role in WITH_T1 else 404)


@pytest.mark.parametrize("url", ROUTES)
def test_without_an_admin_session_it_asks_for_the_admin_login(client, personal_account, url):
    login = reverse("administration:login")
    assert client.get(url)["Location"].startswith(login)
    personal = client_for(personal_account, area=AREA_PERSONAL).get(url)
    assert personal.status_code == 302 and personal["Location"].startswith(login)


@pytest.mark.parametrize("url", ROUTES)
def test_read_only_no_method_writes(make_admin, url):  # noqa: F811
    assert client_for(make_admin(R.TREASURER)).post(url).status_code == 405
    # Sense permís, «no trobat» abans de mirar el mètode: no revela que la ruta existeix.
    assert client_for(make_admin(R.SECRETARY)).post(url).status_code == 404


def test_the_menu_only_links_the_screens_with_t1(make_admin):  # noqa: F811
    home = reverse("administration:home")
    treasurer = client_for(make_admin(R.TREASURER)).get(home).content.decode()
    secretary = client_for(make_admin(R.SECRETARY)).get(home).content.decode()
    assert ACCOUNTS in treasurer and MOVEMENTS in treasurer
    assert ACCOUNTS not in secretary and MOVEMENTS not in secretary


# --- Saldos (RN-T02, CA-T02.1, LT13) -----------------------------------------------------


def test_lt13_without_movements_balances_are_zero_and_it_says_where_they_come_from(treasurer):
    html = page(treasurer, ACCOUNTS)
    assert "Encara no hi ha cap moviment" in html
    assert "Caixa" in html and "Banc principal" in html
    assert html.count("0,00 €") == TreasuryAccount.objects.count()


def test_ca_t02_1_the_balance_is_entries_minus_exits_up_to_the_date(treasurer, two_fees, cash):
    # Exemple del pla: 9000 + 3500 al trànsit → 125,00 €.
    original = adjustment(cash, amount=50)
    adjustment(cash, direction=Movement.Direction.IN, amount=50, reverses=original)
    adjustment(cash, direction=Movement.Direction.IN, amount=700, on=date(2026, 12, 1))
    found = {a.name: a.balance_cents for a in balances(DAY)}
    assert found[two_fees.name] == 12_500
    assert found["Caixa"] == 0  # l'ajust i el contramoviment s'anul·len; el de desembre, no hi és
    assert {a.name: a.balance_cents for a in balances(date(2026, 12, 1))}["Caixa"] == 700
    assert {a.name: a.balance_cents for a in balances(date(2026, 11, 12))}[two_fees.name] == 0
    html = page(treasurer, ACCOUNTS, on=DAY.isoformat())
    assert "125,00 €" in html and "Encara no hi ha cap moviment" not in html


def test_the_balance_of_every_account_is_a_single_query(two_fees, django_assert_num_queries):
    total = TreasuryAccount.objects.count()
    with django_assert_num_queries(1):
        assert len(list(balances(DAY))) == total


def test_no_field_writes_the_balance_and_no_iban_is_shown(treasurer):
    TreasuryAccount.objects.create(name="Banc de proves", kind="bank", last4="4321")
    html = page(treasurer, ACCOUNTS)
    assert "·4321" in html
    # L'únic formulari és el de la data, amb GET; cap camp no porta el saldo.
    assert html.count("<form") == 1 and 'method="get"' in html
    assert set(re.findall(r'name="([^"]+)"', html)) == {"on"}


def test_an_invalid_date_is_an_error_and_the_balance_is_today(treasurer):
    html = page(treasurer, ACCOUNTS, on="no-es-una-data")
    assert 'aria-invalid="true"' in html
    assert date.today().strftime("%d/%m/%Y") in html


# --- Moviments (C8 sense exportació, CA-T06.1, RNF-T4) -----------------------------------


def test_movements_show_sign_amount_account_and_department_without_names(treasurer, two_fees, cash):
    adjustment(cash, amount=50)
    html = page(treasurer, MOVEMENTS)
    assert "+90,00 €" in html and "+35,00 €" in html and "−0,50 €" in html
    assert "import-entrada" in html and "import-sortida" in html
    assert "General / Quotes de socis" in html and "General / Ajustos de caixa" in html
    assert "3 moviments" in html
    assert "Núria" not in html and "Coll" not in html  # RNF-T4


def test_ca_t06_1_a_reversed_movement_stays_in_the_list_marked(treasurer, cash):
    original = adjustment(cash, amount=50)
    adjustment(cash, direction=Movement.Direction.IN, amount=50, reverses=original)
    html = page(treasurer, MOVEMENTS)
    assert "2 moviments" in html
    assert html.count("Anul·lat") == 1 and "Contramoviment" in html


def test_filters_by_account_department_and_dates(treasurer, two_fees, cash):
    adjustment(cash, amount=50, on=date(2026, 11, 20))
    other = Department.objects.create(name="Departament de proves")

    def count(**params):
        return page(treasurer, MOVEMENTS, **params).count('<th scope="row"')

    assert count() == 3
    assert count(account=two_fees.pk) == 2
    assert count(account=cash.pk) == 1
    assert count(department=Department.objects.get(name="General").pk) == 3
    assert count(department=other.pk) == 0
    assert count(date_from="2026-11-14") == 1
    assert count(date_to="2026-11-13") == 2
    assert count(date_from="2026-11-13", date_to="2026-11-13") == 2


def test_a_reversed_date_range_is_an_error_and_the_end_does_not_filter(treasurer, two_fees):
    # Com al registre d'activitat: els camps vàlids filtren; el que té l'error, no.
    html = page(treasurer, MOVEMENTS, date_from="2026-11-01", date_to="2026-10-01")
    assert "Ha de ser igual o posterior" in html
    assert html.count('<th scope="row"') == 2


def test_without_movements_it_says_so(treasurer):
    assert "Cap moviment amb aquests filtres." in page(treasurer, MOVEMENTS)
