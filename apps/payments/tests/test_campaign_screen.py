"""Pantalla de la campanya de mandats (T-M05a-13, segona part; C5 de M05a-3; A4 i A5 de M05a-4;
P-M05a-E). Proves per rol, per abast i de la confirmació. Només dades inventades."""

import pytest
from django.urls import reverse
from procrastinate.contrib.django.models import ProcrastinateJob

from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.members.tests.test_cards import make_member
from apps.payments import campaigns
from apps.payments.models import MandateCampaign
from apps.payments.tests.test_campaigns import member_with_email, ready  # noqa: F401
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
URL = reverse("administration:payments_campaign")
R = Role.Code
MANAGEMENT_ROLES = [code for code in R.values if code not in ("member", "visitor", "guest")]
WITH_ACCESS = {R.TREASURER, R.ADMINISTRATOR}
WITH_A4_ONLY = {R.SECRETARY}  # «Cons.» (P-193, 095): veu el recompte, no obre res


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(R.TREASURER)


@pytest.fixture
def client(treasurer):
    return client_for(treasurer)


@pytest.fixture
def campaign(treasurer):
    return campaigns.open_campaign("Campanya de prova", by=treasurer)


def page(client):
    response = client.get(URL)
    assert response.status_code == 200
    return main_of(response.content.decode())


def jobs():
    return ProcrastinateJob.objects.filter(task_name="payments.send_campaign_invitations")


@pytest.mark.parametrize("role", MANAGEMENT_ROLES)
def test_a4_i_a5_cella_de_cada_rol(make_admin, role):  # noqa: F811
    client = client_for(make_admin(role))
    expected = 200 if role in WITH_ACCESS | WITH_A4_ONLY else 404
    assert client.get(URL).status_code == expected
    response = client.post(URL, {"action": "open", "name": "Prova"})
    assert response.status_code == (302 if role in WITH_ACCESS else 404)
    assert MandateCampaign.objects.exists() == (role in WITH_ACCESS)


def test_amb_a4_de_consulta_i_sense_a5_nomes_es_veu_el_recompte(make_admin, campaign):  # noqa: F811
    # La Secretaria té «Cons.» a A4 de bon principi (P-193, 095) i no té A5.
    client = client_for(make_admin(R.SECRETARY))

    html = page(client)
    assert "Sense resposta" in html and "<form" not in html
    assert client.post(URL, {"action": "close", "confirm": "1"}).status_code == 404
    campaign.refresh_from_db()
    assert campaign.closed_at is None


def test_obrir_des_de_la_pantalla(client, treasurer):
    assert "Obre la campanya" in page(client)
    client.post(URL, {"action": "open", "name": "Tardor"})

    assert MandateCampaign.objects.get().opened_by == treasurer
    assert "Tardor" in page(client)


def test_sense_signatura_no_hi_ha_formularis_i_el_post_no_obre_res(settings, client):
    settings.MANDATE_SIGNING_ENABLED = False

    html = page(client)
    assert "La signatura del mandat no està activada" in html
    assert "Obre la campanya" not in html
    client.post(URL, {"action": "open", "name": "Prova"})
    assert not MandateCampaign.objects.exists()


def test_enviar_demana_confirmacio_i_va_per_la_cua(client, campaign, treasurer):
    member_with_email("Anna", 1287, "12345678Z")
    make_member("Marc", number=603, document="00000004G")  # sense correu (P-199)

    first = client.post(URL, {"action": "send"})
    assert first.status_code == 200
    assert "1 invitació per correu." in first.content.decode()
    assert not jobs().exists()

    client.post(URL, {"action": "send", "confirm": "1"})
    job = jobs().get()
    assert job.args == {"campaign_id": campaign.pk, "account_id": treasurer.pk}


def test_tancar_demana_confirmacio(client, campaign):
    assert client.post(URL, {"action": "close"}).status_code == 200
    campaign.refresh_from_db()
    assert campaign.closed_at is None

    client.post(URL, {"action": "close", "confirm": "1"})
    campaign.refresh_from_db()
    assert campaign.closed_at is not None
    assert AuditEntry.objects.filter(action="payments.campaign.closed").exists()
    assert "No hi ha cap campanya oberta." in page(client)


def test_recompte_i_encara_no_ha_respost_ningu(client, campaign, treasurer):
    member_with_email("Anna", 1287, "12345678Z")
    member_with_email("Jordi", 311, "00000001R")
    campaigns.send_invitations(campaign, by=treasurer)

    html = page(client)
    assert "Com pagaran els 2 socis actius" in html
    assert "Encara no ha respost ningú." in html
    assert "anna" not in html.lower()  # cap nom ni adreça
