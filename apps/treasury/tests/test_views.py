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
from apps.core.models import Department, Role, RolePermission
from apps.core.tests.conftest import (
    main_of,
    make_admin,  # noqa: F401 (fixture)
)
from apps.treasury.balances import balances
from apps.treasury.models import CostCentre, Movement, StatementLineState, TreasuryAccount
from apps.treasury.references import check_character
from apps.treasury.settlements import SettlementLine
from apps.treasury.tests.test_reconciliation import lines
from apps.treasury.tests.test_record_income import PAID_AT, new_transit, paid, record
from apps.treasury.tests.test_settlements import collected, data, record_it

pytestmark = pytest.mark.django_db
ACCOUNTS = reverse("administration:treasury_accounts")
MOVEMENTS = reverse("administration:treasury_movements")
REVIEW = reverse("administration:treasury_review")
ROUTES = (ACCOUNTS, MOVEMENTS, REVIEW)  # REVIEW: T10, les mateixes cel·les inicials que T1
REVIEW_CODE = "treasury.review"  # T10 (P-190, 095)
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


def test_t10_is_its_own_cell_not_t1(make_admin):  # noqa: F811
    # P-190 (095): sense la cel·la T10, la llista «a revisar» no es troba encara que hi hagi T1; amb
    # T10 i sense T1, s'obre.
    RolePermission.objects.filter(role__code=R.ADMINISTRATOR, permission_code=REVIEW_CODE).delete()
    admin = client_for(make_admin(R.ADMINISTRATOR))
    assert admin.get(REVIEW).status_code == 404 and admin.get(ACCOUNTS).status_code == 200
    RolePermission.objects.create(
        role=Role.objects.get(code=R.SECRETARY), permission_code=REVIEW_CODE, scope="all"
    )
    secretary = client_for(make_admin(R.SECRETARY))
    assert secretary.get(REVIEW).status_code == 200 and secretary.get(ACCOUNTS).status_code == 404


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


# --- «A revisar» i exclusions (T-M04-14; C6, T8, T10; CA-T12.1, CA-T13.1) ------------------


def exclude_url(line):
    return reverse("administration:treasury_exclude_line", args=[line.pk])


def test_ca_t13_1_empty_list_says_there_is_nothing_to_review(treasurer):
    assert "No hi ha res a revisar." in page(treasurer, REVIEW)


def test_ca_t13_1_a_line_to_review_shows_its_reason_without_the_concept(make_admin, settings):  # noqa: F811
    settings.TRANSFER_REFERENCE_PREFIX = "CRIS"
    account = make_admin(R.TREASURER)
    reference = f"CRIS-AB2CD-{check_character('AB2CD')}"  # vàlida, però de cap càrrec
    (line,) = lines(account, (777, f"{reference} PAGAT PER JOAN INVENTAT"))
    html = page(client_for(account), REVIEW)
    assert "La referència no és de cap càrrec" in html and "7,77" in html
    assert "INVENTAT" not in html  # el concepte només es veu a la conciliació (M04-4)
    assert exclude_url(line) in html
    # L'administrador veu la llista (T10) però no pot excloure (T8): ni formulari ni POST.
    admin = client_for(make_admin(R.ADMINISTRATOR))
    assert exclude_url(line) not in page(admin, REVIEW)
    assert admin.post(exclude_url(line), {"motiu": "Prova"}).status_code == 404


def test_ca_t13_1_a_settlement_to_review_shows_its_problem_and_where_to_resolve_it(
    make_admin,  # noqa: F811
    make_person,
):
    """T-M04-14b (P-191, opció per defecte): la llista també mostra les liquidacions «a revisar»
    (CA-T11.2) amb la referència i el problema, sense cap nom, i l'enllaç on es revisen. Una
    liquidació rebuda no hi surt. Res no es tanca ni es mou des d'aquí."""
    new_transit()
    collected(make_person("Núria", "Coll"), 9000, "REF-A")
    record_it(data(SettlementLine("REF-A", 9000), external_id="LIQ-BONA"))
    record_it(data(SettlementLine("REF-X", 2500), external_id="LIQ-DUBTE"))
    for role in (R.TREASURER, R.ADMINISTRATOR):  # T10
        html = page(client_for(make_admin(role)), REVIEW)
        assert "LIQ-DUBTE" in html and "REF-X" in html and "23,80" in html
        assert "Cap cobrament amb aquesta referència" in html
        assert reverse("administration:treasury_settlements") in html
        assert reverse("administration:payments_list") in html  # B6: els intents, al 05b
        assert "LIQ-BONA" not in html and "Coll" not in html
        assert "No hi ha res a revisar." not in html


def test_ca_t12_1_excluding_from_the_screen(make_admin):  # noqa: F811
    account = make_admin(R.TREASURER)
    (line,) = lines(account, (-1230, "REBUT LLUM"))
    client = client_for(account)
    assert client.get(exclude_url(line)).status_code == 405
    response = client.post(exclude_url(line), {"motiu": ""}, follow=True)
    assert "cal escriure&#x27;n el motiu" in response.content.decode()
    response = client.post(exclude_url(line), {"motiu": "Despesa"}, follow=True)
    assert "Línia exclosa. No s&#x27;ha creat cap moviment." in response.content.decode()
    state = StatementLineState.objects.get(statement_line=line)
    assert (state.status, state.exclusion_reason) == ("excluded", "Despesa")
    assert not Movement.objects.exists()
    assert (
        client.post(
            reverse("administration:treasury_exclude_line", args=[999999]), {"motiu": "x"}
        ).status_code
        == 404
    )
