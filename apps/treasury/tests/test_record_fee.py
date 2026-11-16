"""`record_fee`: la comissió coneguda d'un cobrament (T-M04-06; HU-T04; P-M04-A, pas 3; RN-T10;
CA-T04.1 a CA-T04.3; P-116). Només dades inventades."""

import pytest

from apps.core.models import AuditEntry, Department, Payment, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.treasury import services
from apps.treasury.models import CostCentre, Movement
from apps.treasury.tests.test_record_income import SYSTEM, new_transit, paid, record
from conftest import CommittedDataTestCase, run_together

pytestmark = pytest.mark.django_db
OUT = Movement.Direction.OUT


@pytest.fixture
def transit():
    return new_transit()


@pytest.fixture
def person(make_person):
    return make_person("Núria", "Coll")


def income_of(payment):
    return record(payment)


def fees(payment=None):
    rows = Movement.objects.filter(kind=Movement.Kind.FEE)
    return rows.filter(payment=payment) if payment else rows


def general(name):
    return CostCentre.objects.select_related("department").get(
        department__name=Department.GENERAL, name=name
    )


class TestDestination:
    def test_ca_t04_1_a_fee_goes_out_of_the_transit_to_member_fees(self, person, transit):
        payment = paid(person)
        income = income_of(payment)
        fee = services.record_fee(payment, 135, by=SYSTEM)
        assert (fee.account, fee.direction, fee.amount_cents, fee.kind) == (
            transit,
            OUT,
            135,
            Movement.Kind.FEE,
        )
        assert fee.cost_centre == general("Quotes de socis")
        assert fee.department == fee.cost_centre.department
        assert (fee.payment, fee.value_date, fee.recorded_by) == (payment, income.value_date, None)
        assert fee.concept == f"Comissió · {income.concept}"
        entry = AuditEntry.objects.get(action=services.FEE_RECORDED)
        assert entry.details == {
            "payment": payment.pk,
            "amount_cents": 135,
            "account": transit.name,
            "cost_centre": "General / Quotes de socis",
        }

    def test_ca_t04_2_an_enrolment_fee_goes_to_the_activity_department(self, person, transit):
        department = Department.objects.create(name="Escola (prova)")
        centre = CostCentre.objects.create(department=department, name="Curs d'iniciació (prova)")
        payment = paid(
            person, kind="enrolment", amount=12000, department=department, cost_centre=centre
        )
        income_of(payment)
        fee = services.record_fee(payment, 180, by=SYSTEM)
        assert (fee.department, fee.cost_centre) == (department, centre)
        # L'activitat s'hi arriba pel càrrec del pagament, com a l'ingrés.
        assert fee.payment.charge == payment.charge

    def test_a_charge_without_cost_centre_gives_a_fee_without_one(self, person, transit):
        department = Department.objects.create(name="Escola (prova)")
        payment = paid(person, kind="enrolment", amount=12000, department=department)
        income_of(payment)
        fee = services.record_fee(payment, 180, by=SYSTEM)
        assert (fee.department, fee.cost_centre) == (department, None)
        assert AuditEntry.objects.get(action=services.FEE_RECORDED).details["cost_centre"] is None

    def test_ca_t04_3_a_licence_fee_goes_to_general_licences(self, person, transit):
        licences = general("Llicències")  # provisional (VT-04, S-M04-07)
        payment = paid(
            person,
            kind="licence",
            amount=4500,
            department=licences.department,
            cost_centre=licences,
        )
        income_of(payment)
        assert services.record_fee(payment, 70, by=SYSTEM).cost_centre == licences

    def test_the_account_is_recorded_when_a_person_records_it(self, person, transit, admin_account):
        payment = paid(person)
        income_of(payment)
        assert services.record_fee(payment, 1, by=admin_account).recorded_by == admin_account


class TestOnlyOnce:
    def test_the_same_fee_again_returns_the_existing_one(self, person, transit):
        payment = paid(person)
        income_of(payment)
        first = services.record_fee(payment, 135, by=SYSTEM)
        assert services.record_fee(payment, 135, by=SYSTEM) == first
        assert list(fees()) == [first]
        assert AuditEntry.objects.filter(action=services.FEE_REPEATED).count() == 1

    def test_p_116_a_different_amount_is_rejected(self, person, transit):
        payment = paid(person)
        income_of(payment)
        first = services.record_fee(payment, 135, by=SYSTEM)
        with pytest.raises(services.FeeAlreadyRecorded):
            services.record_fee(payment, 140, by=SYSTEM)
        assert list(fees()) == [first]

    def test_after_reversing_the_fee_a_new_one_can_be_recorded(self, person, transit, make_admin):  # noqa: F811
        payment = paid(person)
        income_of(payment)
        first = services.record_fee(payment, 135, by=SYSTEM)
        services.reverse(first, reason="Import equivocat (prova)", by=make_admin("treasurer"))
        second = services.record_fee(payment, 140, by=SYSTEM)
        assert second != first and second.amount_cents == 140


class TestRejected:
    @pytest.mark.parametrize("amount", [0, -5, 1.5, "135", True, None, 9001])
    def test_the_amount_is_positive_cents_up_to_the_payment(self, person, transit, amount):
        payment = paid(person)
        income_of(payment)
        with pytest.raises(services.InvalidAmount):
            services.record_fee(payment, amount, by=SYSTEM)
        assert not fees().exists()

    def test_the_whole_payment_is_still_a_valid_fee(self, person, transit):
        payment = paid(person)
        income_of(payment)
        assert services.record_fee(payment, 9000, by=SYSTEM).amount_cents == 9000

    def test_without_income_there_is_no_fee(self, person, transit):
        with pytest.raises(services.IncomeNotRecorded):
            services.record_fee(paid(person), 135, by=SYSTEM)
        assert not fees().exists()

    def test_with_a_reversed_income_there_is_no_fee(self, person, transit, make_admin):  # noqa: F811
        payment = paid(person)
        services.reverse(
            income_of(payment),
            reason="Conciliació desfeta (prova)",
            by=make_admin("treasurer"),
            origin=services.RECONCILIATION,
        )
        with pytest.raises(services.IncomeNotRecorded):
            services.record_fee(payment, 135, by=SYSTEM)

    def test_nobody_else_records_a_fee(self, person, transit):
        payment = paid(person)
        income_of(payment)
        with pytest.raises(services.BrowserOriginRejected):
            services.record_fee(payment, 135, by=None)
        assert not fees().exists()


class TestSimultaneousCalls(CommittedDataTestCase):
    def test_two_simultaneous_calls_leave_a_single_fee(self):
        new_transit()
        person = Person.objects.create(first_name="Núria", last_name="Coll", origin="web")
        payment = paid(person)
        record(payment)

        first, second = run_together(
            [lambda: services.record_fee(Payment(pk=payment.pk), 135, by=SYSTEM).pk] * 2
        )

        assert first == second
        assert [m.pk for m in fees(payment)] == [first]
