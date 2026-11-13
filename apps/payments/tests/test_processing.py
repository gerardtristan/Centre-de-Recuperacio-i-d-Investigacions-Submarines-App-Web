"""Processament de les notificacions del proveïdor i xarxa de seguretat (T-M05b-05; P-M05b-D;
RN-M05b-03, 05, 06 i 08; CA-M05b-03 a 07; L-M05b-01). Proveïdor fals, sense xarxa. Només dades
inventades.

Cada prova fa el camí sencer: el soci obre l'intent (`start_payment`), el proveïdor envia la
notificació signada a l'endpoint, que la desa i la posa a la cua, i la cua la processa."""

import json
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.test import Client
from django.urls import reverse
from procrastinate.contrib.django.models import ProcrastinateJob

from apps.accounts.models import Account
from apps.core import audit, charges
from apps.core.models import AuditEntry, Charge, Department, Payment
from apps.members.models import Member, MemberCard
from apps.members.tests.test_cards import add_fee, make_member
from apps.payments import checkout, processing, services
from apps.payments.models import PaymentAttempt as Attempt
from apps.payments.models import ProviderEvent
from apps.payments.providers import base, fake
from apps.treasury.models import CostCentre, Movement, TreasuryAccount
from conftest import PASSWORD, CommittedDataTestCase, run_together

pytestmark = pytest.mark.django_db
R = ProviderEvent.Result
S = Attempt.Status
URL = reverse("payments:provider_notification", args=["fake"])
URLS = base.OrderUrls("https://example.org/n", "https://example.org/ok", "https://example.org/ko")


@pytest.fixture(autouse=True)
def clean_orders(settings):
    settings.PUBLIC_SITE_URL = "https://socis.example.org"
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def transit():
    """RN-T08: el compte de trànsit del proveïdor on va l'ingrés (el crea la T-M04-17)."""
    return TreasuryAccount.objects.create(
        name="Trànsit del proveïdor de proves", kind="transit", provider_code="fake"
    )


@pytest.fixture
def member():
    """Soci aprovat, pendent de pagar la primera quota (P-M01-A)."""
    return make_member(status=Member.Status.PENDING)


@pytest.fixture
def fee(member):
    return add_fee(member)


