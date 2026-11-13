"""Començar un pagament amb targeta (T-M05b-04, tall de targeta; P-M05b-A, pas 2; RN-M05b-02
i 04; CA-M05b-01 i 08). Proveïdor fals, sense xarxa. Només dades inventades.

CA-M05b-02 (la tornada del navegador) no és aquí: arriba amb la pantalla de pagament."""

import dataclasses
import inspect

import pytest
from django.urls import reverse

from apps.accounts.models import Account
from apps.core import audit, charges
from apps.core.models import AuditEntry, Charge, Department, GuestLink, Payment, Person
from apps.payments import attempts, checkout, services
from apps.payments.models import PaymentAttempt as Attempt
from apps.payments.providers import base, fake
from apps.payments.tests.provider_contract import FORBIDDEN_FIELDS
from conftest import PASSWORD, CommittedDataTestCase, run_together

pytestmark = pytest.mark.django_db
S = Attempt.Status
SYSTEM = audit.system("proves")
SITE = "https://socis.example.org"


def new_charge(person, amount_cents=9000):
    general = Department.objects.get(name=Department.GENERAL)
    fields = {"kind": "fee", "amount_cents": amount_cents, "concept": "Inventat"}
    return charges.create_charge(person, department=general, by=SYSTEM, origin="proves", **fields)


@pytest.fixture(autouse=True)
def clean_orders(settings):
    settings.PUBLIC_SITE_URL = SITE
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def charge(personal_account):
    return new_charge(personal_account.person)


@pytest.fixture
def orders(monkeypatch):
    """El que rep el proveïdor a cada `create_order`: (import del càrrec, mètode, adreces, clau)."""
    received = []
    create = fake.FakeProvider._create_order

    def spy(self, charge, method, urls, idempotency_key):
        received.append((charge.amount_cents, method, urls, idempotency_key))
        return create(self, charge, method, urls, idempotency_key)

    monkeypatch.setattr(fake.FakeProvider, "_create_order", spy)
    return received


def nothing_started(charge, orders):
    charge.refresh_from_db()
    return not orders and not Attempt.objects.exists() and charge.status == Charge.Status.PENDING


class TestCardOrder:
    def test_ca_m05b_01_the_order_is_created_on_the_server_with_the_charge_amount(
        self, charge, personal_account, orders
    ):
        start = checkout.start_payment(charge, "card", personal_account)

        attempt = Attempt.objects.get()
        assert (attempt.status, attempt.method, attempt.amount_cents) == (
            S.IN_PROGRESS,
            "card",
            9000,
        )
        assert attempt.started_by == personal_account
        [(amount, method, _urls, key)] = orders
        assert (amount, method, key) == (9000, "card", attempt.idempotency_key)
        order = fake.FakeProvider().get_order(attempt.provider_order_id)
        assert (order.amount_cents, order.status, attempt.provider_code) == (
            9000,
            "pending",
            "fake",
        )
        # La pantalla només rep on ha d'anar el navegador: la pàgina del proveïdor.
        assert start == checkout.PaymentStart(
            attempt_id=attempt.pk,
            kind=checkout.REDIRECT,
            amount_cents=9000,
            url=f"{SITE}{fake.PAY_PATH}{attempt.provider_order_id}/",
        )

    def test_ca_m05b_01_the_amount_never_comes_from_the_caller(
        self, charge, personal_account, orders
    ):
        """RN-M05b-02: ni un paràmetre per a l'import ni una còpia del càrrec amb un altre."""
        assert list(inspect.signature(checkout.start_payment).parameters) == [
            "charge",
            "method",
            "actor",
        ]
        charge.amount_cents = 1  # còpia en memòria manipulada; a la base de dades hi ha 9000
        start = checkout.start_payment(charge, "card", personal_account)
        assert (start.amount_cents, orders[0][0], Attempt.objects.get().amount_cents) == (
            9000,
            9000,
            9000,
        )

    def test_ca_m05b_01_no_card_field_travels_through_the_platform(self):
        names = {field.name for field in dataclasses.fields(checkout.PaymentStart)}
        assert names == {"attempt_id", "kind", "amount_cents", "url"}
        assert not names & set(FORBIDDEN_FIELDS)
        assert not [n for n in inspect.signature(checkout.start_payment).parameters if "card" in n]

    def test_ca_m05b_01_the_provider_decides_between_its_page_and_its_embedded_field(
        self, charge, personal_account, monkeypatch
    ):
        embedded = dataclasses.replace(fake.FakeProvider().capabilities(), embedded_field=True)
        monkeypatch.setattr(fake.FakeProvider, "capabilities", lambda self: embedded)
        assert checkout.start_payment(charge, "card", personal_account).kind == checkout.IFRAME

    def test_rn_m05b_05_starting_a_payment_never_pays_the_charge(self, charge, personal_account):
        """«Pagat» només arriba per la notificació verificada (T-M05b-05)."""
        checkout.start_payment(charge, "card", personal_account)
        charge.refresh_from_db()
        assert charge.status == Charge.Status.PENDING
        assert not Payment.objects.exists()
        assert not Attempt.objects.filter(status=S.PAID).exists()

    def test_the_provider_is_told_where_to_notify_and_where_to_send_the_browser_back(
        self, charge, personal_account, orders
    ):
        checkout.start_payment(charge, "card", personal_account)
        urls = orders[0][2]
        assert urls == base.OrderUrls(
            notification=SITE + reverse("payments:provider_notification", args=["fake"]),
            return_ok=f"{SITE}/socis/pagaments/{charge.pk}/?tornada=ok",
            return_ko=f"{SITE}/socis/pagaments/{charge.pk}/?tornada=ko",
        )

    def test_it_is_left_in_the_activity_log_with_the_account_that_pays(
        self, charge, personal_account
    ):
        checkout.start_payment(charge, "card", personal_account)
        attempt = Attempt.objects.get()
        entries = AuditEntry.objects.filter(target_type="payments.paymentattempt")
        assert [entry.action for entry in entries.order_by("pk")] == [
            "payments.attempt_created",
            "payments.attempt_status_changed",
            "payments.order_created",
        ]
        assert {entry.actor_account for entry in entries} == {personal_account}
        last = entries.order_by("pk").last()
        assert last.details == {"provider": "fake", "order": attempt.provider_order_id}

    def test_it_is_the_service_the_module_offers(self):
        assert services.start_payment is checkout.start_payment
        assert services.PaymentStart is checkout.PaymentStart


