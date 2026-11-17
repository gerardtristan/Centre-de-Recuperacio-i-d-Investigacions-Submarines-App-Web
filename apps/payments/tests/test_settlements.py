"""Liquidacions del proveïdor cap a la 04 (T-M05b-14; P-M05b-H; RN-T21; CA-T11.1 i CA-T11.2;
P-226, P-227). Proveïdor fals, sense xarxa. Només dades inventades."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core.models import AuditEntry, OutgoingEmail, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import settlements, tasks
from apps.payments.providers import base, fake
from apps.treasury import settlements as treasury
from apps.treasury.balances import balances
from apps.treasury.models import ProviderSettlement, TreasuryAccount
from apps.treasury.tests.test_settlements import collected

pytestmark = pytest.mark.django_db
Status = ProviderSettlement.Status
TODAY = timezone.localdate()


@pytest.fixture(autouse=True)
def clean_fake():
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def provider():
    return fake.FakeProvider()


@pytest.fixture
def two(make_person):
    person = make_person("Núria", "Coll")
    return collected(person, 9000, "fake-ord-a"), collected(person, 3500, "fake-ord-b")


def settle(provider, *operations, fees=120, days_ago=1, external_id="LIQ-001"):
    operations = operations or (("fake-ord-a", 9000), ("fake-ord-b", 3500))
    on = TODAY - timedelta(days=days_ago)
    return provider.settle(operations, fees_cents=fees, settled_on=on, external_id=external_id)


class TestImport:
    def test_a_settlement_reaches_treasury_and_is_confirmed(self, provider, two, make_admin):  # noqa: F811
        settle(provider)
        [settlement] = settlements.import_settlements()
        assert (settlement.provider_code, settlement.external_id, settlement.status) == (
            "fake",
            "LIQ-001",
            Status.RECEIVED,
        )
        assert (settlement.gross_cents, settlement.fees_cents, settlement.net_cents) == (
            12_500,
            120,
            12_380,
        )
        assert settlement.source == ProviderSettlement.Source.NOTIFICATION
        assert {item.payment for item in settlement.items.all()} == set(two)
        entry = AuditEntry.objects.get(action=treasury.RECORDED)
        assert (entry.actor_kind, entry.actor_origin) == ("system", settlements.ORIGIN)
        # CA-T11.1: en confirmar-la, comissions i traspàs; el trànsit queda a zero (M04-7).
        treasury.confirm(settlement, by=make_admin("treasurer"))
        transit = TreasuryAccount.objects.get(kind="transit", provider_code="fake")
        assert balances(TODAY).get(pk=transit.pk).balance_cents == 0

    def test_it_is_idempotent(self, provider, two):
        settle(provider)
        assert len(settlements.import_settlements()) == 1
        assert settlements.import_settlements() == []
        assert ProviderSettlement.objects.count() == 1

    def test_ca_t11_2_an_unknown_charge_goes_to_review(self, provider, two):
        settle(provider, ("fake-ord-a", 9000), ("fake-ord-x", 3500))
        [settlement] = settlements.import_settlements()
        assert settlement.status == Status.TO_REVIEW
        assert settlement.review_notes == [
            {"reference": "fake-ord-x", "problem": "unknown_payment"}
        ]

    def test_p_226_only_the_last_days_are_asked_for(self, provider, two):
        settle(provider, ("fake-ord-a", 9000), fees=50, days_ago=8, external_id="OLD")
        settle(provider, ("fake-ord-b", 3500), fees=20, days_ago=7, external_id="EDGE")
        assert [s.external_id for s in settlements.import_settlements()] == ["EDGE"]

    def test_p_227_one_that_does_not_add_up_is_logged_and_the_rest_go_on(self, provider, two):
        wrong = base.ProviderSettlementReport(
            "BAD", TODAY, 9000, 50, 9000, (base.SettledOperation("fake-ord-a", 9000),)
        )
        fake._settlements.append(wrong)
        settle(provider, ("fake-ord-b", 3500), fees=20, external_id="GOOD")
        assert [s.external_id for s in settlements.import_settlements()] == ["GOOD"]
        assert not ProviderSettlement.objects.filter(external_id="BAD").exists()
        entry = AuditEntry.objects.get(action=settlements.REJECTED)
        assert entry.details["external_id"] == "BAD" and entry.details["provider"] == "fake"
        assert entry.details["errors"]

    def test_p_227_whoever_has_treasury_permission_gets_one_email(
        self,
        provider,
        two,
        make_admin,  # noqa: F811
    ):
        # Decisió 095, P-227 (B): no s'apunta res i s'avisa per correu qui té T1.
        treasurer = make_admin(Role.Code.TREASURER)
        treasurer.notification_email = "tresoreria@example.org"
        treasurer.save()
        make_admin(Role.Code.SECRETARY)  # sense T1: no rep res
        fake._settlements.append(
            base.ProviderSettlementReport(
                "BAD", TODAY, 9000, 50, 9000, (base.SettledOperation("fake-ord-a", 9000),)
            )
        )
        settlements.import_settlements()
        (email,) = OutgoingEmail.objects.filter(template=settlements.REJECTED_TEMPLATE)
        assert email.to_address == "tresoreria@example.org"
        assert "BAD" in email.body_text and "no quadren" in email.body_text
        assert "Núria" not in email.body_text + email.subject  # cap dada personal
        # L'endemà es torna a demanar (P-226) i es torna a rebutjar, però no es torna a avisar.
        settlements.import_settlements()
        assert AuditEntry.objects.filter(action=settlements.REJECTED).count() == 2
        assert OutgoingEmail.objects.filter(template=settlements.REJECTED_TEMPLATE).count() == 1

    def test_the_detailed_fee_passes_through(self):
        report = base.ProviderSettlementReport(
            "LIQ-2", TODAY, 9000, 80, 8920, (base.SettledOperation("fake-ord-a", 9000, 80),)
        )
        data = settlements.to_data(report)
        assert data.lines == (treasury.SettlementLine("fake-ord-a", 9000, 80),)
        assert (data.external_id, data.settled_on, data.net_cents) == ("LIQ-2", TODAY, 8920)


class TestNothingToImport:
    def test_without_a_provider(self, settings):
        settings.PAYMENTS_PROVIDER = ""
        assert settlements.import_settlements() == []

    @pytest.mark.parametrize("error", [base.NotSupported("settlements"), base.ProviderError("x")])
    def test_a_provider_without_settlements_or_down(self, monkeypatch, error):
        def fail(self, since):
            raise error

        monkeypatch.setattr(fake.FakeProvider, "list_settlements", fail)
        assert settlements.import_settlements() == []
        assert not ProviderSettlement.objects.exists()

    def test_the_base_adapter_does_not_support_settlements(self, provider):
        with pytest.raises(base.NotSupported):
            base.PaymentProvider.list_settlements(provider, TODAY)


def test_the_daily_task_calls_the_service(monkeypatch):
    calls = []
    monkeypatch.setattr(settlements, "import_settlements", lambda: calls.append(1))
    tasks.import_settlements(0)
    assert calls == [1]
