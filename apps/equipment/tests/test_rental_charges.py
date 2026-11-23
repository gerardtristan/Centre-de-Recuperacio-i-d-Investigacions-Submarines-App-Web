"""T-M03-11 i la part de càrrecs de la T-M03-16: el càrrec del lloguer al participant, darrere de
l'interruptor apagat (RN-M03-11 [A validar]; CA-M03-13, 14 i 19). Només dades inventades."""

import pytest

from apps.activities import cancellation
from apps.activities import closing as activities_closing
from apps.activities.models import Activity
from apps.activities.tests.test_attendance import enrolled, opened
from apps.core.models import Charge
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, closing, handover, rental_charges
from apps.equipment.models import CentreRate, DiveCentre

from .test_assignments import JUNE, keeper, kind, manager, outing  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
UNPAID = "Hi ha 1 càrrec de lloguer sense pagar."


@pytest.fixture
def centre(keeper):  # noqa: F811
    centre = DiveCentre.objects.create(name="Centre inventat")
    CentreRate.objects.create(
        centre=centre, label="Jaquet", equipment_type=kind("Jaquet"), cost_cents=2500,
        member_price_cents=3000, valid_from=JUNE, created_by=keeper,
    )  # fmt: skip
    return centre


@pytest.fixture
def switch_on(monkeypatch):
    monkeypatch.setattr(rental_charges, "enabled", lambda: True)


def rent(activity, centre, keeper, name="Alumna"):  # noqa: F811
    return assignments.assign_rented(enrolled(activity, name), kind("Jaquet"), centre, by=keeper)


def test_switched_off_by_default_no_charge(manager, keeper, centre):  # noqa: F811
    assert rental_charges.enabled() is False
    activity = outing(manager)
    row = rent(activity, centre, keeper)
    assert row.charge is None and not Charge.objects.exists()
    assert UNPAID not in activities_closing.closing_blockers(activity)


def test_ca_m03_13_a_rental_charges_the_participant_price(manager, keeper, centre, switch_on):  # noqa: F811
    activity = outing(manager)
    row = rent(activity, centre, keeper)
    charge = row.charge
    assert (charge.amount_cents, charge.kind, charge.status) == (3000, "enrolment", "pending")
    assert (charge.person, charge.department) == (row.enrolment.person, activity.department)
    # Propi o del club: cap càrrec.
    own = assignments.assign_own(enrolled(activity, "B"), kind("Aletes"), by=keeper)
    assert own.charge is None and Charge.objects.count() == 1


def test_ca_m03_19_an_unpaid_rental_charge_blocks_closing(manager, keeper, centre, switch_on):  # noqa: F811
    activity = outing(manager)
    row = handover.deliver(rent(activity, centre, keeper), by=keeper)
    handover.give_back(row, by=keeper)
    assert UNPAID in closing.pending_reasons(activity)
    Charge.objects.filter(pk=row.charge_id).update(status=Charge.Status.PAID)
    assert UNPAID not in closing.pending_reasons(activity)


def test_ca_m03_14_cancelling_voids_a_pending_charge(manager, keeper, centre, switch_on):  # noqa: F811
    activity = opened(outing(manager), Activity.Status.OPEN)
    row = rent(activity, centre, keeper)
    cancellation.cancel_enrolment(row.enrolment, by=manager, reason="No pot venir (inventat).")
    row.refresh_from_db()
    assert (row.status, row.charge.status) == ("cancelled", "cancelled")
    other = rent(activity, centre, keeper, "B")
    handover.cancel(other, by=keeper, reason="Ja no el necessita (inventat).")
    other.charge.refresh_from_db()
    assert other.charge.status == "cancelled"


def test_a_paid_rental_charge_is_not_voided(manager, keeper, centre, switch_on):  # noqa: F811
    activity = outing(manager)
    row = rent(activity, centre, keeper)
    Charge.objects.filter(pk=row.charge_id).update(status=Charge.Status.PAID)
    handover.cancel(row, by=keeper, reason="Canvi de pla (inventat).")
    row.charge.refresh_from_db()
    assert row.charge.status == "paid"  # la devolució és P-531
