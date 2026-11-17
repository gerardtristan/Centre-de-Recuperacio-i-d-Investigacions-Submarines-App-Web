"""Pantalla de remeses (C5 de M05b-3; B3 de M05b-4; P-M05b-E, passos 1 a 5). Proves per rol, de
la previsualització i la confirmació, de l'avís previ i de la descàrrega. Només dades inventades."""

from datetime import timedelta

import pytest
from django.urls import reverse

from apps.core.models import Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.payments import remittances
from apps.payments.models import DirectDebitRemittance
from apps.payments.tests.test_remittances import (  # noqa: F401 (fixtures)
    collection_date,
    iban,
    new_member,
    signer,
    text,
)
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
URL = reverse("administration:payments_remittances")
R = Role.Code
MANAGEMENT_ROLES = [code for code in R.values if code not in ("member", "visitor", "guest")]


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
def fees(signer, text):  # noqa: F811
    new_member(1, signer=signer, text=text, cents=3500)
    new_member(2, signer=signer, text=text)
    new_member(3, mandate=False)


def form(**extra):
    day = collection_date().isoformat()
    return {"period": "2026-12", "collection_date": day, "previewed": day, **extra}


@pytest.mark.parametrize("role", MANAGEMENT_ROLES)
def test_b3_cella_de_cada_rol(make_admin, role, fees):  # noqa: F811
    client = client_for(make_admin(role))
    allowed = role == R.TREASURER  # B3: només el tresorer (M05b-4)
    assert client.get(URL).status_code == (200 if allowed else 404)
    response = client.post(URL, form(confirm="1"))
    assert response.status_code == (302 if allowed else 404)
    assert DirectDebitRemittance.objects.exists() == allowed


def test_previsualitzar_no_crea_res_i_confirmar_crea_la_remesa(client, fees):
    html = main_of(client.post(URL, form()).content.decode())
    assert "125,00 €" in html and "Sense mandat actiu" in html and "Sí, crea la remesa" in html
    assert not DirectDebitRemittance.objects.exists()

    later = (collection_date() + timedelta(days=1)).isoformat()
    client.post(
        URL, form(confirm="1", collection_date=later)
    )  # data canviada: torna a previsualitzar
    assert not DirectDebitRemittance.objects.exists()
    response = client.post(URL, form(confirm="1"))

    remittance = DirectDebitRemittance.objects.get()
    assert response.url == reverse("administration:payments_remittance", args=[remittance.pk])
    detail = main_of(client.get(response.url).content.decode())
    assert "Avisada" in detail and "ES … 0001" in detail
    assert iban(1) not in detail and iban(2) not in detail


def test_una_data_massa_propera_es_rebutja_al_formulari(client, fees):
    too_soon = remittances.earliest_collection_date().toordinal() - 1
    date = type(collection_date()).fromordinal(too_soon).isoformat()
    html = main_of(client.post(URL, form(collection_date=date, confirm="1")).content.decode())
    assert "avís previ" in html
    assert not DirectDebitRemittance.objects.exists()


def test_la_descarrega_dona_el_fitxer_sense_desar_lo(client, fees, treasurer):
    remittance = remittances.build_remittance("2026-12", collection_date(), treasurer)
    url = reverse("administration:payments_remittance_file", args=[remittance.pk])

    assert client.get(url).status_code == 405  # només POST
    response = client.post(url)

    assert response["Content-Type"] == "application/xml"
    assert "attachment" in response["Content-Disposition"]
    assert "no-store" in response["Cache-Control"]
    assert iban(1).encode() in response.content
    remittance.refresh_from_db()
    assert remittance.file_hash


def test_esborrany_sense_fitxer_i_avisos_que_falten(client, signer, text, treasurer):  # noqa: F811
    new_member(1, signer=signer, text=text, email=False)
    remittance = remittances.build_remittance("2026-12", collection_date(), treasurer)
    detail = reverse("administration:payments_remittance", args=[remittance.pk])

    html = main_of(client.get(detail).content.decode())
    assert "Torna a enviar els avisos" in html and "Descarrega el fitxer" not in html
    response = client.post(reverse("administration:payments_remittance_file", args=[remittance.pk]))
    assert response.status_code == 302
    response = client.post(
        reverse("administration:payments_remittance_notices", args=[remittance.pk]), follow=True
    )
    assert "cal avisar-los per una altra via" in response.content.decode()
