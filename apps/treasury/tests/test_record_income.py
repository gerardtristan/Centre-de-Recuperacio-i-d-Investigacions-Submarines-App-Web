"""`record_income`: l'ingrés d'un cobrament confirmat (T-M04-05; HU-T03; CA-T03.1 a CA-T03.4;
RN-T08 a RN-T10 i RN-T13; LT1). Només dades inventades."""

from datetime import date, datetime
from pathlib import Path

import pytest
from django.conf import settings
from django.db import IntegrityError
from django.urls import URLResolver, get_resolver
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import audit, charges
from apps.core.models import AuditEntry, Charge, Department, Payment, Person
from apps.members.models import Member, MembershipType
from apps.treasury import services
from apps.treasury.models import CostCentre, Movement, TreasuryAccount
from conftest import CommittedDataTestCase, run_together

pytestmark = pytest.mark.django_db
SYSTEM = audit.system("proves-t-m04-05")
# Les 00.30 del dia 13 a Barcelona encara són del dia 12 en hora universal: la data de valor és
# la d'aquí.
PAID_AT = timezone.make_aware(datetime(2026, 11, 13, 0, 30))
M = Payment.Method


def new_transit(provider_code=None, name="Trànsit del proveïdor de proves"):
    """El del proveïdor configurat ja hi és des de `migrate` (T-M04-17): es torna l'existent."""
    return services.create_transit_account(provider_code or settings.PAYMENTS_PROVIDER, name)


def paid(
    person,
    *,
    method=M.CARD,
    amount=9000,
    received=None,
    kind="fee",
    department=None,
    cost_centre=None,
):
    """Un pagament amb el càrrec ja «pagat», com el deixen el 05b o la conciliació."""
    charge = charges.create_charge(
        person,
        kind=kind,
        amount_cents=amount,
        concept="Concepte del càrrec",
        origin="proves",
        by=SYSTEM,
        department=department,
        cost_centre=cost_centre,
    )
    # T-M05b-30: un pagament manual porta l'origen «manual», qui i el motiu (restricció).
    manual = {}
    if method == M.MANUAL:
        recorder = Account.objects.create_admin(
            Person.objects.create(first_name="Registra", origin="in_person"), "registra.prova"
        )
        manual = {"origin": "manual", "recorded_by": recorder, "reason": "Prova"}
    payment = Payment.objects.create(
        charge=charge, method=method, amount_cents=received or amount, paid_at=PAID_AT, **manual
    )
    origin = "reconciliation" if method == M.TRANSFER else "provider"
    charges.mark_paid(charge, payment, origin=origin, by=SYSTEM)
    return payment


def record(payment, origin="provider", by=SYSTEM):
    return services.record_income(payment, origin=origin, by=by)


def incomes(payment=None):
    rows = Movement.objects.filter(kind=Movement.Kind.INCOME)
    return rows.filter(payment=payment) if payment else rows


def logged(action):
    return AuditEntry.objects.filter(action=action)


def nothing_was_recorded():
    return not incomes().exists() and not logged(services.INCOME_RECORDED).exists()


@pytest.fixture
def transit():
    return new_transit()


@pytest.fixture
def person(make_person):
    return make_person("Núria", "Coll")


@pytest.fixture
def payment(person, transit):
    return paid(person)


