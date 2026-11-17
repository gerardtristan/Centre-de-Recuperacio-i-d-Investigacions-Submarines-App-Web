"""`record_refund` i `record_return`: devolucions i rebuts retornats (T-M04-07; HU-T05; P-M04-B;
RN-T11; CA-T05.1 a CA-T05.4; P-118). Només dades inventades."""

from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.models import AuditEntry, Charge, Department, Payment, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.treasury import services
from apps.treasury.models import CostCentre, Movement
from apps.treasury.tests.test_record_income import SYSTEM, new_transit, paid, record
from conftest import CommittedDataTestCase, run_together

pytestmark = pytest.mark.django_db
K = Movement.Kind
OUT = Movement.Direction.OUT
REASON = "Activitat anul·lada pel club (prova)"


@pytest.fixture
def transit():
    return new_transit()


@pytest.fixture
def person(make_person):
    return make_person("Núria", "Coll")


@pytest.fixture
def payment(person, transit):
    """Una inscripció de 12.000 cèntims pagada, amb el seu ingrés (exemple de RN-T11)."""
    department = Department.objects.create(name="Escola (prova)")
    centre = CostCentre.objects.create(department=department, name="Curs d'iniciació (prova)")
    payment = paid(
        person, kind="enrolment", amount=12000, department=department, cost_centre=centre
    )
    record(payment)
    return payment


def income(payment):
    return Movement.objects.get(payment=payment, kind=K.INCOME)


def refund(payment, amount, reason=REASON, by=SYSTEM):
    return services.record_refund(payment, amount, reason=reason, by=by)


def rows(payment, kind):
    return list(Movement.objects.filter(payment=payment, kind=kind))


class TestRefund:
    def test_ca_t05_1_a_partial_refund_is_a_new_outgoing_movement(self, payment, transit):
        original = income(payment)
        before = Movement.objects.filter(pk=original.pk).values().get()
        out = refund(payment, 4000)
        assert (out.kind, out.direction, out.amount_cents, out.account) == (
            K.REFUND,
            OUT,
            4000,
            transit,
        )
        assert (out.department, out.cost_centre) == (original.department, original.cost_centre)
        assert (out.payment, out.reason, out.value_date) == (payment, REASON, timezone.localdate())
        assert out.concept == f"Devolució · {original.concept}"
        # L'ingrés original no canvia ni queda anul·lat.
        assert Movement.objects.filter(pk=original.pk).values().get() == before
        assert not Movement.objects.get(pk=original.pk).is_reversed
        entry = AuditEntry.objects.get(action=services.REFUND_RECORDED)
        assert entry.reason == REASON
        assert entry.details == {
            "payment": payment.pk,
            "amount_cents": 4000,
            "account": transit.name,
            "cost_centre": "Escola (prova) / Curs d'iniciació (prova)",
        }

    def test_ca_t05_4_refunds_add_up_to_the_paid_amount_and_no_more(self, payment):
        # Exemple de M04-7: 4000 i 8000 s'accepten; una tercera d'1 cèntim es rebutja.
        refund(payment, 4000)
        refund(payment, 8000)
        with pytest.raises(services.RefundExceedsPaid):
            refund(payment, 1)
        assert [m.amount_cents for m in rows(payment, K.REFUND)] == [4000, 8000]

    def test_ca_t05_4_a_single_refund_above_the_paid_amount_is_rejected(self, payment):
        with pytest.raises(services.RefundExceedsPaid):
            refund(payment, 12001)
        assert refund(payment, 12000).amount_cents == 12000  # total

    def test_a_reversed_refund_no_longer_counts(self, payment, make_admin):  # noqa: F811
        first = refund(payment, 12000)
        services.reverse(first, reason="Apuntada per error (prova)", by=make_admin("treasurer"))
        assert refund(payment, 12000).amount_cents == 12000

    def test_p_119_a_repeated_refund_id_returns_the_existing_refund(self, payment):
        # Decisió 095, P-119 (B): l'identificador de la devolució va al moviment.
        key = uuid4()
        first = services.record_refund(payment, 4000, reason=REASON, by=SYSTEM, refund_id=key)
        assert first.refund_id == key
        again = services.record_refund(payment, 4000, reason=REASON, by=SYSTEM, refund_id=key)
        assert again == first and len(rows(payment, K.REFUND)) == 1
        assert AuditEntry.objects.filter(action=services.REFUND_RECORDED).count() == 1
        # Dues devolucions parcials iguals amb identificadors diferents són legítimes.
        services.record_refund(payment, 4000, reason=REASON, by=SYSTEM, refund_id=uuid4())
        assert len(rows(payment, K.REFUND)) == 2
        # El mateix identificador amb un altre import no és la mateixa devolució.
        with pytest.raises(ValidationError):
            services.record_refund(payment, 1000, reason=REASON, by=SYSTEM, refund_id=key)

    def test_ca_t05_2_the_original_fee_is_not_given_back(self, payment):
        fee = services.record_fee(payment, 180, by=SYSTEM)
        refund(payment, 12000)
        assert rows(payment, K.FEE) == [fee]  # cap moviment que la compensi
        assert not Movement.objects.get(pk=fee.pk).is_reversed

    def test_a_refund_needs_a_reason(self, payment):
        for reason in ("", "   ", None):
            with pytest.raises(ValidationError):
                refund(payment, 100, reason=reason)
        assert not rows(payment, K.REFUND)

    @pytest.mark.parametrize("amount", [0, -1, 1.5, "100", True, None])
    def test_the_amount_is_positive_cents(self, payment, amount):
        with pytest.raises(services.InvalidAmount):
            refund(payment, amount)

    def test_a_person_is_recorded_and_nobody_else_can(self, payment, admin_account):
        assert refund(payment, 100, by=admin_account).recorded_by == admin_account
        with pytest.raises(services.BrowserOriginRejected):
            refund(payment, 100, by=None)


