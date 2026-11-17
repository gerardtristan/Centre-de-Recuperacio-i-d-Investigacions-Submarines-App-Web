"""Exportació CSV dels moviments per a la gestoria (T-M04-16; C8 i T9 de M04-3 i M04-4; HU-T15,
P-M04-G; CA-T15.1; RNF-T4, RN-T03). Només dades inventades."""

import codecs
import csv
import io
from datetime import date

import pytest
from django.urls import reverse

from apps.core.models import AuditEntry, Payment, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.treasury import exports, views
from apps.treasury.models import CostCentre, Movement, TreasuryAccount
from apps.treasury.tests.test_views import (
    MANAGEMENT_ROLES,
    MOVEMENTS,
    adjustment,
    cash,  # noqa: F401 (fixture)
    client_for,
    two_fees,  # noqa: F401 (fixture)
)

pytestmark = pytest.mark.django_db
EXPORT = reverse("administration:treasury_export")
R = Role.Code
WITH_T9 = {R.TREASURER, R.ADMINISTRATOR}  # M04-4, T9


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return client_for(make_admin(R.TREASURER))


def download(client, **filters):
    response = client.post(EXPORT, filters)
    assert response.status_code == 200
    content = response.content
    assert content.startswith(codecs.BOM_UTF8)
    return response, list(csv.reader(io.StringIO(content.decode("utf-8-sig")), delimiter=";"))


def test_ca_t15_1_columns_euros_and_no_personal_data(treasurer, two_fees, cash):  # noqa: F811
    Payment.objects.filter(amount_cents=9000).update(provider_reference="REF-PROVES-1")
    bank = TreasuryAccount.objects.get(name="Banc principal")
    TreasuryAccount.objects.filter(pk=bank.pk).update(last4="1954")
    adjustment(cash, amount=123456, on=date(2026, 11, 20))
    response, rows = download(treasurer)
    assert response["Content-Type"] == "text/csv; charset=utf-8"
    assert response["Content-Disposition"].startswith('attachment; filename="moviments-')
    assert rows[0] == [
        "Data",
        "Compte",
        "Concepte",
        "Departament",
        "Centre de cost",
        "Entrada",
        "Sortida",
        "Referència",
    ]
    fee, smaller, cash_row = rows[1:]  # del més antic al més recent
    assert fee[0] == "13/11/2026" and fee[1] == two_fees.name
    assert fee[3:] == ["General", "Quotes de socis", "90,00", "", "REF-PROVES-1"]
    assert smaller[5:7] == ["35,00", ""]
    assert cash_row[:2] == ["20/11/2026", "Caixa"]
    assert cash_row[3:] == ["General", "Ajustos de caixa", "", "1234,56", ""]
    text = response.content.decode("utf-8-sig")
    assert "Núria" not in text and "Coll" not in text  # RNF-T4
    assert "1954" not in text  # cap dígit del compte bancari (RN-T03)


def test_the_same_filters_as_the_list(treasurer, two_fees, cash):  # noqa: F811
    adjustment(cash, amount=50, on=date(2026, 11, 20))
    fees = CostCentre.objects.get(name="Quotes de socis")

    def count(**filters):
        return len(download(treasurer, **filters)[1]) - 1

    assert count() == 3
    assert count(account=cash.pk) == 1
    assert count(cost_centre=fees.pk) == 2
    assert count(date_from="2026-11-14") == 1
    assert count(date_to="2026-11-13") == 2
    # Un filtre no vàlid no filtra, com a la llista.
    assert count(date_from="2026-11-14", date_to="2026-11-01") == 1


def test_a_reversed_movement_and_its_reversal_both_appear(treasurer, cash):  # noqa: F811
    original = adjustment(cash, amount=50)
    adjustment(cash, direction=Movement.Direction.IN, amount=50, reverses=original)
    _response, rows = download(treasurer)
    assert sorted((row[5], row[6]) for row in rows[1:]) == [("", "0,50"), ("0,50", "")]


def test_a_formula_in_the_concept_is_neutralised(treasurer, cash):  # noqa: F811
    centre = CostCentre.objects.get(name="Ajustos de caixa")
    Movement.objects.create(
        account=cash,
        direction=Movement.Direction.OUT,
        amount_cents=100,
        value_date=date(2026, 11, 20),
        kind=Movement.Kind.CASH_ADJUSTMENT,
        concept='=HYPERLINK("http://exemple.invalid")',
        department=centre.department,
        cost_centre=centre,
        reason="Prova",
    )
    _response, rows = download(treasurer)
    assert rows[1][2].startswith("'=")


def test_each_export_is_logged_with_the_filters_and_the_rows(make_admin, two_fees):  # noqa: F811
    account = make_admin(R.TREASURER)
    download(client_for(account), account=two_fees.pk, date_from="2026-11-01")
    row = AuditEntry.objects.get(action=views.EXPORTED)
    assert row.actor_account == account
    assert row.details == {
        "filters": {"account": str(two_fees.pk), "date_from": "2026-11-01"},
        "rows": 2,
    }


@pytest.mark.parametrize("role", MANAGEMENT_ROLES)
def test_t9_cell_of_each_role(make_admin, role):  # noqa: F811
    response = client_for(make_admin(role)).post(EXPORT)
    assert response.status_code == (200 if role in WITH_T9 else 404)
    if role not in WITH_T9:
        assert not AuditEntry.objects.filter(action=views.EXPORTED).exists()


def test_only_post(make_admin):  # noqa: F811
    assert client_for(make_admin(R.TREASURER)).get(EXPORT).status_code == 405
    assert client_for(make_admin(R.SECRETARY)).get(EXPORT).status_code == 404


def test_the_button_carries_the_filters_of_the_list(treasurer, two_fees):  # noqa: F811
    html = main_of(treasurer.get(MOVEMENTS, {"account": two_fees.pk}).content.decode())
    assert f'action="{EXPORT}"' in html
    assert f'name="account" value="{two_fees.pk}"' in html
    assert 'name="date_from"' not in html.split(f'action="{EXPORT}"')[1].split("</form>")[0]


def test_amounts_are_two_decimals_with_a_comma():
    assert [exports.amount(c) for c in (0, 5, 50, 12_500, 123_456)] == [
        "0,00",
        "0,05",
        "0,50",
        "125,00",
        "1234,56",
    ]
