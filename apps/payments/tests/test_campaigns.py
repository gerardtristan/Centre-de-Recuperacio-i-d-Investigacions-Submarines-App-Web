"""Campanya de mandats: obrir, convidar, recordar, recomptar i tancar (T-M05a-13; P-M05a-E;
RN-M05a-14; CA-M05a-12; P-135, P-199, P-210 i P-211, opcions per defecte). Dates inventades amb
el rellotge controlat (`today`) i el dia local (`timezone.localdate`)."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import business_settings
from apps.core.models import AuditEntry, LegalText, OutgoingEmail, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.models import Member
from apps.members.tests.test_cards import make_member
from apps.payments import campaigns, preferences, tasks
from apps.payments.models import MandateCampaign, MandateCampaignRecipient
from apps.payments.tests.test_preferences import prefer
from apps.treasury.tests.test_views import client_for
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

INVITATION = campaigns.INVITATION_TEMPLATE
REMINDER = campaigns.REMINDER_TEMPLATE


@pytest.fixture(autouse=True)
def ready(settings):
    settings.MANDATE_SIGNING_ENABLED = True
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    settings.PUBLIC_SITE_URL = "https://cris1954.cat"
    LegalText.objects.create(
        kind=campaigns.INVITATION_TEXT, version=1, content="Text de prova de la invitació."
    )


def member_with_email(first, number, document, status=Member.Status.ACTIVE):
    member = make_member(first, number=number, document=document, status=status)
    email = f"{first.lower()}.prova@example.org"
    Person.objects.filter(pk=member.person_id).update(contact_email=email)
    member.person.refresh_from_db()
    return member


@pytest.fixture
def treasurer(db):
    person = Person.objects.create(first_name="Tresa", last_name="Prova", origin=Person.Origin.WEB)
    return Account.objects.create_admin(
        person, "tresoreria.prova", PASSWORD, notification_email="t@example.org"
    )


@pytest.fixture
def anna():
    return member_with_email("Anna", 1287, "12345678Z")


@pytest.fixture
def jordi():
    return member_with_email("Jordi", 311, "00000001R")


@pytest.fixture
def campaign(treasurer):
    return campaigns.open_campaign("Campanya de prova", by=treasurer)


def emails(template):
    return list(
        OutgoingEmail.objects.filter(template=template).values_list("to_address", flat=True)
    )


def days_ago(recipient, days):
    MandateCampaignRecipient.objects.filter(pk=recipient.pk).update(
        invited_at=timezone.now() - timedelta(days=days)
    )


# --- Obrir ---


def test_obrir_queda_al_registre(campaign, treasurer):
    assert campaign.invitation_text.kind == campaigns.INVITATION_TEXT
    assert AuditEntry.objects.get(action="payments.campaign.opened").actor_account == treasurer


def test_salvaguarda_amb_la_signatura_apagada_no_s_obre_ni_s_envia_res(
    settings, treasurer, campaign, anna
):
    settings.MANDATE_SIGNING_ENABLED = False
    campaigns.close_campaign(campaign, by=treasurer)
    with pytest.raises(campaigns.SigningDisabled):
        campaigns.open_campaign("Una altra", by=treasurer)
    with pytest.raises(campaigns.SigningDisabled):
        campaigns.send_invitations(campaign, by=treasurer)
    assert campaigns.send_due_reminders(today=timezone.localdate() + timedelta(days=30)) == 0
    assert not OutgoingEmail.objects.exists()


def test_sense_creditor_o_sense_text_no_s_obre(settings, treasurer, monkeypatch):
    settings.SEPA_CREDITOR_IDENTIFIER = ""
    with pytest.raises(campaigns.NotReady):
        campaigns.open_campaign("Sense creditor", by=treasurer)
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    monkeypatch.setattr(campaigns, "INVITATION_TEXT", "text-que-no-existeix")
    with pytest.raises(campaigns.NotReady):
        campaigns.open_campaign("Sense text", by=treasurer)
    assert not MandateCampaign.objects.exists()


def test_p_211_una_sola_campanya_oberta(campaign, treasurer):
    with pytest.raises(campaigns.AlreadyOpen):
        campaigns.open_campaign("Segona", by=treasurer)
    campaigns.close_campaign(campaign, by=treasurer)
    assert campaigns.open_campaign("Segona", by=treasurer).name == "Segona"


# --- Convidar (CA-M05a-12) ---


def test_ca_m05a_12_nomes_es_convida_els_socis_actius_sense_metode(
    campaign, treasurer, anna, jordi
):
    prefer(jordi, treasurer, "pay_each_time")
    member_with_email("Pere", 401, "00000002W", status=Member.Status.PENDING)
    member_with_email("Laia", 502, "00000003A", status=Member.Status.UNPAID)
    make_member("Marc", number=603, document="00000004G")  # sense correu (P-199)

    assert campaigns.send_invitations(campaign, by=treasurer) == 1

    assert emails(INVITATION) == ["anna.prova@example.org"]
    email = OutgoingEmail.objects.get(template=INVITATION)
    assert "Text de prova de la invitació." in email.body_text
    assert "https://cris1954.cat/socis/pagaments/metode/" in email.body_text
    entry = AuditEntry.objects.get(action="payments.campaign.invitations_sent")
    assert entry.details == {"sent": 1, "text_version": 1}


def test_tornar_a_enviar_nomes_convida_els_que_falten(campaign, treasurer, anna):
    campaigns.send_invitations(campaign, by=treasurer)
    jordi = member_with_email("Jordi", 311, "00000001R")

    assert campaigns.send_invitations(campaign, by=treasurer) == 1
    assert sorted(emails(INVITATION)) == ["anna.prova@example.org", "jordi.prova@example.org"]
    assert campaign.recipients.filter(member=jordi).exists()


def test_una_campanya_tancada_no_envia_res(campaign, treasurer, anna):
    campaigns.close_campaign(campaign, by=treasurer)
    with pytest.raises(campaigns.Closed):
        campaigns.send_invitations(campaign, by=treasurer)
    with pytest.raises(campaigns.Closed):
        campaigns.close_campaign(campaign, by=treasurer)


def test_la_tasca_de_la_cua_envia_les_invitacions(campaign, treasurer, anna):
    tasks.send_campaign_invitations(campaign_id=campaign.pk, account_id=treasurer.pk)
    assert emails(INVITATION) == ["anna.prova@example.org"]


# --- Recordatoris (RN-M05a-14) ---


def test_recordatoris_als_7_i_als_14_dies_i_cap_mes(campaign, treasurer, anna):
    campaigns.send_invitations(campaign, by=treasurer)
    recipient = campaign.recipients.get()
    today = timezone.localdate(recipient.invited_at)

    assert campaigns.send_due_reminders(today=today + timedelta(days=6)) == 0
    assert campaigns.send_due_reminders(today=today + timedelta(days=7)) == 1
    assert campaigns.send_due_reminders(today=today + timedelta(days=8)) == 0
    assert campaigns.send_due_reminders(today=today + timedelta(days=14)) == 1
    assert campaigns.send_due_reminders(today=today + timedelta(days=40)) == 0
    recipient.refresh_from_db()
    assert recipient.reminders_sent == 2
    assert emails(REMINDER) == ["anna.prova@example.org"] * 2


def test_ca_m05a_18_els_dies_dels_recordatoris_son_l_ajust_vc_11(
    campaign,
    treasurer,
    anna,
    make_admin,  # noqa: F811
):
    tresorer = make_admin(Role.Code.TREASURER)
    for wrong in ([0, 10], [5, 61]):
        with pytest.raises(ValidationError):
            business_settings.change(campaigns.REMINDER_DAYS, wrong, tresorer)
    with pytest.raises(Http404):  # VC-11: només el Tresorer
        business_settings.change(
            campaigns.REMINDER_DAYS, [5, 10], make_admin(Role.Code.ADMINISTRATOR)
        )
    business_settings.change(campaigns.REMINDER_DAYS, [5, 10], tresorer, note="Prova")
    entry = AuditEntry.objects.get(
        action=business_settings.ACTION_CHANGED, field=campaigns.REMINDER_DAYS
    )
    assert (entry.old_value, entry.new_value) == ([7, 14], [5, 10])

    campaigns.send_invitations(campaign, by=treasurer)
    today = timezone.localdate(campaign.recipients.get().invited_at)
    sent = [campaigns.send_due_reminders(today=today + timedelta(days=n)) for n in range(4, 15)]
    assert sent == [0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0]  # dies 5 i 10
    page = client_for(tresorer).get(reverse("administration:payments_campaign"))
    assert "Dies des de la invitació: 5, 10" in page.content.decode()


def test_p_210_si_se_n_ha_saltat_un_nomes_n_envia_un(campaign, treasurer, anna):
    campaigns.send_invitations(campaign, by=treasurer)
    recipient = campaign.recipients.get()
    today = timezone.localdate(recipient.invited_at)

    assert campaigns.send_due_reminders(today=today + timedelta(days=20)) == 1
    recipient.refresh_from_db()
    assert recipient.reminders_sent == 2


def test_ca_m05a_12_cap_recordatori_despres_d_haver_triat(campaign, treasurer, anna, jordi):
    campaigns.send_invitations(campaign, by=treasurer)
    preferences.set_preference(anna, "pay_each_time", by=treasurer)
    today = timezone.localdate() + timedelta(days=7)

    assert campaigns.send_due_reminders(today=today) == 1
    assert emails(REMINDER) == ["jordi.prova@example.org"]
    answered = campaign.recipients.get(member=anna)
    assert (answered.answer, answered.answered_at is not None) == ("pay_each_time", True)


def test_ni_recordatoris_a_qui_ja_no_es_actiu_ni_amb_la_campanya_tancada(
    campaign, treasurer, anna, jordi
):
    campaigns.send_invitations(campaign, by=treasurer)
    Member.objects.filter(pk=jordi.pk).update(status=Member.Status.LEFT)
    today = timezone.localdate() + timedelta(days=7)
    assert emails(REMINDER) == []
    assert campaigns.send_due_reminders(today=today) == 1  # només l'Anna

    campaigns.close_campaign(campaign, by=treasurer)
    assert campaigns.send_due_reminders(today=today + timedelta(days=7)) == 0


def test_la_tasca_diaria_crida_el_servei(monkeypatch):
    periodic = tasks.app.periodic_registry.periodic_tasks[("payments.campaign_reminders", "")]
    assert periodic.cron == "30 9 * * *"
    called = []
    monkeypatch.setattr(campaigns, "send_due_reminders", lambda: called.append(True))
    tasks.campaign_reminders(timestamp=0)
    assert called == [True]


# --- Recompte i tancar ---


def test_recompte_per_resposta_i_tancar(campaign, treasurer, anna, jordi):
    status = campaigns.campaign_status(campaign)
    assert (status["no_answer"], status["active"], status["invited"]) == (2, 2, 0)

    campaigns.send_invitations(campaign, by=treasurer)
    preferences.set_preference(jordi, "pay_each_time", by=treasurer)
    status = campaigns.campaign_status(campaign)
    assert status == {
        "direct_debit": 0,
        "saved_card": 0,
        "pay_each_time": 1,
        "no_answer": 1,
        "active": 2,
        "invited": 2,
    }

    campaigns.close_campaign(campaign, by=treasurer)
    assert campaign.closed_at is not None
    assert AuditEntry.objects.get(action="payments.campaign.closed").details == status
