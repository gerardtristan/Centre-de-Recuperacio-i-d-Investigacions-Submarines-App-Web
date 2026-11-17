"""Pantalles de traspàs, arqueig, anul·lació i liquidacions (T-M04-15, tercer tall; T4 a T7).
Proves per permís, dels dos passos i dels errors del servei. Només dades inventades."""

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.core.models import Department, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.treasury import services, settlements
from apps.treasury.balances import balance
from apps.treasury.models import CashCount, Movement, ProviderSettlement, TreasuryAccount
from apps.treasury.tests.test_settlements import (  # noqa: F401 (fixtures)
    data,
    person,
    record_it,
    transit,
    two,
)
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
R = Role.Code
TRANSFER = reverse("administration:treasury_transfer")
CASH = reverse("administration:treasury_cash_count")
SETTLEMENTS = reverse("administration:treasury_settlements")


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(R.TREASURER)


@pytest.fixture
def client(treasurer):
    return client_for(treasurer)


@pytest.fixture
def accounts():
    return TreasuryAccount.objects.get(name="Banc principal"), TreasuryAccount.objects.get(
        name="Caixa"
    )


def transfer_form(bank, cash, **extra):
    today = timezone.localdate().isoformat()
    return {"source": cash.pk, "destination": bank.pk, "amount": "120,50", "value_date": today,
            "concept": "Ingrés de l'efectiu de la caixa", **extra}  # fmt: skip


@pytest.mark.parametrize("role", [R.SECRETARY, R.PRESIDENT])
def test_sense_t5_t6_ni_t7_no_trobat(make_admin, role, accounts):  # noqa: F811
    client = client_for(make_admin(role))
    movement = Movement.objects.first()
    for url in (TRANSFER, CASH):
        assert client.get(url).status_code == 404
        assert client.post(url, {"confirm": "1"}).status_code == 404
    if movement:
        assert (
            client.get(reverse("administration:treasury_reverse", args=[movement.pk])).status_code
            == 404
        )


def test_traspas_en_dos_passos(client, accounts):
    bank, cash = accounts
    html = main_of(client.post(TRANSFER, transfer_form(bank, cash)).content.decode())
    assert "Confirma el traspàs" in html and "120,50 €" in html
    assert not Movement.objects.filter(kind=Movement.Kind.TRANSFER).exists()

    response = client.post(TRANSFER, transfer_form(bank, cash, confirm="1"))

    assert response.url == reverse("administration:treasury_movements")
    out, entry = Movement.objects.filter(kind=Movement.Kind.TRANSFER).order_by("pk")
    assert (out.account, entry.account, out.amount_cents) == (cash, bank, 12050)


def test_traspas_rebutjat_pel_servei_no_desa_res(client, accounts):
    bank, _cash = accounts
    html = main_of(client.post(TRANSFER, transfer_form(bank, bank, confirm="1")).content.decode())
    assert "dos comptes propis diferents" in html
    assert not Movement.objects.filter(kind=Movement.Kind.TRANSFER).exists()


def test_arqueig_mostra_la_diferencia_i_fa_l_ajust_amb_motiu(client, accounts):
    _bank, cash = accounts
    today = timezone.localdate()
    form = {"account": cash.pk, "counted": "15,00", "counted_on": today.isoformat(),
            "adjustment_reason": "Recompte de prova"}  # fmt: skip
    html = main_of(client.post(CASH, form).content.decode())
    assert "Saldo calculat" in html and "15,00 €" in html and "Ajustos de caixa" in html
    assert not CashCount.objects.exists()

    client.post(CASH, {**form, "confirm": "1"})

    count = CashCount.objects.get()
    assert (count.counted_cents, count.adjustment is not None) == (1500, True)
    assert balance(cash, today) == 1500


