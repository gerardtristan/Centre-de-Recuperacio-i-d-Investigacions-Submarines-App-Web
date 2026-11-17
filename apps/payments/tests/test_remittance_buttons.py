"""Botons de la remesa: marcar-la enviada i casar l'abonament (T-M05b-11b; B3 i T4; P-M05b-E,
passos 6 a 8; CA-T16.1). Només dades inventades."""

import pytest
from django.urls import reverse

from apps.core.models import Charge, Role, RolePermission
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.payments import remittances, sepa_xml
from apps.payments.models import DirectDebitRemittance
from apps.payments.tests.test_remittance_settlement import bank_line
from apps.payments.tests.test_remittances import (  # noqa: F401 (fixtures)
    collection_date,
    iban,
    new_member,
    signer,
    text,
)
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
R = Role.Code


@pytest.fixture(autouse=True)
def club(settings):
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    settings.CLUB_IBAN_TRANSFERENCIES = iban(999)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(R.TREASURER)


@pytest.fixture
def client(treasurer):
    return client_for(treasurer)


@pytest.fixture
def notified(signer, text, treasurer):  # noqa: F811
    new_member(1, signer=signer, text=text, cents=3500)
    new_member(2, signer=signer, text=text)
    remittance = remittances.build_remittance("2026-12", collection_date(), treasurer)
    sepa_xml.remittance_file(remittance, treasurer)
    return remittance


def urls(remittance):
    args = [remittance.pk]
    return (
        reverse("administration:payments_remittance", args=args),
        reverse("administration:payments_remittance_sent", args=args),
        reverse("administration:payments_remittance_settle", args=args),
    )


def status(remittance):
    return DirectDebitRemittance.objects.get(pk=remittance.pk).status


def test_marcar_enviada_demana_la_casella_de_l_esborrat(client, notified):
    detail, sent, _settle = urls(notified)
    assert "Marca com a enviada al banc" in main_of(client.get(detail).content.decode())

    client.post(sent, {})
    assert status(notified) == "notified"
    client.post(sent, {"file_deleted": "on"})
    assert status(notified) == "sent_to_bank"


def test_casar_l_abonament_en_dos_passos(client, notified, treasurer):
    remittances.mark_remittance_sent(notified, file_deleted=True, by=treasurer)
    line = bank_line(12500 - 260, treasurer)
    detail, _sent, settle = urls(notified)

    html = main_of(client.get(detail, {"fee": "2,60"}).content.decode())
    assert "Casa aquesta línia…" in html and "122,40 €" in html

    html = main_of(client.post(settle, {"line": line.pk, "fee": "2,60"}).content.decode())
    assert "Sí, casa l'abonament" in html
    assert status(notified) == "sent_to_bank"  # el primer pas no canvia res

    client.post(settle, {"line": line.pk, "fee": "2,60", "confirm": "1"})
    assert status(notified) == "settled"
    assert Charge.objects.filter(status=Charge.Status.PAID).count() == 2


def test_una_linia_que_no_es_candidata_es_rebutja(client, notified, treasurer):
    remittances.mark_remittance_sent(notified, file_deleted=True, by=treasurer)
    other = bank_line(9999, treasurer)
    _detail, _sent, settle = urls(notified)

    client.post(settle, {"line": other.pk, "fee": "0", "confirm": "1"})

    assert status(notified) == "sent_to_bank"
    assert not Charge.objects.filter(status=Charge.Status.PAID).exists()


def test_sense_t4_no_es_veu_ni_es_pot_casar(make_admin, notified, treasurer):  # noqa: F811
    remittances.mark_remittance_sent(notified, file_deleted=True, by=treasurer)
    line = bank_line(12500, treasurer)
    RolePermission.objects.filter(
        role__code=R.TREASURER, permission_code="treasury.reconcile"
    ).delete()
    client = client_for(treasurer)
    detail, _sent, settle = urls(notified)

    assert "Casa l'abonament del banc" not in main_of(client.get(detail).content.decode())
    assert client.post(settle, {"line": line.pk, "fee": "0", "confirm": "1"}).status_code == 404
    assert status(notified) == "sent_to_bank"


@pytest.mark.parametrize("role", [R.SECRETARY, R.ADMINISTRATOR])
def test_sense_b3_no_es_pot_marcar_ni_casar(make_admin, notified, role):  # noqa: F811
    client = client_for(make_admin(role))
    _detail, sent, settle = urls(notified)
    assert client.post(sent, {"file_deleted": "on"}).status_code == 404
    assert client.post(settle, {"line": 1, "fee": "0", "confirm": "1"}).status_code == 404
    assert status(notified) == "notified"
