"""Pagaments de convidats amb l'enllaç de la 00 (T-M05b-08; CA-M05b-09; decisió 021; RN-33,
CA-02.2, CA-02.4 i CA-02.9 de la 00). Proveïdor fals, sense xarxa. Només dades inventades."""

import re

import pytest
from django.test import Client
from django.urls import reverse

from apps.core import audit, charges, guest_links
from apps.core.models import AuditEntry, Charge, Department, OutgoingEmail, Payment
from apps.payments import checkout, receipts
from apps.payments.models import PaymentAttempt as Attempt
from apps.payments.models import Receipt
from apps.payments.providers import fake
from apps.payments.tests.test_checkout import SITE
from apps.payments.tests.test_processing import notify, run_queue, transit  # noqa: F401

pytestmark = pytest.mark.django_db
SYSTEM = audit.system("proves")
SCREEN = reverse("payments:guest_charge")
EMAIL = "mar.convidada@example.org"
IBAN = "ES00 0000 0000 0000 0000 0000"  # inventat: cap compte real


@pytest.fixture(autouse=True)
def configured(settings):
    settings.PUBLIC_SITE_URL = SITE
    settings.CLUB_IBAN_TRANSFERENCIES = IBAN
    fake.reset()
    yield
    fake.reset()


def guest_charge(make_person, concept="Curs Open Water (inventat)"):
    person = make_person("Mar", "Convidada", contact_email=EMAIL)
    general = Department.objects.get(name=Department.GENERAL)
    return charges.create_charge(
        person,
        kind=Charge.Kind.ENROLMENT,
        amount_cents=12000,
        concept=concept,
        origin="proves",
        department=general,
        by=SYSTEM,
    )


@pytest.fixture
def charge(make_person):
    return guest_charge(make_person)


@pytest.fixture
def link(charge):
    return guest_links.create(charge.person, charge, by=SYSTEM)


@pytest.fixture
def guest(link):
    """El navegador del convidat, amb l'enllaç del correu obert (la sessió en desa l'id)."""
    body = OutgoingEmail.objects.filter(template=guest_links.EMAIL_TEMPLATE).latest("pk").body_text
    token = re.search(r"/convidat/([\w-]+)/", body).group(1)
    client = Client()
    assert client.get(reverse("core:guest_link", args=[token])).status_code == 302
    return client


def pay(client, method="card"):
    return client.post(reverse(f"payments:guest_pay_{method}"))


class TestGuestPays:
    def test_ca_m05b_09_card_goes_to_the_provider_with_the_link_and_no_account(
        self, guest, link, charge
    ):
        html = guest.get(SCREEN).content.decode()
        assert "120,00" in html and "Paga amb targeta" in html
        assert "Mar" not in html and EMAIL not in html  # cap dada personal (CA-02.2)

        response = pay(guest)

        attempt = Attempt.objects.get()
        assert response["Location"] == f"{SITE}{fake.PAY_PATH}{attempt.provider_order_id}/"
        assert attempt.guest_link == link and attempt.started_by is None
        assert attempt.amount_cents == 12000 and attempt.status == Attempt.Status.IN_PROGRESS
        entry = AuditEntry.objects.get(action="payments.attempt_created")
        assert entry.actor_kind == AuditEntry.ActorKind.GUEST
        assert entry.actor_person == charge.person
        assert entry.actor_origin == f"guest_link:{link.pk}"

    def test_ca_02_9_the_return_says_confirming_and_changes_nothing(self, guest, charge):
        pay(guest)
        html = guest.get(SCREEN + "?tornada=ok").content.decode()
        assert "Estem confirmant el pagament" in html and "Pagat" not in html
        charge.refresh_from_db()
        assert charge.status == Charge.Status.PENDING and not Payment.objects.exists()

    def test_the_provider_returns_the_browser_to_the_guest_screen(self):
        assert checkout.GUEST_RETURN_PATH.format(result="ok") == SCREEN + "?tornada=ok"

    def test_rn_33_the_verified_notification_pays_and_links_it_to_the_profile(
        self,
        guest,
        charge,
        transit,  # noqa: F811
    ):
        pay(guest)
        attempt = Attempt.objects.get()
        notify(attempt)
        run_queue()

        charge.refresh_from_db()
        assert charge.status == Charge.Status.PAID
        assert Payment.objects.get().charge.person == charge.person
        receipt = Receipt.objects.get(attempt=attempt)
        email = OutgoingEmail.objects.get(template=receipts.PAID_TEMPLATE)
        assert email.to_address == EMAIL and "/pagaments/convidat/rebut/" in email.body_text

        # CA-02.4: amb el càrrec pagat, només l'estat i el rebut; no es torna a pagar.
        html = guest.get(SCREEN).content.decode()
        assert "Pagat" in html and "Paga amb targeta" not in html
        assert reverse("payments:guest_receipt") in html
        assert receipt.number in guest.get(reverse("payments:guest_receipt")).content.decode()
        assert pay(guest)["Location"] == SCREEN and Attempt.objects.count() == 1

    def test_transfer_shows_the_club_iban_and_the_reference(self, guest):
        assert pay(guest, "transfer")["Location"] == SCREEN
        html = guest.get(SCREEN).content.decode()
        assert "Esperant la transferència" in html and "ES00 0000" in html
        assert Attempt.objects.get().method == Attempt.Method.TRANSFER

    def test_the_status_fragment_is_the_guest_one(self, guest):
        pay(guest)
        html = guest.get(reverse("payments:guest_status"), headers={"HX-Request": "true"})
        assert f'hx-get="{reverse("payments:guest_status")}"' in html.content.decode()


class TestOnlyWithAWorkingLink:
    """V-02 i RN-31: el servidor torna a comprovar l'enllaç a cada petició; sense, a la pàgina
    del convidat de la 00, que no diu per què."""

    @pytest.mark.parametrize(
        "name", ["guest_charge", "guest_status", "guest_receipt", "guest_pay_card"]
    )
    def test_without_a_link_nothing_is_shown(self, name, charge):
        client = Client()
        url = reverse(f"payments:{name}")
        response = client.post(url) if "pay" in name else client.get(url)
        assert response.status_code == 302 and response["Location"] == reverse("core:guest")
        assert not Attempt.objects.exists()

    def test_htmx_without_a_link_redirects_the_whole_page(self):
        response = Client().get(reverse("payments:guest_status"), headers={"HX-Request": "true"})
        assert response.status_code == 204 and response["HX-Redirect"] == reverse("core:guest")

    def test_a_revoked_link_no_longer_pays(self, guest, link):
        guest_links.revoke(link, by=SYSTEM)
        assert pay(guest)["Location"] == reverse("core:guest")
        assert not Attempt.objects.exists()

    def test_the_service_only_takes_a_working_link_of_that_charge(self, link, charge, make_person):
        other = guest_charge(make_person, concept="Sortida (inventada)")
        with pytest.raises(checkout.NotOwnCharge):
            checkout.start_payment(other, "card", link)
        guest_links.resend(link, by=SYSTEM)  # l'anterior queda substituït
        with pytest.raises(checkout.NotOwnCharge):
            checkout.start_payment(charge, "card", link)
        assert not Attempt.objects.exists()

    def test_a_paid_charge_without_receipt_shows_the_state(self, guest, charge):
        payment = Payment.objects.create(charge=charge, method="card", amount_cents=12000)
        charges.mark_paid(charge, payment, origin="provider", by=SYSTEM)
        response = guest.get(reverse("payments:guest_receipt"))
        assert response["Location"] == SCREEN
        assert "Pagat" in guest.get(SCREEN).content.decode()