class TestIncome:
    def test_ca_t03_1_a_paid_charge_gets_one_income_in_the_account_of_the_method(
        self, payment, transit
    ):
        movement = record(payment)
        assert list(incomes()) == [movement]
        fees = CostCentre.objects.get(name="Quotes de socis")
        assert (movement.kind, movement.direction) == ("income", "in")
        assert movement.amount_cents == payment.amount_cents == 9000
        assert movement.department == payment.charge.department == fees.department
        assert movement.cost_centre == fees
        assert movement.account == transit  # RN-T08: targeta → trànsit del proveïdor
        assert movement.payment == payment
        assert movement.value_date == date(2026, 11, 13)
        assert movement.recorded_by is None and movement.reason == ""

    def test_ca_t03_1_the_amount_is_the_one_of_the_payment(self, person, transit):
        payment = paid(person, amount=9000, received=8990)
        assert record(payment).amount_cents == 8990

    @pytest.mark.parametrize(
        ("method", "account"),
        [
            (M.CARD, "Trànsit del proveïdor «fake»"),  # el de `migrate` (T-M04-17)
            (M.BIZUM, "Trànsit del proveïdor «fake»"),
            (M.DIRECT_DEBIT, "Remeses SEPA"),
            (M.TRANSFER, "Banc principal"),
        ],
    )
    def test_ca_t03_1_rn_t08_each_method_has_its_account(self, person, transit, method, account):
        new_transit(services.SEPA_REMITTANCE, "Remeses SEPA")
        assert record(paid(person, method=method)).account.name == account

    def test_ca_t03_1_two_fees_paid_by_card_add_up_in_the_transit_account(self, person, transit):
        # Exemple numèric de M04-7: 9000 + 3500 → 12.500 cèntims al trànsit.
        for amount in (9000, 3500):
            record(paid(person, amount=amount))
        entries = transit.movements.filter(direction="in")
        assert sum(entries.values_list("amount_cents", flat=True)) == 12_500

    @pytest.mark.parametrize(
        "case", ["no-transit", "transit-off", "no-provider", "manual", "two-banks"]
    )
    def test_ca_t03_1_without_one_active_account_for_the_method_nothing_is_recorded(
        self, person, settings, case
    ):
        method = M.CARD
        if case == "no-transit":  # un proveïdor configurat sense el seu trànsit
            settings.PAYMENTS_PROVIDER = "sense_transit"
        elif case == "transit-off":
            TreasuryAccount.objects.filter(pk=new_transit().pk).update(active=False)
        elif case == "no-provider":
            new_transit()
            settings.PAYMENTS_PROVIDER = ""
        elif case == "manual":  # RN-T08: el registre manual espera la P-12
            method = M.MANUAL
        elif case == "two-banks":
            TreasuryAccount.objects.create(name="Banc segon", kind="bank")
            method = M.TRANSFER
        with pytest.raises(services.IncomeAccountUnavailable):
            record(paid(person, method=method))
        assert nothing_was_recorded()

    def test_ca_t03_1_rn_t10_the_income_takes_the_cost_centre_of_the_charge(self, person, transit):
        # Ja no hi ha la regla provisional de la P-81: el centre de cost surt del càrrec.
        courses = Department.objects.create(name="Cursos")
        open_water = CostCentre.objects.create(department=courses, name="Open Water")
        payment = paid(person, kind="enrolment", department=courses, cost_centre=open_water)
        movement = record(payment)
        assert (movement.department, movement.cost_centre) == (courses, open_water)
        movement = record(paid(person, kind="enrolment", department=courses))
        assert (movement.department, movement.cost_centre) == (courses, None)

    def test_ca_t03_1_without_payment_date_the_value_date_is_today(self, payment):
        Payment.objects.filter(pk=payment.pk).update(paid_at=None)
        assert record(payment).value_date == timezone.localdate()

    def test_ca_t03_1_the_concept_has_the_member_number_and_never_a_name(self, payment, person):
        Member.objects.create(
            person=person,
            member_number=1954,
            type=MembershipType.objects.get(code="full"),
            status=Member.Status.ACTIVE,
            joined_on=date(2019, 3, 12),
        )
        other = paid(Person.objects.create(first_name="Pau", last_name="Roca", origin="web"))
        concept = record(payment).concept
        assert concept == f"Quota · soci 1954 · càrrec {payment.charge_id}"
        assert record(other).concept == f"Quota · càrrec {other.charge_id}"  # no és soci
        assert not {"Núria", "Coll", "Concepte del càrrec"} & set(concept.split(" · "))

    def test_ca_t03_1_rn_t13_the_income_is_in_the_activity_log(self, payment, transit):
        movement = record(payment)
        entry = logged(services.INCOME_RECORDED).get()
        assert (entry.target_type, entry.target_id) == ("treasury.movement", str(movement.pk))
        assert (entry.actor_kind, entry.actor_origin) == ("system", "proves-t-m04-05")
        assert entry.details == {
            "payment": payment.pk,
            "charge": payment.charge_id,
            "amount_cents": 9000,
            "account": transit.name,
            "origin": "provider",
        }

    def test_ca_t03_1_a_reconciliation_records_who_confirmed_it(self, person, admin_account):
        payment = paid(person, method=M.TRANSFER)
        movement = record(payment, origin="reconciliation", by=admin_account)
        assert movement.recorded_by == admin_account
        assert logged(services.INCOME_RECORDED).get().actor_account == admin_account


class TestIdempotent:
    def test_ca_t03_2_a_second_call_creates_nothing_and_is_logged_as_a_repetition(self, payment):
        first = record(payment)
        second = record(payment)
        assert second == first and list(incomes()) == [first]
        assert logged(services.INCOME_RECORDED).count() == 1
        repetition = logged(services.INCOME_REPEATED).get()
        assert repetition.target_id == str(first.pk)
        assert repetition.details == {"payment": payment.pk, "origin": "provider"}

    def test_ca_t03_2_the_database_stops_the_duplicate_the_check_did_not_see(
        self, payment, monkeypatch
    ):
        # Dues notificacions alhora: la segona mira si ja hi ha ingrés abans que la primera
        # l'hagi confirmat. Aquí la primera mirada no veu res i decideix la base de dades.
        first = record(payment)
        real, looks = services._income_of, []

        def blind_once(payment):
            looks.append(payment)
            return None if len(looks) == 1 else real(payment)

        monkeypatch.setattr(services, "_income_of", blind_once)
        assert record(payment) == first
        assert len(looks) == 2 and list(incomes()) == [first]  # la transacció continua viva
        assert logged(services.INCOME_RECORDED).count() == 1
        assert logged(services.INCOME_REPEATED).count() == 1

    def test_ca_t03_2_any_other_database_error_is_not_taken_for_a_repetition(
        self, payment, monkeypatch
    ):
        def broken(*args, **kwargs):
            raise IntegrityError("una altra restricció")

        monkeypatch.setattr(services, "_create_income", broken)
        with pytest.raises(IntegrityError, match="una altra"):
            record(payment)
        assert nothing_was_recorded() and not logged(services.INCOME_REPEATED).exists()