class TestOneAttemptInProgress:
    def test_ca_m05b_08_with_an_attempt_in_progress_the_new_one_waits(
        self, charge, personal_account, orders
    ):
        """RN-M05b-04, opció conservadora: ni un segon intent ni una segona ordre."""
        checkout.start_payment(charge, "card", personal_account)
        with pytest.raises(attempts.AttemptInProgress):
            checkout.start_payment(charge, "card", personal_account)
        assert Attempt.objects.count() == 1
        assert len(orders) == 1

    def test_ca_m05b_08_the_database_index_also_stops_it(
        self, charge, personal_account, orders, monkeypatch
    ):
        """Si dues peticions passen alhora la comprovació, l'índex únic atura la segona abans
        que arribi al proveïdor, i no en queda cap intent a mitges."""
        checkout.start_payment(charge, "card", personal_account)
        monkeypatch.setattr(checkout, "_in_progress", lambda charge: False)
        with pytest.raises(attempts.AttemptInProgress):
            checkout.start_payment(charge, "card", personal_account)
        assert Attempt.objects.count() == 1
        assert len(orders) == 1

    @pytest.mark.parametrize("end", [S.FAILED, S.EXPIRED, S.ABANDONED])
    def test_ca_m05b_08_when_the_attempt_ends_a_new_one_can_start(
        self, charge, personal_account, orders, end
    ):
        first = checkout.start_payment(charge, "card", personal_account)
        attempts.transition(Attempt.objects.get(), end, by=SYSTEM)
        second = checkout.start_payment(charge, "card", personal_account)
        assert second.attempt_id != first.attempt_id
        assert second.url != first.url
        assert orders[0][3] != orders[1][3]  # una clau d'idempotència per intent


class TestTwoAtOnce(CommittedDataTestCase):
    """CA-M05b-08 amb dues peticions de debò, cadascuna amb la seva connexió."""

    def test_ca_m05b_08_two_requests_at_once_open_one_order(self):
        person = Person.objects.create(first_name="Núria", last_name="Coll", origin="web")
        account = Account.objects.create_personal(person, "nuria@example.org", PASSWORD)
        account.status = Account.Status.ACTIVE
        account.save()
        charge = new_charge(person)
        fake.reset()

        def pay():
            try:
                return checkout.start_payment(charge, "card", account).attempt_id
            except attempts.AttemptInProgress:
                return None

        results = run_together([pay, pay])
        attempt = Attempt.objects.get()
        assert sorted(results, key=str) == [attempt.pk, None]
        assert attempt.status == S.IN_PROGRESS
        assert len(fake._orders) == 1


