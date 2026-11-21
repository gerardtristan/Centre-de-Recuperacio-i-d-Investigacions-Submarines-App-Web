"""Prova de flux sencer de la llesca F2-4 a nivell de servei (T-M03-20, part de proves): inscripció
amb necessitats → assignació (del club i llogat) → llista de lloguer enviada → lliurament →
retorn (una peça a revisió) → cost per participant → marge real del 09 → tancament amb el material
al marge congelat. Només dades inventades; proveïdor i banc ficticis (092)."""

import pytest

from apps.activities import closing as activities_closing
from apps.activities import enrolment, states
from apps.activities.models import Enrolment, OutingType
from apps.activities.tests.helpers import BEFORE_DEADLINE, PUBLISHED, a_member, an_outing, moment
from apps.core import audit, charges, events
from apps.core.models import Event, Payment, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, costs, handover, inventory, needs, rentals
from apps.equipment.models import (
    CentreRate,
    DiveCentre,
    EquipmentItem,
    EquipmentType,
    TypicalEquipmentTemplate,
    UsageRate,
)
from apps.margins import calc, closing
from apps.margins import services as margins
from apps.treasury import services as treasury

pytestmark = pytest.mark.django_db
SYSTEM = audit.system("proves-f2-4")
DAY = moment(2027, 6, 14).date()


def kind(name):
    return EquipmentType.objects.get(name=name)


def pay(row):
    charges.record_payment(row.charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM)
    events.deliver(Event.objects.get(name=events.CHARGE_PAID, payload__charge=row.charge_id).pk)
    treasury.record_income(Payment.objects.get(charge=row.charge), origin="provider", by=SYSTEM)


def test_f2_4_from_the_enrolment_needs_to_the_material_in_the_frozen_margin(make_admin):  # noqa: F811
    manager = make_admin(Role.Code.COURSES_MANAGER)
    keeper = make_admin(Role.Code.EQUIPMENT_MANAGER)
    treasurer = make_admin(Role.Code.TREASURER)
    jacket, tank = kind("Jaquet"), kind("Ampolla")
    for equipment_type in (jacket, tank):
        TypicalEquipmentTemplate.objects.create(
            outing_type=OutingType.objects.get(name="Immersió"), equipment_type=equipment_type,
            quantity_per_participant=1,
        )  # fmt: skip
    UsageRate.objects.create(equipment_type=tank, cost_per_day_cents=175, valid_from=DAY)
    centre = DiveCentre.objects.create(name="Centre inventat")
    CentreRate.objects.create(
        centre=centre, label="Jaquet", equipment_type=jacket, cost_cents=2500,
        member_price_cents=3000, valid_from=DAY, created_by=keeper,
    )  # fmt: skip
    club_tank = inventory.create_item(
        equipment_type=tank, by=keeper, litres=12, next_review_on=moment(2027, 9, 1).date()
    )

    activity = an_outing(manager)  # 14 i 15 de juny de 2027
    states.publish(activity, by=manager, now=PUBLISHED)
    answers = {
        f"need_{jacket.pk}": "need", f"size_{jacket.pk}": "M",
        f"need_{tank.pk}": "need", f"litres_{tank.pk}": 12,
    }  # fmt: skip
    account = a_member("Sòcia")
    row = enrolment.enrol(
        activity, account.person, channel="account", actor=account,
        answers={needs.SECTION_KEY: answers}, now=BEFORE_DEADLINE,
    )  # fmt: skip
    pay(row)
    row.refresh_from_db()
    assert row.status == Enrolment.Status.CONFIRMED
    assert len(needs.needs_of(activity)) == 2

    # Assignació: l'ampolla del club (només s'ofereix la de 12 litres) i el jaquet llogat.
    assert list(assignments.available_items(activity, tank, litres=12)) == [club_tank]
    from_club = assignments.assign_club(row, club_tank, by=keeper)
    rented = assignments.assign_rented(row, jacket, centre, by=keeper)
    content = rentals.generate(activity, centre, by=keeper)
    assert content.lines == (("Jaquet", "M", 1, (rentals.reference(row),)),)
    assert activities_closing.closing_blockers(activity) == [
        "Hi ha 2 peces de material previstes o lliurades sense tancar.",
        "Hi ha 1 llista de lloguer sense enviar.",
    ]
    rentals.mark_sent(content.rental_list, by=keeper)

    for assignment in (from_club, rented):
        handover.deliver(assignment, by=keeper)
    handover.give_back(from_club, by=keeper, to_review=True, note="Revisar la valvuleria.")
    handover.give_back(rented, by=keeper)
    club_tank.refresh_from_db()
    assert club_tank.status == EquipmentItem.Status.IN_REVIEW

    cost = costs.activity_material_cost(activity)
    assert cost.per_participant == {row.pk: 2 * 175 + 2500}
    assert (cost.club_use_cents, cost.rental_cost_estimated_cents, cost.rental_margin_cents) == (
        350, 2500, 500,
    )  # fmt: skip
    assert handover.used_by(account.person)[0]["activity"] == activity

    states.mark_done(activity, by=manager, now=moment(2027, 6, 16, 12))
    snapshot = closing.close_activity(activity, by=treasurer)
    # 4500 d'inscripció − 2500 de lloguer estimat − 350 de cost d'ús del club.
    assert snapshot.margin_cents == 4500 - 2500 - 350 == 1650
    assert snapshot.breakdown["rental"] == {"source": "estimated", "cents": 2500}
    assert snapshot.breakdown["material_source"] == "real"
    assert margins.activity_margin(activity, calc.REAL).margin_cents == 1650