@pytest.fixture
def account(member):
    account = Account.objects.create_personal(member.person, "anna.prova@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    return account


@pytest.fixture
def attempt(fee, account):
    start = checkout.start_payment(fee.charge, "card", account)
    return Attempt.objects.get(pk=start.attempt_id)


def notify(attempt, status=base.PAID, *, event_id="e-1", **overrides):
    """El proveïdor envia la notificació a l'endpoint. `overrides`: camps del cos canviats i
    tornats a signar, com ho faria el proveïdor (import o moneda que no quadren)."""
    body, headers = fake.FakeProvider().notification(
        attempt.provider_order_id, status, event_id=event_id
    )
    if overrides:
        body = json.dumps({**json.loads(body), **overrides}, sort_keys=True).encode()
        headers = {fake.SIGNATURE_HEADER: fake.sign(body)}
    return Client().post(URL, data=body, content_type="application/json", headers=headers)


def run_queue():
    """El que fa el procés de la cua: cada notificació a la cua, en ordre."""
    jobs = ProcrastinateJob.objects.filter(task_name="payments.process_notification")
    return [processing.process_notification(job.args["event_id"]) for job in jobs.order_by("id")]


def state(attempt, fee):
    attempt.refresh_from_db()
    fee.charge.refresh_from_db()
    return attempt.status, fee.charge.status


def incomes():
    return Movement.objects.filter(kind=Movement.Kind.INCOME)


class TestPaid:
    def test_ca_m05b_03_a_valid_notification_pays_attempt_charge_treasury_and_member(
        self, attempt, fee, member, transit
    ):
        assert notify(attempt).status_code == 200
        event = ProviderEvent.objects.get()
        job = ProcrastinateJob.objects.get(task_name="payments.process_notification")
        assert (job.args, job.queue_name, event.result) == (
            {"event_id": event.pk},
            "payments",
            R.RECEIVED,
        )
        assert state(attempt, fee) == (S.IN_PROGRESS, Charge.Status.PENDING)  # encara a la cua

        assert run_queue() == [R.PROCESSED]

        assert state(attempt, fee) == (S.PAID, Charge.Status.PAID)
        event.refresh_from_db()
        assert event.result == R.PROCESSED and event.processed_at
        (payment,) = Payment.objects.filter(charge=fee.charge)
        assert (payment.method, payment.amount_cents, payment.provider_reference) == (
            "card",
            9000,
            attempt.provider_order_id,
        )
        # CA-T03.1: l'ingrés, de l'import del càrrec, al trànsit, amb departament i centre de cost.
        (income,) = incomes()
        assert (income.payment, income.amount_cents, income.account) == (payment, 9000, transit)
        general = Department.objects.get(name=Department.GENERAL)
        assert income.department == general
        assert income.cost_centre == CostCentre.objects.get(
            department=general, name="Quotes de socis"
        )
        # El camí del 01 (`on_fee_paid`): el soci passa a actiu i té carnet.
        member.refresh_from_db()
        assert member.status == Member.Status.ACTIVE
        assert MemberCard.objects.filter(member=member, revoked_at=None).count() == 1
        system = AuditEntry.objects.filter(actor_origin=processing.ORIGIN)
        assert {"payments.attempt_status_changed", "charges.status_changed"} <= set(
            system.values_list("action", flat=True)
        )

    def test_it_is_the_service_of_the_contract(self):
        assert services.process_notification is processing.process_notification

    def test_a_notification_that_is_not_paid_yet_changes_nothing(self, attempt, fee, transit):
        notify(attempt, base.PENDING)
        assert run_queue() == [R.PROCESSED]
        assert state(attempt, fee) == (S.IN_PROGRESS, Charge.Status.PENDING)


class TestSignature:
    def test_an_invalid_signature_is_never_processed(self, attempt, fee, transit):
        body, _headers = fake.FakeProvider().notification(attempt.provider_order_id, base.PAID)
        forged = {fake.SIGNATURE_HEADER: fake.sign(body, key="una-altra-clau")}
        response = Client().post(URL, data=body, content_type="application/json", headers=forged)
        assert response.status_code == 400
        assert not ProcrastinateJob.objects.filter(task_name="payments.process_notification")
        assert ProviderEvent.objects.get().result == R.REJECTED_SIGNATURE
        processing.safety_net()  # tampoc no l'agafa la xarxa de seguretat: no és «rebuda»
        assert state(attempt, fee) == (S.IN_PROGRESS, Charge.Status.PENDING)
        assert not Payment.objects.exists() and not incomes().exists()


class TestIdempotent:
    def test_ca_m05b_04_the_same_notification_twice_pays_and_records_once(
        self, attempt, fee, transit
    ):
        notify(attempt, event_id="e-1")
        notify(attempt, event_id="e-1")
        assert run_queue() == [R.PROCESSED]  # la repetida ni tan sols arriba a la cua
        event = ProviderEvent.objects.get(result=R.PROCESSED)
        assert processing.process_notification(event.pk) == R.PROCESSED  # la cua la repeteix
        assert Payment.objects.count() == 1 and incomes().count() == 1
        assert AuditEntry.objects.filter(action="members.status_changed").count() == 1
        assert state(attempt, fee) == (S.PAID, Charge.Status.PAID)

    def test_ca_m05b_04_another_event_of_the_same_paid_order_adds_nothing(
        self, attempt, fee, transit
    ):
        notify(attempt, event_id="e-1")
        notify(attempt, event_id="e-2")
        assert run_queue() == [R.PROCESSED, R.PROCESSED]
        assert Payment.objects.count() == 1 and incomes().count() == 1

    def test_ca_m05b_04_a_denial_that_arrives_after_the_payment_is_ignored(
        self, attempt, fee, transit
    ):
        notify(attempt, base.PAID, event_id="e-1")
        notify(attempt, base.DENIED, event_id="e-0")
        run_queue()
        assert state(attempt, fee) == (S.PAID, Charge.Status.PAID)
        assert Payment.objects.count() == 1


class TestBrowser:
    def test_the_notification_arrives_before_the_browser_returns(
        self, attempt, fee, account, transit
    ):
        notify(attempt)
        run_queue()
        client = Client()
        client.force_login(account)
        client.get(checkout.RETURN_PATH.format(charge=fee.charge.pk, result="ok"))
        assert state(attempt, fee) == (S.PAID, Charge.Status.PAID)
        assert Payment.objects.count() == 1 and incomes().count() == 1

    def test_rn_m05b_05_the_browser_return_alone_never_pays(self, attempt, fee, account, transit):
        client = Client()
        client.force_login(account)
        client.get(checkout.RETURN_PATH.format(charge=fee.charge.pk, result="ok"))
        assert state(attempt, fee) == (S.IN_PROGRESS, Charge.Status.PENDING)
        assert not Payment.objects.exists() and not incomes().exists()
        # Cap vista no crida el processament ni marca res com a pagat: només ho fa la cua.
        apps_dir = Path(processing.__file__).parents[1]
        views = [*apps_dir.glob("*/views.py"), *apps_dir.glob("*/views/*.py")]
        assert views
        for view in views:
            text = view.read_text(encoding="utf-8")
            assert "processing" not in text and "mark_paid" not in text, view


class TestToReview:
    @pytest.mark.parametrize("override", [{"amount_cents": 8000}, {"currency": "USD"}])
    def test_ca_m05b_05_an_amount_or_currency_that_does_not_match(
        self, attempt, fee, transit, override
    ):
        notify(attempt, **override)
        assert run_queue() == [R.TO_REVIEW]
        assert state(attempt, fee) == (S.TO_REVIEW, Charge.Status.PENDING)
        assert "import o la moneda" in attempt.review_reason
        assert not Payment.objects.exists() and not incomes().exists()

    def test_an_unknown_order_goes_to_review(self, transit):
        provider = fake.FakeProvider()
        charge = SimpleNamespace(pk=1, amount_cents=9000, currency="EUR")
        order = provider.create_order(charge, base.CARD, URLS, uuid4())  # cap intent la coneix
        body, headers = provider.notification(order.external_id, base.PAID)
        Client().post(URL, data=body, content_type="application/json", headers=headers)
        assert run_queue() == [R.TO_REVIEW]
        event = ProviderEvent.objects.get()
        entry = AuditEntry.objects.get(action=processing.TO_REVIEW)
        assert entry.target_id == str(event.pk) and "ordre coneguda" in entry.reason

    def test_ca_m05b_07_a_late_confirmation_of_a_charge_already_paid_is_a_duplicate(
        self, attempt, fee, transit
    ):
        # El tresorer ha conciliat una transferència del mateix càrrec mentre l'intent era en curs.
        transfer = Payment.objects.create(
            charge=fee.charge, method=Payment.Method.TRANSFER, amount_cents=9000
        )
        charges.mark_paid(fee.charge, transfer, origin="reconciliation", by=audit.system("proves"))
        notify(attempt)
        assert run_queue() == [R.TO_REVIEW]
        assert state(attempt, fee) == (S.TO_REVIEW, Charge.Status.PAID)
        assert attempt.review_reason.startswith("Pagament duplicat")
        assert list(Payment.objects.all()) == [transfer]  # cap pagament nou
        assert not incomes().exists()  # el de la transferència l'apunta la conciliació

    def test_p_82_a_payment_of_an_attempt_already_closed_does_not_reopen_it(
        self, attempt, fee, transit
    ):
        notify(attempt, base.DENIED, event_id="e-1")
        notify(attempt, base.PAID, event_id="e-2")
        assert run_queue() == [R.PROCESSED, R.TO_REVIEW]
        assert state(attempt, fee) == (S.FAILED, Charge.Status.PENDING)
        entry = AuditEntry.objects.get(action=processing.TO_REVIEW)
        assert entry.target_id == str(ProviderEvent.objects.get(external_id="e-2").pk)
        assert not Payment.objects.exists()


class TestClosed:
    @pytest.mark.parametrize(
        ("status", "closed"), [(base.DENIED, S.FAILED), (base.EXPIRED, S.EXPIRED)]
    )
    def test_a_denied_or_expired_order_closes_the_attempt_and_the_charge_stays_pending(
        self, attempt, fee, transit, status, closed
    ):
        notify(attempt, status)
        notify(attempt, base.EXPIRED, event_id="e-2")  # una altra, desordenada: no canvia res
        assert run_queue() == [R.PROCESSED, R.PROCESSED]
        assert state(attempt, fee) == (closed, Charge.Status.PENDING)

    def test_the_queue_tasks_call_the_service(self, attempt, fee, transit, monkeypatch):
        from apps.payments import tasks

        notify(attempt)
        tasks.process_notification(event_id=ProviderEvent.objects.get().pk)
        assert state(attempt, fee) == (S.PAID, Charge.Status.PAID)
        called = []
        monkeypatch.setattr(processing, "safety_net", lambda: called.append(True))
        tasks.safety_net(timestamp=0)
        assert called == [True]


class TestError:
    def test_an_error_rolls_everything_back_and_the_safety_net_recovers_it(
        self, attempt, fee, monkeypatch
    ):
        notify(attempt)  # sense compte de trànsit: l'ingrés no es pot apuntar (RN-T08)
        assert run_queue() == [R.ERROR]
        assert state(attempt, fee) == (S.IN_PROGRESS, Charge.Status.PENDING)
        assert not Payment.objects.exists() and not incomes().exists()
        entry = AuditEntry.objects.get(action=processing.ERROR)
        assert entry.details == {"error": "IncomeAccountUnavailable"}
        assert processing.process_notification(ProviderEvent.objects.get().pk) == R.ERROR

        TreasuryAccount.objects.create(name="Trànsit", kind="transit", provider_code="fake")
        monkeypatch.setattr(processing, "SAFETY_NET_AGE", timedelta(0))
        processing.safety_net()
        assert state(attempt, fee) == (S.PAID, Charge.Status.PAID)
        assert incomes().count() == 1


class TestSafetyNet:
    @pytest.fixture(autouse=True)
    def no_age(self, monkeypatch):
        monkeypatch.setattr(processing, "SAFETY_NET_AGE", timedelta(0))

    def test_an_order_paid_without_notification_is_closed_by_the_safety_net(
        self, attempt, fee, transit
    ):
        fake.FakeProvider().notification(attempt.provider_order_id, base.PAID)  # mai no arriba
        processing.safety_net()
        assert state(attempt, fee) == (S.PAID, Charge.Status.PAID)
        assert Payment.objects.count() == 1 and incomes().count() == 1
        processing.safety_net()
        assert Payment.objects.count() == 1 and incomes().count() == 1

    def test_a_pending_order_is_left_alone(self, attempt, fee, transit):
        processing.safety_net()
        assert state(attempt, fee) == (S.IN_PROGRESS, Charge.Status.PENDING)

    def test_l_m05b_01_an_order_that_cannot_be_read_goes_to_review(self, attempt, fee, transit):
        fake.reset()  # el proveïdor ja no la coneix
        processing.safety_net()
        assert state(attempt, fee) == (S.TO_REVIEW, Charge.Status.PENDING)
        assert "consultar l'ordre" in attempt.review_reason

    def test_a_notification_left_in_the_queue_is_processed(self, attempt, fee, transit):
        notify(attempt)  # la feina de la cua s'ha perdut
        processing.safety_net()
        assert ProviderEvent.objects.get().result == R.PROCESSED
        assert state(attempt, fee) == (S.PAID, Charge.Status.PAID)

    def test_a_recent_order_waits(self, attempt, fee, transit, monkeypatch):
        monkeypatch.setattr(processing, "SAFETY_NET_AGE", timedelta(minutes=60))
        fake.FakeProvider().notification(attempt.provider_order_id, base.PAID)
        processing.safety_net()
        assert state(attempt, fee) == (S.IN_PROGRESS, Charge.Status.PENDING)

    def test_an_error_in_one_order_does_not_stop_the_others(self, attempt, fee, monkeypatch):
        fake.FakeProvider().notification(attempt.provider_order_id, base.PAID)
        processing.safety_net()  # sense compte de trànsit: falla, queda al registre i continua
        assert state(attempt, fee) == (S.IN_PROGRESS, Charge.Status.PENDING)


class TestSimultaneous(CommittedDataTestCase):
    def test_ca_m05b_04_two_events_of_the_same_order_at_once_pay_once(self):
        fake.reset()
        TreasuryAccount.objects.create(name="Trànsit", kind="transit", provider_code="fake")
        member = make_member(status=Member.Status.PENDING)
        fee = add_fee(member)
        account = Account.objects.create_personal(member.person, "anna@example.org", PASSWORD)
        account.status = Account.Status.ACTIVE
        account.save()
        attempt = Attempt.objects.get(
            pk=checkout.start_payment(fee.charge, "card", account).attempt_id
        )
        notify(attempt, event_id="e-1")
        notify(attempt, event_id="e-2")
        first, second = ProviderEvent.objects.order_by("pk").values_list("pk", flat=True)

        results = run_together(
            [lambda pk=pk: processing.process_notification(pk) for pk in (first, second)]
        )

        assert results == [R.PROCESSED, R.PROCESSED]
        assert state(attempt, fee) == (S.PAID, Charge.Status.PAID)
        assert Payment.objects.count() == 1 and incomes().count() == 1
        fake.reset()