class TestRefusals:
    @pytest.mark.parametrize("method", ["bizum", "transfer", "direct_debit", "saved_card", "", "x"])
    def test_only_card_in_this_slice(self, charge, personal_account, orders, method):
        with pytest.raises(attempts.MethodNotAllowed):
            checkout.start_payment(charge, method, personal_account)
        assert nothing_started(charge, orders)

    def test_a_method_the_provider_does_not_offer(
        self, charge, personal_account, orders, monkeypatch
    ):
        without = dataclasses.replace(fake.FakeProvider().capabilities(), card=False)
        monkeypatch.setattr(fake.FakeProvider, "capabilities", lambda self: without)
        with pytest.raises(attempts.MethodNotAllowed):
            checkout.start_payment(charge, "card", personal_account)
        assert nothing_started(charge, orders)

    def test_a_charge_that_is_not_pending(self, charge, personal_account, orders):
        charges.cancel(charge, "Duplicat (inventat)", by=SYSTEM)
        with pytest.raises(attempts.ChargeNotPayable):
            checkout.start_payment(charge, "card", personal_account)
        assert not orders
        assert not Attempt.objects.exists()

    def test_nobody_pays_the_charge_of_someone_else(self, charge, make_person, orders):
        """M05b-4, «per objecte»: el servei ho comprova encara que la pantalla ja ho faci."""
        other = Account.objects.create_personal(
            make_person("Pau", "Mas"), "pau@example.org", PASSWORD
        )
        other.status = Account.Status.ACTIVE  # el que l'atura és de qui és el càrrec
        other.save()
        with pytest.raises(checkout.NotOwnCharge):
            checkout.start_payment(charge, "card", other)
        assert issubclass(checkout.NotOwnCharge, attempts.ChargeNotPayable)
        assert nothing_started(charge, orders)

    @pytest.mark.parametrize("status", [Account.Status.PENDING, Account.Status.DISABLED])
    def test_an_account_that_is_not_active_pays_nothing(
        self, charge, personal_account, orders, status
    ):
        personal_account.status = status
        personal_account.save()
        with pytest.raises(checkout.NotOwnCharge):
            checkout.start_payment(charge, "card", personal_account)
        assert nothing_started(charge, orders)

    def test_without_an_account_nothing_starts(self, charge, orders):
        """El pagament de convidats és la T-M05b-08: mentrestant, un enllaç no paga."""
        link = GuestLink(person=charge.person, charge=charge)
        for actor in (None, link, SYSTEM):
            with pytest.raises(checkout.NotOwnCharge):
                checkout.start_payment(charge, "card", actor)
        assert nothing_started(charge, orders)

    def test_the_real_environment_without_authorization(
        self, charge, personal_account, orders, settings
    ):
        """RN-M05a-11: es rebutja abans d'obrir cap intent."""
        settings.PAYMENTS_ENVIRONMENT = base.LIVE
        with pytest.raises(base.LiveChargesNotAllowed):
            checkout.start_payment(charge, "card", personal_account)
        assert nothing_started(charge, orders)

    def test_no_provider_configured(self, charge, personal_account, orders, settings):
        settings.PAYMENTS_PROVIDER = ""
        with pytest.raises(base.ProviderNotConfigured):
            checkout.start_payment(charge, "card", personal_account)
        assert nothing_started(charge, orders)

    def test_if_the_provider_fails_nothing_is_left_and_it_can_be_tried_again(
        self, charge, personal_account, monkeypatch
    ):
        def broken(self, *args):
            raise base.ProviderError("sense resposta")

        with monkeypatch.context() as patch:
            patch.setattr(fake.FakeProvider, "_create_order", broken)
            with pytest.raises(base.ProviderError):
                checkout.start_payment(charge, "card", personal_account)
        assert not Attempt.objects.exists()
        assert not AuditEntry.objects.filter(target_type="payments.paymentattempt").exists()
        assert checkout.start_payment(charge, "card", personal_account).kind == checkout.REDIRECT