class TestReturn:
    def test_ca_t05_3_a_returned_debit_with_its_fee(self, payment, transit):
        original = income(payment)
        returned = services.record_return(payment, 250, by=SYSTEM)
        assert (returned.kind, returned.direction, returned.amount_cents) == (
            K.RETURN,
            OUT,
            12000,
        )
        assert (returned.account, returned.department, returned.cost_centre) == (
            transit,
            original.department,
            original.cost_centre,
        )
        assert returned.value_date == timezone.localdate()
        assert returned.concept == f"Retorn · {original.concept}"
        (fee,) = rows(payment, K.FEE)
        assert (fee.amount_cents, fee.direction, fee.account, fee.linked_movement) == (
            250,
            OUT,
            transit,
            returned,
        )
        assert (fee.department, fee.cost_centre) == (original.department, original.cost_centre)
        assert AuditEntry.objects.filter(action=services.RETURN_RECORDED).count() == 1
        assert AuditEntry.objects.filter(action=services.FEE_RECORDED).count() == 1

    def test_without_a_return_fee_only_the_return(self, payment):
        services.record_return(payment, by=SYSTEM)
        assert len(rows(payment, K.RETURN)) == 1 and not rows(payment, K.FEE)

    def test_the_return_fee_does_not_block_the_collection_fee(self, payment):
        # La comissió de retorn no és «la comissió del cobrament» de P-116.
        services.record_return(payment, 250, by=SYSTEM)
        fee = services.record_fee(payment, 180, by=SYSTEM)
        assert fee.linked_movement is None
        assert sorted(m.amount_cents for m in rows(payment, K.FEE)) == [180, 250]

    def test_a_payment_is_returned_only_once(self, payment):
        services.record_return(payment, by=SYSTEM)
        with pytest.raises(services.AlreadyReturned):
            services.record_return(payment, 250, by=SYSTEM)
        assert len(rows(payment, K.RETURN)) == 1 and not rows(payment, K.FEE)

    def test_p_118_no_refund_after_a_return_and_no_return_after_a_refund(self, payment, person):
        services.record_return(payment, by=SYSTEM)
        with pytest.raises(services.RefundExceedsPaid):
            refund(payment, 1)
        other = paid(person, amount=9000)
        record(other)
        refund(other, 100)
        with pytest.raises(services.RefundExceedsPaid):
            services.record_return(other, by=SYSTEM)
        assert not rows(other, K.RETURN)

    @pytest.mark.parametrize("fee", [0, -1, 2.5, "250", True])
    def test_the_return_fee_is_positive_cents(self, payment, fee):
        with pytest.raises(services.InvalidAmount):
            services.record_return(payment, fee, by=SYSTEM)
        assert not rows(payment, K.RETURN)

    def test_the_charge_is_not_touched(self, payment):
        # El càrrec el canvia el 05b (P-M05b-F i RN-M05b-17), no la tresoreria.
        services.record_return(payment, by=SYSTEM)
        assert Charge.objects.get(pk=payment.charge_id).status == Charge.Status.PAID


class TestWithoutIncome:
    def test_nothing_is_given_back_without_a_live_income(self, person, transit, make_admin):  # noqa: F811
        bare = paid(person)
        with pytest.raises(services.IncomeNotRecorded):
            refund(bare, 100)
        with pytest.raises(services.IncomeNotRecorded):
            services.record_return(bare, by=SYSTEM)
        record(bare)
        services.reverse(
            income(bare),
            reason="Conciliació desfeta (prova)",
            by=make_admin("treasurer"),
            origin=services.RECONCILIATION,
        )
        with pytest.raises(services.IncomeNotRecorded):
            refund(bare, 100)


class TestSimultaneousCalls(CommittedDataTestCase):
    def test_two_refunds_at_once_never_add_up_above_the_paid_amount(self):
        new_transit()
        person = Person.objects.create(first_name="Núria", last_name="Coll", origin="web")
        payment = paid(person, amount=12000)
        record(payment)

        def attempt():
            try:
                return refund(Payment(pk=payment.pk), 8000).pk
            except services.RefundExceedsPaid:
                return None

        results = run_together([attempt] * 2)

        assert results.count(None) == 1
        assert [m.amount_cents for m in rows(payment, K.REFUND)] == [8000]
