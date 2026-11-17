"""Pantalla de retornats i proposta d'alternativa a la remesa (T-M05b-27; P-M05b-F; B4;
CA-M05b-32). Només dades inventades."""

import pytest
from django.urls import reverse

from apps.core.models import Charge, OutgoingEmail, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.payments import remittances, returns, sepa_xml
from apps.payments.models import DirectDebitItem
from apps.payments.tests.test_remittance_settlement import (  # noqa: F401 (fixtures)
    club,
    sent,
    treasurer,
)
from apps.payments.tests.test_remittances import (  # noqa: F401 (fixtures)
    collection_date,
    signer,
    text,
)
from apps.payments.tests.test_returns import collected, settle  # noqa: F401 (fixture)
from apps.treasury.models import Movement
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
URL = reverse("administration:payments_returns")
R = Role.Code
MANAGEMENT_ROLES = [code for code in R.values if code not in ("member", "visitor", "guest")]


def decision(item):
    return reverse("administration:payments_return_decision", args=[item.pk])


@pytest.mark.parametrize("role", MANAGEMENT_ROLES)
def test_b4_cella_de_cada_rol(make_admin, role, collected):  # noqa: F811
    client = client_for(make_admin(role))
    allowed = role == R.TREASURER  # B4: només el tresorer (core/0040)
    assert client.get(URL).status_code == (200 if allowed else 404)
    form = {"end_to_end_id": collected[0].end_to_end_id, "reason_code": "AM04"}
    assert client.post(URL, form).status_code == (302 if allowed else 404)
    assert client.post(decision(collected[0]), {"decision": "retry"}).status_code == (
        302 if allowed else 404
    )
    assert Movement.objects.filter(kind="return").exists() == allowed


def test_registra_amb_comissio_i_decideix_el_reintent(treasurer, collected):  # noqa: F811
    client = client_for(treasurer)
    item = collected[0]
    form = {"end_to_end_id": item.end_to_end_id, "reason_code": "am04", "fee": "3,00"}

    response = client.post(URL, form, follow=True)

    html = main_of(response.content.decode())
    assert "Proposta: reintent" in html and "Reintent (intent 2)" in html and "AM04" in html
    assert Movement.objects.get(kind="fee").amount_cents == 300
    client.post(decision(item), {"decision": "retry"})
    assert Charge.objects.get(pk=item.attempt.charge_id).status == Charge.Status.PENDING
    html = main_of(client.get(URL).content.decode())
    assert "No hi ha cap retorn per decidir." in html


def test_una_referencia_desconeguda_no_canvia_res(treasurer, collected):  # noqa: F811
    response = client_for(treasurer).post(URL, {"end_to_end_id": "R000999", "reason_code": "AM04"})
    assert "No hi ha cap rebut cobrat" in main_of(response.content.decode())
    assert not DirectDebitItem.objects.filter(status="returned").exists()


def test_ca_m05b_32_intents_esgotats_alternativa_i_proposta_a_la_remesa(treasurer, collected):  # noqa: F811
    client = client_for(treasurer)
    first = collected[0]
    returns.register_return(first, "AM04", by=treasurer)
    returns.confirm(first, returns.RETRY, by=treasurer)
    second = remittances.build_remittance("2026-12-R", collection_date(), treasurer)
    sepa_xml.remittance_file(second, treasurer)
    remittances.mark_remittance_sent(second, file_deleted=True, by=treasurer)
    settle(second, treasurer, n=2)
    retry = second.items.get()

    response = client.post(
        URL, {"end_to_end_id": retry.end_to_end_id, "reason_code": "AM04"}, follow=True
    )

    assert "No queda cap reintent" in main_of(response.content.decode())
    assert OutgoingEmail.objects.filter(template=returns.ALTERNATIVE_TEMPLATE).count() == 1
    day = collection_date().isoformat()
    preview = client.post(
        reverse("administration:payments_remittances"),
        {"period": "2027-01", "collection_date": day},
    )
    html = main_of(preview.content.decode())
    assert "Intents esgotats" in html and "Proposta: alternativa de pagament" in html
