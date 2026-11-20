"""Activitat, sessió i bloc del programa amb el lloc (T-M02-03a; M02-6; addenda de llocs: la part
de model de CA-M02-41 i CA-M02-47). Les restriccions són a la base de dades; els estats i els
serveis són de les T-M02-03b i següents. Només dades inventades.
"""

import datetime

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils import timezone

from apps.activities import catalogue
from apps.activities.models import (
    Activity,
    EnvironmentalSubtype,
    OutingType,
    ProgrammeBlock,
    Session,
    TrainingCatalogueEntry,
)
from apps.core.models import Department, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db

START = datetime.date(2027, 6, 14)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


@pytest.fixture
def place(manager):
    return catalogue.create_place(by=manager, name="Lloc de prova")


def outing_data(default_place, **fields):
    data = {
        "kind": Activity.Kind.OUTING,
        "title": "Sortida inventada",
        "outing_type": OutingType.objects.get(name="Immersió"),
        "department": Department.objects.get(name=Department.GENERAL),
        "starts_on": START,
        "ends_on": START,
        "place": default_place,
        "max_places": 12,
        "registration_closes_at": timezone.make_aware(datetime.datetime(2027, 6, 10, 20)),
        "payment_window_hours": 72,
        "price_member_cents": 4500,
        "price_non_member_cents": 6000,
        "responsible": Person.objects.create(first_name="Responsable", origin="in_person"),
    }
    return {**data, **fields}


def at(hour):
    return timezone.make_aware(datetime.datetime.combine(START, datetime.time(hour)))


def test_an_outing_keeps_its_place_prices_and_standard_copies(place):
    activity = Activity.objects.create(
        **outing_data(place, standard_price_member_cents=4500, standard_price_non_member_cents=6000)
    )
    activity.refresh_from_db()
    assert activity.place == place and activity.status == Activity.Status.DRAFT
    assert (activity.standard_price_member_cents, activity.material_cost_cents) == (4500, None)


@pytest.mark.parametrize(
    "wrong",
    [
        {"kind": "conference"},
        {"status": "lost"},
        {"outing_type": None},
        {"ends_on": START - datetime.timedelta(days=1)},
        {"max_places": 0},
        {"status": "cancelled"},  # sense motiu
        {"requirements_mode": "maybe"},
    ],
)
def test_activity_constraints_are_in_the_database(place, wrong):
    with pytest.raises(IntegrityError), transaction.atomic():
        Activity.objects.create(**outing_data(place, **wrong))


def test_a_course_needs_a_catalogue_entry_and_its_place_is_optional(place):
    data = outing_data(place, kind=Activity.Kind.COURSE, outing_type=None, place=None)
    with pytest.raises(IntegrityError), transaction.atomic():
        Activity.objects.create(**data)
    entry = TrainingCatalogueEntry.objects.create(
        kind="course",
        name="Curs inventat",
        default_places=8,
        price_member_cents=0,
        price_non_member_cents=0,
        department=data["department"],
    )
    assert Activity.objects.create(**{**data, "catalogue_entry": entry}).place is None


def test_ca_m02_47_an_outing_needs_a_place_except_as_a_draft(place):
    """RN-M02-44: una còpia amb un lloc desactivat queda en esborrany sense lloc; fora de
    l'esborrany, una sortida sense lloc es rebutja."""
    draft = Activity.objects.create(**outing_data(place, place=None))
    with pytest.raises(IntegrityError), transaction.atomic():
        Activity.objects.filter(pk=draft.pk).update(status=Activity.Status.OPEN)
    with pytest.raises(IntegrityError), transaction.atomic():
        Activity.objects.create(**outing_data(place, place=None, status=Activity.Status.OPEN))


def test_ca_m02_47_a_session_needs_a_place_and_a_block_shows_the_activity_one(manager, place):
    activity = Activity.objects.create(**outing_data(place))
    with pytest.raises(IntegrityError), transaction.atomic():
        Session.objects.create(activity=activity, kind="pool", starts_at=at(9), ends_at=at(11))
    pool = catalogue.create_place(by=manager, name="Piscina de prova")
    session = Session.objects.create(
        activity=activity, kind="pool", starts_at=at(9), ends_at=at(11), place=pool
    )
    assert session.place == pool
    block = ProgrammeBlock.objects.create(
        activity=activity, order=1, starts_at=datetime.time(8), label="Trobada"
    )
    assert block.shown_place == place
    block.place = pool
    assert block.shown_place == pool


@pytest.mark.parametrize(
    "wrong",
    [
        {"kind": "space"},
        {"ends_at": at(9)},  # no acaba després de començar
        {"cancelled": True},  # sense motiu
    ],
)
def test_session_constraints_are_in_the_database(place, wrong):
    activity = Activity.objects.create(**outing_data(place))
    data = {"activity": activity, "kind": "sea", "starts_at": at(9), "ends_at": at(11)}
    with pytest.raises(IntegrityError), transaction.atomic():
        Session.objects.create(place=place, **{**data, **wrong})


def test_block_order_is_unique_per_activity(place):
    activity = Activity.objects.create(**outing_data(place))
    ProgrammeBlock.objects.create(activity=activity, order=1, starts_at=datetime.time(8), label="A")
    with pytest.raises(IntegrityError), transaction.atomic():
        ProgrammeBlock.objects.create(
            activity=activity, order=1, starts_at=datetime.time(9), label="B"
        )


def test_ca_m02_41_a_used_place_cannot_be_deleted_and_deactivating_keeps_it(manager, place):
    first = Activity.objects.create(**outing_data(place))
    second = Activity.objects.create(**outing_data(place, title="Una altra sortida inventada"))
    with pytest.raises(ProtectedError):
        place.delete()
    catalogue.set_active(place, False, by=manager)
    for activity in (first, second):
        activity.refresh_from_db()
        assert activity.place == place and activity.place.active is False


def test_catalogue_rows_used_by_an_activity_cannot_be_deleted(place):
    environment = OutingType.objects.get(name="Medi ambient")
    cleaning = EnvironmentalSubtype.objects.get(name="Neteja")
    Activity.objects.create(**outing_data(place, outing_type=environment, subtype=cleaning))
    for row in (environment, cleaning):
        with pytest.raises(ProtectedError):
            row.delete()