def test_anullar_un_moviment_demana_motiu_i_dos_passos(client, accounts, treasurer):
    _bank, cash = accounts
    services.record_cash_count(
        cash, 700, counted_on=timezone.localdate(), by=treasurer, adjustment_reason="Prova"
    )
    adjustment = Movement.objects.get(kind=Movement.Kind.CASH_ADJUSTMENT)
    url = reverse("administration:treasury_reverse", args=[adjustment.pk])
    assert "Anul·la…" in main_of(
        client.get(reverse("administration:treasury_movements")).content.decode()
    )

    assert "Motiu" in main_of(client.post(url, {"reason": ""}).content.decode())
    html = main_of(client.post(url, {"reason": "Arqueig equivocat"}).content.decode())
    assert "Confirma l'anul·lació" in html
    assert not Movement.objects.filter(kind=Movement.Kind.REVERSAL).exists()

    client.post(url, {"reason": "Arqueig equivocat", "confirm": "1"})
    assert Movement.objects.get(kind=Movement.Kind.REVERSAL).reverses == adjustment


def test_un_traspas_no_s_anulla_des_de_la_pantalla(client, accounts, treasurer):
    bank, cash = accounts
    services.record_transfer(cash, bank, 500, value_date=timezone.localdate(), concept="Prova",
                             by=treasurer)  # fmt: skip
    leg = Movement.objects.filter(kind=Movement.Kind.TRANSFER).first()
    url = reverse("administration:treasury_reverse", args=[leg.pk])
    html = main_of(client.get(url).content.decode())
    assert "no s'anul·la aquí" in html and "Revisa l'anul·lació" not in html
    client.post(url, {"reason": "Prova", "confirm": "1"})
    assert not Movement.objects.filter(kind=Movement.Kind.REVERSAL).exists()


def test_liquidacions_amb_motius_i_confirmacio(client, two, treasurer):  # noqa: F811
    received = record_it()
    to_review = record_it(data(gross=None, external_id="LIQ-002"))  # cobraments ja liquidats
    html = main_of(client.get(SETTLEMENTS).content.decode())
    assert "LIQ-001" in html and "Confirma…" in html
    assert to_review.status == "to_review" and "ja és en una altra liquidació" in html

    url = reverse("administration:treasury_settlement_confirm", args=[received.pk])
    assert "Sí, confirma-la" in main_of(client.get(url).content.decode())
    client.post(url)
    assert ProviderSettlement.objects.get(pk=received.pk).status == "reconciled"


def test_confirmar_una_liquidacio_demana_t4(make_admin, two):  # noqa: F811
    settlement = record_it()
    client = client_for(make_admin(R.SECRETARY))
    url = reverse("administration:treasury_settlement_confirm", args=[settlement.pk])
    assert client.post(url).status_code == 404
    assert ProviderSettlement.objects.get(pk=settlement.pk).status == settlements.Status.RECEIVED


# --- T-M04-15d: anul·lar despeses i altres ingressos (#153) i el període tancat --------------


def margins_movement(kind, bank, by):
    general = Department.objects.get(name="General")
    record = services.record_expense if kind == "expense" else services.record_other_income
    return record(
        bank, 4200, value_date=timezone.localdate(), department=general,
        concept="Factura de prova", by=by,
    )  # fmt: skip


@pytest.mark.parametrize("kind", ["expense", "other_income"])
def test_una_despesa_o_un_altre_ingres_s_anullen_amb_motiu(client, accounts, treasurer, kind):
    bank, _cash = accounts
    movement = margins_movement(kind, bank, treasurer)
    url = reverse("administration:treasury_reverse", args=[movement.pk])
    listing = main_of(client.get(reverse("administration:treasury_movements")).content.decode())
    assert url in listing
    assert "Revisa l'anul·lació" in main_of(client.get(url).content.decode())

    client.post(url, {"reason": "Factura duplicada (prova)", "confirm": "1"})

    reversal = Movement.objects.get(kind=Movement.Kind.REVERSAL)
    assert reversal.reverses == movement and reversal.reason == "Factura duplicada (prova)"
    assert balance(bank, timezone.localdate()) == 0


def test_dins_un_periode_tancat_surt_l_error_i_no_es_desa_res(
    client, accounts, treasurer, monkeypatch
):
    bank, _cash = accounts
    movement = margins_movement("expense", bank, treasurer)
    monkeypatch.setattr(services, "_GUARDS", [])
    services.register_movement_guard(timezone.localdate)  # tancat fins avui (RN-T30)
    url = reverse("administration:treasury_reverse", args=[movement.pk])

    html = main_of(client.post(url, {"reason": "Prova", "confirm": "1"}).content.decode())

    assert "període tancat" in html
    assert not Movement.objects.filter(kind=Movement.Kind.REVERSAL).exists()
