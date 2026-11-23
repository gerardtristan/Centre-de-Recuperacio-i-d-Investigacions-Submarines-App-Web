"""T-M03-08: assignació de material amb la restricció d'exclusió (P-M03-D; RN-M03-01, 02, 03, 06 i
08; CA-M03-02, 03, 04 i 06; MT6). Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.backends.postgresql.psycopg_any import DateRange
from django.http import Http404
from django.utils import timezone

from apps.activities.models import Enrolment, Session
from apps.activities.tests.helpers import a_place, an_outing
from apps.activities.tests.test_attendance import a_session, enrolled
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, inventory, places
from apps.equipment.models import (
    CentreRate,
    DiveCentre,
    EquipmentAssignment,
    EquipmentItem,
    EquipmentType,
    UsageRate,
)

pytestmark = pytest.mark.django_db
R = Role.Code
JUNE = datetime.date(2027, 6, 14)


def kind(name):
    return EquipmentType.objects.get(name=name)


@pytest.fixture
def keeper(make_admin):  # noqa: F811
    return make_admin(R.EQUIPMENT_MANAGER)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(R.COURSES_MANAGER)


def outing(manager, starts=JUNE, days=2):
    ends = starts + datetime.timedelta(days=days - 1)
    return an_outing(manager, starts_on=starts, ends_on=ends)


def jacket(keeper, size="M"):
    return inventory.create_item(equipment_type=kind("Jaquet"), by=keeper, size=size)


def test_ca_m03_02_a_piece_cannot_be_in_two_activities_on_touching_days(manager, keeper):
    item = jacket(keeper)
    first = enrolled(outing(manager))  # 14 i 15 de juny
    assignments.assign_club(first, item, by=keeper)
    touching = enrolled(outing(manager, JUNE + datetime.timedelta(days=1), days=1), "B")
    with pytest.raises(ValidationError):
        assignments.assign_club(touching, item, by=keeper)
    after = enrolled(outing(manager, JUNE + datetime.timedelta(days=2), days=1), "C")
    assignments.assign_club(after, item, by=keeper)
    # La garantia és la base de dades, també si el servei no ho mirés (dues peticions alhora).
    row = EquipmentAssignment.objects.filter(enrolment=first).get()
    with transaction.atomic(), pytest.raises(IntegrityError):
        EquipmentAssignment.objects.create(
            activity=touching.activity, enrolment=touching, equipment_type=item.type,
            origin="club", item=item, period=DateRange(JUNE, JUNE, "[]"), cost_cents=0,
            participant_price_cents=0, created_by=keeper,
        )  # fmt: skip
    # Una assignació cancel·lada ja no ocupa la peça.
    EquipmentAssignment.objects.filter(pk=row.pk).update(status="cancelled")
    assignments.assign_club(touching, item, by=keeper)


def test_ca_m03_03_and_06_only_available_pieces_of_the_size_are_offered(manager, keeper):
    activity = outing(manager)
    medium, large, reviewed = jacket(keeper), jacket(keeper, "L"), jacket(keeper)
    inventory.change_status(reviewed, EquipmentItem.Status.IN_REVIEW, by=keeper)
    busy = jacket(keeper)
    assignments.assign_club(enrolled(outing(manager), "Ocupa"), busy, by=keeper)
    offered = assignments.available_items(activity, kind("Jaquet"), size="M")
    assert list(offered) == [medium]
    assert large not in assignments.available_items(activity, kind("Jaquet"), size="M")
    reviewed.refresh_from_db()
    with pytest.raises(ValidationError):  # forçar la petició
        assignments.assign_club(enrolled(activity), reviewed, by=keeper)


def test_ca_m03_04_an_overdue_review_before_the_last_day_is_rejected(manager, keeper):
    activity = outing(manager)  # 14 i 15 de juny
    tank = inventory.create_item(
        equipment_type=kind("Ampolla"), by=keeper, litres=12, next_review_on=JUNE
    )
    assert tank not in assignments.available_items(activity, kind("Ampolla"))
    with pytest.raises(ValidationError, match="revisió"):
        assignments.assign_club(enrolled(activity), tank, by=keeper)


def test_rn_m03_08_club_cost_is_days_by_the_usage_rate(manager, keeper):
    UsageRate.objects.create(equipment_type=kind("Jaquet"), cost_per_day_cents=200, valid_from=JUNE)
    row = assignments.assign_club(enrolled(outing(manager)), jacket(keeper), by=keeper)
    assert (row.cost_cents, row.participant_price_cents, row.status) == (400, 0, "planned")
    entry = AuditEntry.objects.get(action=assignments.ASSIGNED)
    assert entry.details["cost_cents"] == 400


def test_rn_m03_06_a_rental_copies_the_rate_of_the_first_day(manager, keeper):
    centre = DiveCentre.objects.create(name="Centre inventat")
    rate = CentreRate.objects.create(
        centre=centre, label="Equip complet", equipment_type=kind("Jaquet"), cost_cents=2500,
        member_price_cents=3000, non_member_price_cents=3500, valid_from=JUNE, created_by=keeper,
    )  # fmt: skip
    activity = outing(manager)
    member = assignments.assign_rented(enrolled(activity), kind("Jaquet"), centre, by=keeper)
    guest = enrolled(activity, "Convidada")
    Enrolment.objects.filter(pk=guest.pk).update(price_kind="non_member")
    other = assignments.assign_rented(guest, kind("Jaquet"), centre, by=keeper)
    assert (member.rate, member.cost_cents, member.participant_price_cents) == (rate, 2500, 3000)
    assert other.participant_price_cents == 3500
    with pytest.raises(ValidationError):  # sense tarifa d'aquest tipus
        assignments.assign_rented(enrolled(activity, "X"), kind("Aletes"), centre, by=keeper)


def rented_jacket(centre, keeper):
    CentreRate.objects.create(
        centre=centre, label="Jaquet", equipment_type=kind("Jaquet"), cost_cents=1000,
        member_price_cents=1200, valid_from=JUNE, created_by=keeper,
    )  # fmt: skip


def test_ca_m03_23_a_rental_without_centre_uses_the_usual_centre_of_the_place(manager, keeper):
    centre = DiveCentre.objects.create(name="Centre A")
    rented_jacket(centre, keeper)
    activity = outing(manager)
    with pytest.raises(ValidationError):  # ni centre triat ni centre habitual
        assignments.assign_rented(enrolled(activity), kind("Jaquet"), by=keeper)
    places.set_usual_centre(activity.place, centre, by=manager)
    row = assignments.assign_rented(enrolled(activity, "B"), kind("Jaquet"), by=keeper)
    assert (row.centre, row.cost_cents) == (centre, 1000)
    # Es pot triar un altre centre actiu.
    other = DiveCentre.objects.create(name="Centre B")
    rented_jacket(other, keeper)
    row = assignments.assign_rented(enrolled(activity, "C"), kind("Jaquet"), other, by=keeper)
    assert row.centre == other
    # Desactivat, ja no es proposa.
    DiveCentre.objects.filter(pk=centre.pk).update(active=False)
    assert places.proposed_centre_for(activity) is None
    with pytest.raises(ValidationError):
        assignments.assign_rented(enrolled(activity, "D"), kind("Jaquet"), by=keeper)


def test_rn_m03_24_the_place_of_the_session_comes_first(manager):
    activity = outing(manager)
    centre_a, centre_b = (DiveCentre.objects.create(name=f"Centre {x}") for x in "AB")
    places.set_usual_centre(activity.place, centre_a, by=manager)
    session = a_session(manager, activity, JUNE)
    assert places.proposed_centre_for(activity, session) == centre_a  # la sessió no en té
    places.set_usual_centre(session.place, centre_b, by=manager)
    assert places.proposed_centre_for(activity, session) == centre_b
    DiveCentre.objects.filter(pk=centre_b.pk).update(active=False)
    assert places.proposed_centre_for(activity, session) is None


def test_own_material_costs_nothing_and_only_confirmed_enrolments(manager, keeper):
    activity = outing(manager)
    own = assignments.assign_own(enrolled(activity), kind("Aletes"), by=keeper)
    assert (own.origin, own.cost_cents, own.item) == ("own", 0, None)
    pending = enrolled(activity, "Pendent", Enrolment.Status.PENDING_PAYMENT)
    with pytest.raises(ValidationError):
        assignments.assign_own(pending, kind("Aletes"), by=keeper)


def test_mt6_by_role_and_by_object(manager, keeper, make_admin):  # noqa: F811
    activity = outing(manager)
    row = enrolled(activity)
    with pytest.raises(Http404):
        assignments.assign_own(row, kind("Aletes"), by=make_admin(R.SECRETARY))
    teacher = make_admin(R.INSTRUCTOR)
    with pytest.raises(Http404):  # no hi fa classe
        assignments.assign_own(row, kind("Aletes"), by=teacher)
    start = timezone.make_aware(datetime.datetime(2027, 6, 14, 9))
    session = Session.objects.create(
        activity=activity, kind="sea", starts_at=start, ends_at=start + datetime.timedelta(hours=2),
        place=a_place(manager, prices=None),
    )  # fmt: skip
    session.instructors.set([teacher.person])
    assignments.assign_own(row, kind("Aletes"), by=teacher)
