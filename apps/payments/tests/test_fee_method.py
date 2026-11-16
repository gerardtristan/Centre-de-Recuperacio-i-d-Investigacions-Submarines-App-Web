"""«Com pago la quota»: servei i pantalla (T-M05a-11; P-M05a-A; CA-M05a-01; P-134 i P-196,
opcions per defecte). Proveïdor fals; només dades inventades."""

from dataclasses import replace

import pytest
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_PERSONAL
from apps.core.models import AuditEntry, Person
from apps.members.models import Member
from apps.members.tests.test_cards import make_member
from apps.payments import preferences
from apps.payments.models import FeePaymentPreference, SepaMandate
from apps.payments.providers import fake
from apps.payments.tests import test_mandates
from apps.payments.tests.test_preferences import card
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
member, text, sign = test_mandates.member, test_mandates.text, test_mandates.sign
URL = reverse("payments:fee_method")
SET = "payments.fee_preference.set"


@pytest.fixture
def account(member):
    return active_account(member.person, "anna.prova@example.org")


def active_account(person, email):
    account = Account.objects.create_personal(person, email, PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    return account


@pytest.fixture
def tokenization(monkeypatch):
    original = fake.FakeProvider.capabilities
    monkeypatch.setattr(
        fake.FakeProvider, "capabilities", lambda self: replace(original(self), tokenization=True)
    )


@pytest.fixture
def client_of(login_as, account):
    return login_as(account, AREA_PERSONAL)


# --- Servei ---


def test_pagar_cada_vegada_es_desa_amb_data_compte_i_registre(member, account):
    preferences.set_preference(member, "pay_each_time", by=account)

    preference = FeePaymentPreference.objects.get(member=member)
    assert (preference.method, preference.set_by, preference.mandate) == (
        "pay_each_time",
        account,
        None,
    )
    entry = AuditEntry.objects.get(action=SET)
    assert (entry.old_value, entry.new_value) == (None, "pay_each_time")
    assert preferences.fee_payment_method(member) == "pay_each_time"

    preferences.set_preference(member, "pay_each_time", by=account)  # sense canvis
    assert AuditEntry.objects.filter(action=SET).count() == 1


def test_sense_resposta_el_servei_torna_none(member):
    assert preferences.fee_payment_method(member) is None


def test_domiciliacio_nomes_amb_un_mandat_actiu(sign, member, account):
    with pytest.raises(preferences.NeedsMandate):
        preferences.set_preference(member, "direct_debit", by=account)
    assert not FeePaymentPreference.objects.exists()

    mandate = sign()
    preferences.set_preference(member, "direct_debit", by=account)
    assert FeePaymentPreference.objects.get(member=member).mandate == mandate
    assert AuditEntry.objects.get(action=SET).details == {"mandate": mandate.reference}


def test_p_134_pagar_cada_vegada_no_revoca_el_mandat(sign, member, account):
    mandate = sign()
    preferences.set_preference(member, "direct_debit", by=account)
    preferences.set_preference(member, "pay_each_time", by=account)

    mandate.refresh_from_db()
    assert mandate.status == SepaMandate.Status.ACTIVE
    preference = FeePaymentPreference.objects.get(member=member)
    assert (preference.method, preference.mandate) == ("pay_each_time", None)


def test_ca_m05a_01_sense_tokenitzacio_la_targeta_guardada_no_es_pot_triar(member, account):
    assert preferences.offered_methods() == ["direct_debit", "pay_each_time"]
    card(member)
    with pytest.raises(preferences.MethodNotOffered):
        preferences.set_preference(member, "saved_card", by=account)
    with pytest.raises(preferences.MethodNotOffered):
        preferences.set_preference(member, "xec", by=account)
    assert not FeePaymentPreference.objects.exists()


def test_amb_tokenitzacio_la_targeta_guardada_demana_una_targeta_activa(
    tokenization, member, account
):
    assert preferences.offered_methods() == ["direct_debit", "saved_card", "pay_each_time"]
    card(member, provider_card_id="c-0", status="removed")
    with pytest.raises(preferences.NeedsSavedCard):
        preferences.set_preference(member, "saved_card", by=account)

    active = card(member)
    preferences.set_preference(member, "saved_card", by=account)
    assert FeePaymentPreference.objects.get(member=member).saved_card == active


# --- Pantalla ---


def test_ca_m05a_01_la_pantalla_nomes_mostra_el_que_ofereix_el_proveidor(client_of):
    html = client_of.get(URL).content.decode()

    assert 'value="saved_card"' not in html
    assert 'value="direct_debit"' in html and 'value="pay_each_time"' in html
    assert "Domiciliació bancària (recomanada)" in html
    assert "Encara no has triat com pagues la quota." in html


def test_amb_tokenitzacio_es_recomana_la_targeta_guardada(tokenization, client_of):
    html = client_of.get(URL).content.decode()

    assert "Targeta guardada (recomanada)" in html
    assert "Domiciliació bancària (recomanada)" not in html


def test_desar_pagar_cada_vegada_des_de_la_pantalla(client_of, member):
    response = client_of.post(URL, {"method": "pay_each_time"}, follow=True)

    assert FeePaymentPreference.objects.get(member=member).method == "pay_each_time"
    html = response.content.decode()
    assert "Hem desat com vols pagar la quota." in html
    assert 'value="pay_each_time" required checked' in html


def test_domiciliacio_sense_mandat_no_desa_res_i_ho_explica(client_of):
    response = client_of.post(URL, {"method": "direct_debit"}, follow=True)

    assert not FeePaymentPreference.objects.exists()
    assert "cal signar el mandat SEPA" in response.content.decode()


def test_una_opcio_que_no_s_ofereix_es_rebutja(client_of):
    response = client_of.post(URL, {"method": "saved_card"}, follow=True)

    assert not FeePaymentPreference.objects.exists()
    assert "Tria una de les opcions." in response.content.decode()


def test_p_134_amb_mandat_actiu_i_pagar_cada_vegada_diu_com_revocar_lo(sign, client_of, member):
    mandate = sign()
    client_of.post(URL, {"method": "pay_each_time"})

    html = client_of.get(URL).content.decode()
    assert f'El mandat <span class="codi">{mandate.reference}</span> continua actiu' in html
    assert "ES55" not in html  # cap IBAN, ni emmascarat


def test_domiciliacio_amb_mandat_mostra_la_referencia(sign, client_of, member):
    mandate = sign()
    client_of.post(URL, {"method": "direct_debit"})

    assert mandate.reference in client_of.get(URL).content.decode()


@pytest.mark.parametrize("status", [Member.Status.PENDING, Member.Status.LEFT])
def test_qui_no_es_soci_actiu_o_impagat_rep_no_trobat(login_as, member, account, status):
    Member.objects.filter(pk=member.pk).update(status=status)
    client = login_as(account, AREA_PERSONAL)

    assert client.get(URL).status_code == 404
    assert client.post(URL, {"method": "pay_each_time"}).status_code == 404
    assert not FeePaymentPreference.objects.exists()


def test_soci_impagat_hi_pot_triar(login_as, member, account):
    Member.objects.filter(pk=member.pk).update(status=Member.Status.UNPAID)

    assert login_as(account, AREA_PERSONAL).get(URL).status_code == 200


def test_una_persona_sense_soci_rep_no_trobat(login_as):
    person = Person.objects.create(first_name="Pau", last_name="Prova", origin=Person.Origin.WEB)
    other = active_account(person, "pau.prova@example.org")

    assert login_as(other, AREA_PERSONAL).get(URL).status_code == 404


def test_sense_sessio_porta_a_l_entrada(client):
    response = client.get(URL)

    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]


def test_nomes_es_desa_la_preferencia_del_soci_de_la_sessio(client_of, member):
    other = make_member("Jordi", number=311, document="00000001R")
    client_of.post(URL, {"method": "pay_each_time", "member": other.pk})

    assert list(FeePaymentPreference.objects.values_list("member", flat=True)) == [member.pk]
