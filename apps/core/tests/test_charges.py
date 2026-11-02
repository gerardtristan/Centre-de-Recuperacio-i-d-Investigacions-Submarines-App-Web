"""Càrrec, pagament i departament (T-M01-09; spec 00, CA-15.1 a CA-15.8, CA-16.1 i CA-16.2,
RN-60 a RN-76). Només dades inventades."""

from decimal import Decimal

import pytest
from django.apps import apps as django_apps
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.http import Http404

from apps.core import audit, charges
from apps.core.models import (
    AuditEntry,
    Charge,
    Department,
    Payment,
    Role,
    UndeletableError,
)

pytestmark = pytest.mark.django_db
R = Role.Code
S = Charge.Status
SYSTEM = audit.system("provider-webhook")


@pytest.fixture
def admin(make_admin):
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def treasurer(make_admin):
    return make_admin(R.TREASURER)


@pytest.fixture
def person(make_person):
    return make_person("Núria", "Coll")


@pytest.fixture
def courses(admin):
    return charges.create_department("Cursos", by=admin)


def new_charge(person, by, kind="enrolment", amount_cents=12000, department=None, **kwargs):
    return charges.create_charge(
        person,
        kind=kind,
        amount_cents=amount_cents,
        concept=kwargs.pop("concept", "Curs Open Water"),
        origin=kwargs.pop("origin", "activities"),
        department=department,
        by=by,
    )


def pay(charge, method="card"):
    return Payment.objects.create(charge=charge, method=method, amount_cents=charge.amount_cents)


class TestDepartments:
    def test_general_exists_after_migrations(self):
        # CA-16.1, amb la precisió del 02/11/2026: «General»; els centres de cost, a la T-M04-02.
        assert Department.objects.get(name="General").active

    def test_create_needs_m7(self, treasurer):
        with pytest.raises(Http404):
            charges.create_department("Sortides", by=treasurer)

    def test_names_are_unique(self, admin, courses):
        with pytest.raises(ValidationError):
            charges.create_department("Cursos", by=admin)

    def test_a_department_with_charges_is_not_deleted(self, admin, person, courses):
        # CA-16.2
        new_charge(person, admin, department=courses)
        with pytest.raises(ProtectedError), transaction.atomic():
            courses.delete()

    def test_deactivated_cannot_take_new_charges(self, admin, person, courses):
        # CA-16.2
        charges.deactivate_department(courses, by=admin)
        courses.refresh_from_db()
        assert not courses.active
        with pytest.raises(ValidationError):
            new_charge(person, admin, department=courses)
        row = AuditEntry.objects.get(action="departments.deactivated")
        assert (row.field, row.old_value, row.new_value) == ("active", True, False)

    def test_general_cannot_be_deactivated(self, admin):
        with pytest.raises(ValidationError):
            charges.deactivate_department(Department.objects.get(name="General"), by=admin)


class TestCreatingCharges:
    def test_charge_without_department_is_refused(self, admin, person):
        # CA-15.1
        with pytest.raises(ValidationError):
            new_charge(person, admin, department=None)
        assert not Charge.objects.exists()

    @pytest.mark.parametrize("amount", [0, -100, 12.5, Decimal("12"), "1200", True, None])
    def test_amount_must_be_a_positive_integer_of_cents(self, admin, person, courses, amount):
        # CA-15.2 i RN-60
        with pytest.raises(ValidationError):
            new_charge(person, admin, amount_cents=amount, department=courses)
        assert not Charge.objects.exists()

    def test_database_also_refuses_a_zero_amount(self, person, courses):
        with pytest.raises(IntegrityError), transaction.atomic():
            Charge.objects.bulk_create(
                [
                    Charge(
                        person=person,
                        kind="enrolment",
                        concept="x",
                        amount_cents=0,
                        department=courses,
                        origin="test",
                    )
                ]
            )

    def test_a_fee_goes_to_general(self, admin, person):
        # CA-15.8
        charge = new_charge(person, admin, kind="fee", amount_cents=9000, origin="members")
        assert charge.department.name == "General"
        assert (charge.status, charge.currency) == (S.PENDING, "EUR")

    def test_a_fee_cannot_go_elsewhere(self, admin, person, courses):
        with pytest.raises(ValidationError):
            new_charge(person, admin, kind="fee", department=courses)

    def test_unknown_kind_is_refused(self, admin, person, courses):
        with pytest.raises(ValidationError):
            new_charge(person, admin, kind="donation", department=courses)

    def test_creation_is_recorded(self, admin, person, courses):
        charge = new_charge(person, admin, department=courses)
        row = AuditEntry.objects.get(action="charges.created")
        assert row.target_id == str(charge.pk)
        assert row.details == {
            "kind": "enrolment",
            "amount_cents": 12000,
            "department": "Cursos",
            "origin": "activities",
        }


class TestPayments:
    @pytest.mark.parametrize("kind", ["enrolment", "licence"])
    def test_direct_debit_only_for_fees(self, admin, person, courses, kind):
        # CA-15.3 i RN-69
        charge = new_charge(person, admin, kind=kind, department=courses)
        with pytest.raises(ValidationError):
            pay(charge, method="direct_debit")
        for method in ["card", "bizum", "transfer"]:
            pay(charge, method=method)

    def test_direct_debit_for_a_fee(self, admin, person):
        charge = new_charge(person, admin, kind="fee", amount_cents=9000)
        assert pay(charge, method="direct_debit").method == "direct_debit"

    @pytest.mark.parametrize("amount", [0, -1, 9.99])
    def test_payment_amount_in_cents(self, admin, person, courses, amount):
        # CA-15.2
        charge = new_charge(person, admin, department=courses)
        with pytest.raises(ValidationError):
            Payment.objects.create(charge=charge, method="card", amount_cents=amount)

    def test_no_field_stores_an_iban_or_card_number(self):
        # CA-15.6 i RN-70. Quan existeixi el mandat xifrat del 05a (044), serà l'única excepció
        # admesa i s'haurà d'afegir aquí amb nom.
        forbidden = {"iban", "pan", "cvv", "cvc", "card_number", "account_number"}
        offenders = []
        for model in django_apps.get_models():
            if not model.__module__.startswith("apps."):
                continue
            for field in model._meta.get_fields():
                name = field.name.lower()
                if set(name.split("_")) & forbidden or any(
                    f in name for f in forbidden if "_" in f
                ):
                    offenders.append(f"{model._meta.label}.{field.name}")
        assert offenders == []