class TestSimultaneousCalls(CommittedDataTestCase):
    def test_ca_t03_2_two_simultaneous_calls_leave_a_single_income(self):
        new_transit()
        person = Person.objects.create(first_name="Núria", last_name="Coll", origin="web")
        payment = paid(person)

        first, second = run_together([lambda: record(payment).pk] * 2)

        assert first == second
        assert [m.pk for m in incomes(payment)] == [first]
        assert logged(services.INCOME_RECORDED).count() == 1
        assert logged(services.INCOME_REPEATED).count() == 1


class TestRejected:
    @pytest.mark.parametrize("status", ["pending", "returned", "cancelled"])
    def test_ca_t03_3_a_charge_that_is_not_paid_is_rejected(self, payment, status):
        Charge.objects.filter(pk=payment.charge_id).update(status=status, cancel_reason="Prova")
        with pytest.raises(services.ChargeNotPaid):
            record(payment)
        assert nothing_was_recorded()

    def test_ca_t03_3_the_status_is_read_from_the_database_not_from_memory(self, payment):
        stale = Payment.objects.select_related("charge").get(pk=payment.pk)
        Charge.objects.filter(pk=payment.charge_id).update(status="cancelled", cancel_reason="x")
        assert stale.charge.status == "paid"  # la còpia en memòria encara diu «pagat»
        with pytest.raises(services.ChargeNotPaid):
            record(stale)
        Charge.objects.filter(pk=payment.charge_id).update(status="paid", cancel_reason="")
        stale.charge.status = "pending"
        assert record(stale)

    @pytest.mark.parametrize("origin", ["browser", "member_area", "manual", ""])
    def test_ca_t03_4_only_the_provider_or_a_reconciliation_can_record_an_income(
        self, payment, origin
    ):
        with pytest.raises(services.BrowserOriginRejected):
            record(payment, origin=origin)
        assert nothing_was_recorded()

    @pytest.mark.parametrize("who", ["nobody", "anonymous", "guest"])
    def test_ca_t03_4_rn_t13_an_income_needs_the_system_or_an_account_behind_it(
        self, payment, person, who
    ):
        # Sense això, l'ingrés s'apuntava i al registre hi quedava «anònim» o un convidat.
        by = {"nobody": None, "anonymous": audit.ANONYMOUS, "guest": audit.guest(person, 1)}[who]
        with pytest.raises(services.BrowserOriginRejected):
            record(payment, by=by)
        assert nothing_was_recorded()

    def test_ca_t03_3_a_repetition_for_a_charge_no_longer_paid_is_rejected_too(self, payment):
        # L'estat del càrrec es mira abans que l'ingrés que ja hi és: ni ingrés nou ni repetició.
        first = record(payment)
        Charge.objects.filter(pk=payment.charge_id).update(status="returned")
        with pytest.raises(services.ChargeNotPaid):
            record(payment)
        assert list(incomes()) == [first] and not logged(services.INCOME_REPEATED).exists()

    def test_ca_t03_4_no_browser_request_reaches_the_treasury(self):
        def callbacks(patterns):
            for pattern in patterns:
                if isinstance(pattern, URLResolver):
                    yield from callbacks(pattern.url_patterns)
                else:
                    yield pattern.callback

        modules = {callback.__module__ for callback in callbacks(get_resolver().url_patterns)}
        # Les úniques vistes de la 04 són les pantalles de la T-M04-15 (també les que mouen
        # diners, `entry_views`, que només apunten l'ingrés d'un pagament a mà amb M14, P-12), que
        # el bucle de sota també revisa.
        treasury = {module for module in modules if module.startswith("apps.treasury")}
        # `structure_views` (T-M04-22) només manté departaments, centres de cost i comptes.
        assert modules and treasury <= {
            "apps.treasury.views",
            "apps.treasury.entry_views",
            "apps.treasury.structure_views",
        }
        apps_dir = Path(services.__file__).parents[1]
        # Cap vista de cap altra app no crida el servei: ho fan el processament de les
        # notificacions (05b) i la conciliació (04), mai una petició.
        views = [
            *apps_dir.glob("*/views.py"),
            *apps_dir.glob("*/views/*.py"),
            *apps_dir.glob("*/*_views.py"),
        ]
        assert views
        assert not [v for v in views if "record_income" in v.read_text(encoding="utf-8")]