class TestTransitions:
    @pytest.mark.parametrize("start", list(S))
    @pytest.mark.parametrize("target", list(S))
    def test_only_the_rn_67_table(self, admin, person, courses, start, target):
        # CA-15.4: es força l'estat inicial i es prova cada parella.
        charge = new_charge(person, admin, department=courses)
        Charge.objects.filter(pk=charge.pk).update(status=start, cancel_reason="prova")
        allowed = (start, target) in charges.TRANSITIONS
        before = AuditEntry.objects.filter(action="charges.status_changed").count()
        if allowed:
            charges._transition(charge, target, by=admin, reason="prova")
            assert charge.status == target
            assert AuditEntry.objects.filter(action="charges.status_changed").count() == before + 1
        else:
            with pytest.raises(ValidationError):
                charges._transition(charge, target, by=admin, reason="prova")
            charge.refresh_from_db()
            assert charge.status == start
            assert AuditEntry.objects.filter(action="charges.status_changed").count() == before

    def test_the_table_is_exactly_rn_67(self):
        assert charges.TRANSITIONS == {
            (S.PENDING, S.PAID),
            (S.PENDING, S.CANCELLED),
            (S.PAID, S.RETURNED),
            (S.PAID, S.CANCELLED),
        }

    def test_each_transition_records_the_previous_value(self, admin, person, courses):
        charge = new_charge(person, admin, department=courses)
        charges.mark_paid(charge, pay(charge), origin="provider", by=SYSTEM)
        row = AuditEntry.objects.get(action="charges.status_changed")
        assert (row.field, row.old_value, row.new_value) == ("status", "pending", "paid")
        assert (row.actor_kind, row.actor_origin) == ("system", "provider-webhook")
        assert row.details["origin"] == "provider"


class TestPaidOnlyFromTrustedOrigins:
    # CA-15.7 i RN-71: cap petició del navegador posa un càrrec a «pagat».

    def test_from_the_provider(self, admin, person, courses):
        charge = new_charge(person, admin, department=courses)
        charges.mark_paid(charge, pay(charge), origin="provider", by=SYSTEM)
        assert charge.status == S.PAID

    def test_from_a_reconciliation_by_the_treasurer(self, admin, treasurer, person, courses):
        charge = new_charge(person, admin, department=courses)
        charges.mark_paid(charge, pay(charge, "transfer"), origin="reconciliation", by=treasurer)
        assert charge.status == S.PAID

    @pytest.mark.parametrize("origin", ["browser", "member_area", "", "manual"])
    def test_any_other_origin_is_refused(self, admin, person, courses, origin):
        charge = new_charge(person, admin, department=courses)
        with pytest.raises(ValidationError):
            charges.mark_paid(charge, pay(charge), origin=origin, by=admin)
        charge.refresh_from_db()
        assert charge.status == S.PENDING

    def test_manual_says_it_waits_for_p_12(self, admin, person, courses):
        charge = new_charge(person, admin, department=courses)
        with pytest.raises(ValidationError, match="P-12"):
            charges.mark_paid(charge, pay(charge), origin="manual", by=admin)

    def test_the_payment_must_belong_to_the_charge(self, admin, person, courses):
        charge = new_charge(person, admin, department=courses)
        other = new_charge(person, admin, department=courses)
        with pytest.raises(ValidationError):
            charges.mark_paid(charge, pay(other), origin="provider", by=SYSTEM)


class TestCancelling:
    def test_needs_a_reason(self, admin, person, courses):
        # CA-15.5
        charge = new_charge(person, admin, department=courses)
        with pytest.raises(ValidationError):
            charges.cancel(charge, "   ", by=admin)
        charge.refresh_from_db()
        assert charge.status == S.PENDING

    def test_cancelling_keeps_the_reason(self, admin, person, courses):
        charge = new_charge(person, admin, department=courses)
        charges.cancel(charge, "Inscripció duplicada", by=admin)
        assert (charge.status, charge.cancel_reason) == (S.CANCELLED, "Inscripció duplicada")
        assert AuditEntry.objects.get(action="charges.status_changed").reason == (
            "Inscripció duplicada"
        )

    def test_the_database_refuses_cancelled_without_reason(self, admin, person, courses):
        charge = new_charge(person, admin, department=courses)
        with pytest.raises(IntegrityError), transaction.atomic():
            Charge.objects.filter(pk=charge.pk).update(status="cancelled")

    def test_charges_and_payments_are_never_deleted(self, admin, person, courses):
        # CA-15.5 i RN-61
        charge = new_charge(person, admin, department=courses)
        payment = pay(charge)
        for action in (
            charge.delete,
            payment.delete,
            Charge.objects.all().delete,
            Payment.objects.all().delete,
        ):
            with pytest.raises(UndeletableError):
                action()
        with pytest.raises(ProtectedError), transaction.atomic():
            person.delete()
        assert Charge.objects.count() == Payment.objects.count() == 1
