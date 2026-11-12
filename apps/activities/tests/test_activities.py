"""Activitat: model i serveis de crear i editar (T-M02-03; M02-6; P-M02-B, passos 1 i 3; RN-M02-05
i RN-M02-06; la part de dades de CA-M02-01, CA-M02-02, CA-M02-03 i CA-M02-26).

Els estats són a `test_states.py`; les sessions i el programa, a `test_sessions.py`; els permisos,
a `test_permissions.py`. No hi ha cap pantalla (T-M02-06). Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.activities import catalogue, services
from apps.activities.models import Activity, EnvironmentalSubtype
from apps.core.models import AuditEntry, Department, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import (
    CLOSES,
    ENDS,
    REASON,
    STARTS,
    TODAY,
    a_course,
    a_person,
    an_entry,
    an_outing,
    at,
    common_data,
    general,
    outing_type,
)

pytestmark = pytest.mark.django_db

NEXT_MONTH = datetime.date(2027, 6, 1)
S = Activity.Status


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")


def entries_of(activity, action):
    return AuditEntry.objects.filter(
        action=action, target_type="activities.activity", target_id=str(activity.pk)
    )


def raise_price(manager, entry, valid_from):
    return catalogue.change_prices(
        entry,
        by=manager,
        price_member_cents=5000,
        price_non_member_cents=6500,
        valid_from=valid_from,
        note="Puja el preu (nota inventada).",
        today=TODAY,
    )


def cleaning():
    return EnvironmentalSubtype.objects.get(name="Neteja")


def a_project(manager):
    return catalogue.create_project(
        by=manager, name="Projecte inventat", objective="Objectiu inventat.", department=general()
    )


# --- Crear un curs (P-M02-B, pas 1) ---------------------------------------------------------------


def test_a_course_is_a_draft_that_copies_the_entry(manager):
    entry = an_entry(manager, default_places=8, open_to_non_members=True)
    course = a_course(manager, entry)
    course.refresh_from_db()
    assert course.kind == Activity.Kind.COURSE
    assert course.status == S.DRAFT
    assert course.catalogue_entry == entry
    assert course.outing_type is None
    assert course.max_places == 8
    assert (course.price_member_cents, course.price_non_member_cents) == (4500, 6000)
    assert course.open_to_non_members is True
    assert course.department == general()
    assert course.price_override_note == ""
    assert (course.published_at, course.done_at, course.duplicated_from) == (None, None, None)
    assert (course.starts_on, course.ends_on, course.registration_closes_at) == (
        STARTS,
        ENDS,
        CLOSES,
    )


def test_defaults_are_the_initial_values_of_the_plan(manager):
    # VC-21 i VC-24: 72 hores per pagar i requisits en mode «avís», mentre no es digui res més.
    course = a_course(manager)
    assert course.payment_window_hours == 72
    assert course.requirements_mode == Activity.RequirementsMode.WARN
    other = an_outing(manager, payment_window_hours=48, requirements_mode="block")
    assert (other.payment_window_hours, other.requirements_mode) == (48, "block")


def test_creating_is_recorded_without_personal_data(manager):
    course = a_course(manager)
    (entry,) = entries_of(course, services.ACTIVITY_CREATED)
    assert entry.actor_account == manager
    assert entry.details == {
        "kind": "course",
        "price_member_cents": 4500,
        "price_non_member_cents": 6000,
    }


def test_what_the_manager_writes_wins_over_the_entry(manager):
    entry = an_entry(manager, default_places=8)
    course = a_course(manager, entry, max_places=6, open_to_non_members=True)
    assert course.max_places == 6
    assert course.open_to_non_members is True


def test_an_inactive_entry_cannot_be_chosen(manager):
    entry = an_entry(manager)
    catalogue.set_active(entry, False, by=manager)
    with pytest.raises(ValidationError):
        a_course(manager, entry)
    with pytest.raises(ValidationError):
        services.create_course(by=manager, catalogue_entry=None, **common_data())
    assert not Activity.objects.exists()


# --- RN-M02-05, CA-M02-01 i CA-M02-26: el preu es copia el dia que es crea ------------------------


def test_ca_m02_26_a_new_course_copies_the_price_in_force_the_day_it_is_created(manager):
    """CA-M02-26: catàleg a 4500 i canvi a 5000 des de l'1 del mes vinent. Creada avui copia 4500;
    creada a partir d'aquella data, 5000; la que ja existia no canvia. El correu al tresorer i a la
    junta és de la T-M02-05."""
    entry = an_entry(manager)
    raise_price(manager, entry, NEXT_MONTH)
    today = services.create_course(
        by=manager, catalogue_entry=entry, today=TODAY, **common_data(title="Creat avui")
    )
    later = services.create_course(
        by=manager, catalogue_entry=entry, today=NEXT_MONTH, **common_data(title="Creat després")
    )
    assert (today.price_member_cents, today.price_non_member_cents) == (4500, 6000)
    assert (later.price_member_cents, later.price_non_member_cents) == (5000, 6500)
    today.refresh_from_db()
    assert today.price_member_cents == 4500
    # Cap dels dos difereix del catàleg del seu dia: no cal motiu.
    assert today.price_override_note == later.price_override_note == ""


def test_ca_m02_01_changing_the_catalogue_never_changes_an_existing_activity(manager):
    entry = an_entry(manager)
    course = a_course(manager, entry)
    raise_price(manager, entry, TODAY)
    course.refresh_from_db()
    assert (course.price_member_cents, course.price_non_member_cents) == (4500, 6000)
    assert not entries_of(course, services.ACTIVITY_UPDATED).exists()


# --- RN-M02-06 i CA-M02-02: preu diferent del catàleg ---------------------------------------------


def test_ca_m02_02_a_price_different_from_the_catalogue_needs_a_note(manager):
    """CA-M02-02, la part de les dades: sense nota es rebutja; amb nota es desa i el registre
    guarda el preu del catàleg i el de l'activitat. L'avís al tresorer és de la T-M02-06."""
    entry = an_entry(manager)
    for note in ("", "   "):
        with pytest.raises(ValidationError):
            a_course(manager, entry, price_member_cents=4000, price_override_note=note)
    assert not Activity.objects.exists()
    course = a_course(manager, entry, price_member_cents=4000, price_override_note=REASON)
    assert course.price_member_cents == 4000
    assert course.price_override_note == REASON
    (created,) = entries_of(course, services.ACTIVITY_CREATED)
    assert created.reason == REASON
    assert created.details["price_member_cents"] == 4000
    assert created.details["catalogue_price_member_cents"] == 4500
    assert created.details["catalogue_price_non_member_cents"] == 6000


def test_ca_m02_02_editing_a_price_away_from_the_catalogue_needs_a_note(manager):
    course = a_course(manager)
    with pytest.raises(ValidationError):
        services.update_activity(course, by=manager, today=TODAY, price_non_member_cents=7000)
    course.refresh_from_db()
    assert course.price_non_member_cents == 6000
    changed = services.update_activity(
        course, by=manager, today=TODAY, price_non_member_cents=7000, price_override_note=REASON
    )
    assert changed == ["price_non_member_cents", "price_override_note"]
    price = entries_of(course, services.ACTIVITY_UPDATED).get(field="price_non_member_cents")
    assert (price.old_value, price.new_value, price.reason) == (6000, 7000, REASON)


def test_going_back_to_the_catalogue_price_needs_no_note(manager):
    course = a_course(manager, price_member_cents=4000, price_override_note=REASON)
    assert services.update_activity(course, by=manager, today=TODAY, price_member_cents=4500) == [
        "price_member_cents"
    ]


def test_the_copied_price_needs_no_note_when_the_catalogue_changes_later(manager):
    # Concreció: el motiu es demana quan canvia el preu de l'activitat, no quan canvia el catàleg.
    entry = an_entry(manager)
    course = a_course(manager, entry)
    raise_price(manager, entry, TODAY)
    assert services.update_activity(course, by=manager, today=TODAY, title="Títol nou") == ["title"]


# --- Sortides i CA-M02-03 connectat amb el desat --------------------------------------------------


def test_an_outing_takes_the_department_of_its_type_and_its_own_prices(manager):
    outing = an_outing(manager, price_member_cents=0, price_non_member_cents=1500)
    assert outing.kind == Activity.Kind.OUTING
    assert outing.status == S.DRAFT
    assert outing.outing_type == outing_type()
    assert outing.catalogue_entry is None
    assert outing.department == outing_type().default_department
    # L-M02-06: una activitat pot ser gratuïta.
    assert (outing.price_member_cents, outing.price_non_member_cents) == (0, 1500)
    assert outing.max_places == 12


@pytest.mark.parametrize("missing", ["max_places", "price_member_cents", "price_non_member_cents"])
def test_an_outing_has_no_entry_to_copy_from(manager, missing):
    data = common_data(max_places=12, price_member_cents=4500, price_non_member_cents=6000)
    del data[missing]
    with pytest.raises(ValidationError):
        services.create_outing(by=manager, outing_type=outing_type(), **data)


def test_ca_m02_03_saving_an_outing_checks_the_subtype(manager):
    """CA-M02-03: una sortida de medi ambient sense subtipus es rebutja; una d'immersió amb
    subtipus, també."""
    environment = outing_type("Medi ambient")
    project = a_project(manager)
    with pytest.raises(ValidationError):
        an_outing(manager, outing_type=environment)
    with pytest.raises(ValidationError):
        an_outing(manager, outing_type=environment, project=project)
    with pytest.raises(ValidationError):
        an_outing(manager, subtype=cleaning())
    with pytest.raises(ValidationError):
        an_outing(manager, project=project)
    with pytest.raises(ValidationError):
        services.create_outing(by=manager, outing_type=None, **common_data())
    assert not Activity.objects.exists()
    outing = an_outing(manager, outing_type=environment, subtype=cleaning(), project=project)
    assert (outing.subtype, outing.project) == (cleaning(), project)
    # El projecte és opcional.
    assert an_outing(manager, outing_type=environment, subtype=cleaning()).project is None


def test_ca_m02_03_editing_an_outing_checks_the_subtype_too(manager):
    environment = outing_type("Medi ambient")
    dive = an_outing(manager)
    with pytest.raises(ValidationError):
        services.update_activity(dive, by=manager, subtype=cleaning())
    with pytest.raises(ValidationError):
        services.update_activity(dive, by=manager, outing_type=environment)
    for wrong in ("Neteja", cleaning().pk):  # ha de ser el subtipus, no el seu nom ni el número
        with pytest.raises(ValidationError):
            services.update_activity(dive, by=manager, outing_type=environment, subtype=wrong)
    assert services.update_activity(
        dive, by=manager, outing_type=environment, subtype=cleaning()
    ) == ["outing_type", "subtype"]
    with pytest.raises(ValidationError):
        services.update_activity(dive, by=manager, subtype=None)
    with pytest.raises(ValidationError):
        services.update_activity(dive, by=manager, outing_type=outing_type())
    dive.refresh_from_db()
    assert (dive.outing_type, dive.subtype) == (environment, cleaning())


def test_a_course_has_neither_type_nor_subtype(manager):
    with pytest.raises(ValidationError):
        a_course(manager, outing_type=outing_type())
    course = a_course(manager)
    with pytest.raises(ValidationError):
        services.update_activity(course, by=manager, subtype=cleaning())


# --- Validacions comunes --------------------------------------------------------------------------

WRONG = {
    "sense títol": {"title": "   "},
    "títol massa llarg": {"title": "x" * 141},
    "acaba abans de començar": {"ends_on": STARTS - datetime.timedelta(days=1)},
    "data amb hora": {"starts_on": at(2027, 6, 14, 9)},
    "data com a text": {"ends_on": "2027-06-15"},
    "límit després de l'inici": {"registration_closes_at": at(2027, 6, 15, 9)},
    "límit sense fus horari": {"registration_closes_at": datetime.datetime(2027, 6, 10, 20)},
    "límit sense hora": {"registration_closes_at": datetime.date(2027, 6, 10)},
    "zero places": {"max_places": 0},
    "places que no són un enter": {"max_places": True},
    "termini de zero hores": {"payment_window_hours": 0},
    "preu negatiu": {"price_member_cents": -1, "price_override_note": REASON},
    "preu amb decimals": {"price_non_member_cents": 45.5, "price_override_note": REASON},
    "mode desconegut": {"requirements_mode": "ignore"},
    "sense responsable": {"responsible": None},
    "responsable que no és una persona": {"responsible": "Anna"},
    "previsió sense https": {"forecast_url": "http://example.org/previsio"},
    "previsió que no és un enllaç": {"forecast_url": "javascript:alert(1)"},
    "estat": {"status": "open"},
    "duplicada de": {"duplicated_from": None},
    "motiu de cancel·lació": {"cancellation_reason": REASON},
    "camp desconegut": {"cost_centre": 1},
}


@pytest.mark.parametrize("fields", WRONG.values(), ids=WRONG.keys())
@pytest.mark.parametrize("make", [a_course, an_outing], ids=["curs", "sortida"])
def test_creating_rejects_wrong_values(manager, make, fields):
    with pytest.raises(ValidationError):
        make(manager, **fields)
    assert not Activity.objects.exists()


@pytest.mark.parametrize("fields", WRONG.values(), ids=WRONG.keys())
def test_editing_rejects_the_same_wrong_values(manager, fields):
    course = a_course(manager)
    before = Activity.objects.values().get(pk=course.pk)
    with pytest.raises(ValidationError):
        services.update_activity(course, by=manager, today=TODAY, **fields)
    assert Activity.objects.values().get(pk=course.pk) == before
    assert not entries_of(course, services.ACTIVITY_UPDATED).exists()


def test_the_responsible_must_be_an_active_person_and_the_department_active(manager):
    gone = a_person("Anonimitzada")
    Person.objects.filter(pk=gone.pk).update(
        status=Person.Status.ANONYMISED, anonymous_ref="anonima-de-proves-1"
    )
    gone.refresh_from_db()
    with pytest.raises(ValidationError):
        a_course(manager, responsible=gone)
    closed = Department.objects.create(name="Departament inventat", active=False)
    with pytest.raises(ValidationError):
        a_course(manager, department=closed)


def test_the_forecast_is_only_a_link(manager):
    # RN-M02-24: un enllaç https a la pàgina pública de previsió, res més.
    url = "https://example.org/previsio-maritima"
    assert an_outing(manager, forecast_url=f"  {url} ").forecast_url == url


def test_the_deadline_can_be_the_start_day(manager):
    outing = an_outing(manager, registration_closes_at=at(2027, 6, 14, 7))
    assert outing.registration_closes_at == at(2027, 6, 14, 7)


# --- Editar ---------------------------------------------------------------------------------------


def test_editing_records_the_previous_value_of_each_field(manager):
    course = a_course(manager)
    other = a_person("Altra")
    changed = services.update_activity(
        course,
        by=manager,
        title="  Títol nou inventat ",
        max_places=10,
        location="Piscina inventada",
        responsible=other,
        starts_on=STARTS,  # igual que abans: no és cap canvi
    )
    assert changed == ["location", "max_places", "responsible", "title"]
    assert (course.title, course.max_places) == ("Títol nou inventat", 10)
    course.refresh_from_db()
    assert (course.title, course.max_places, course.responsible) == (
        "Títol nou inventat",
        10,
        other,
    )
    logged = {
        e.field: (e.old_value, e.new_value)
        for e in entries_of(course, "activities.activity.updated")
    }
    assert logged["max_places"] == (8, 10)
    assert logged["title"] == ("Activitat inventada de proves", "Títol nou inventat")
    assert logged["responsible"][1] == other.pk  # l'identificador, mai el nom
    assert set(logged) == set(changed)
    assert {e.actor_account for e in entries_of(course, services.ACTIVITY_UPDATED)} == {manager}


def test_editing_without_changes_records_nothing(manager):
    course = a_course(manager)
    assert services.update_activity(course, by=manager, title=course.title, max_places=8) == []
    assert services.update_activity(course, by=manager) == []
    assert not entries_of(course, services.ACTIVITY_UPDATED).exists()


@pytest.mark.parametrize("field", ["kind", "catalogue_entry", "status", "published_at", "done_at"])
def test_class_entry_and_status_are_never_edited(manager, field):
    course = a_course(manager)
    with pytest.raises(ValidationError):
        services.update_activity(course, by=manager, **{field: None})


def test_editing_checks_the_dates_against_the_ones_it_keeps(manager):
    course = a_course(manager)
    with pytest.raises(ValidationError):
        services.update_activity(course, by=manager, starts_on=datetime.date(2027, 6, 9))
    with pytest.raises(ValidationError):
        services.update_activity(course, by=manager, ends_on=datetime.date(2027, 6, 13))
    assert services.update_activity(
        course, by=manager, starts_on=datetime.date(2027, 6, 11), ends_on=datetime.date(2027, 6, 11)
    ) == ["ends_on", "starts_on"]


@pytest.mark.parametrize("status", [S.DONE, S.CLOSED, S.CANCELLED])
def test_a_finished_or_cancelled_activity_is_not_edited(manager, status):
    course = a_course(manager)
    Activity.objects.filter(pk=course.pk).update(status=status, cancellation_reason=REASON)
    with pytest.raises(ValidationError):
        services.update_activity(course, by=manager, title="Títol nou")
    course.refresh_from_db()
    assert course.title == "Activitat inventada de proves"


@pytest.mark.parametrize("status", [S.DRAFT, S.OPEN, S.REGISTRATION_CLOSED, S.IN_PROGRESS])
def test_an_activity_is_edited_until_it_is_done(manager, status):
    course = a_course(manager)
    Activity.objects.filter(pk=course.pk).update(status=status)
    assert services.update_activity(course, by=manager, title="Títol nou") == ["title"]


# --- Restriccions també a la base de dades (M02-6) ------------------------------------------------


def row(manager, **fields):
    entry = an_entry(manager, name=f"Fitxa {Activity.objects.count()} inventada")
    return {
        "kind": "course",
        "catalogue_entry": entry,
        "title": "Fila inventada",
        "department": general(),
        "starts_on": STARTS,
        "ends_on": ENDS,
        "max_places": 8,
        "registration_closes_at": CLOSES,
        "payment_window_hours": 72,
        "price_member_cents": 4500,
        "price_non_member_cents": 6000,
        "responsible": a_person(),
        **fields,
    }


BROKEN_ROWS = {
    "curs sense fitxa": {"catalogue_entry": None},
    "sortida sense tipus": {"kind": "outing"},
    "classe desconeguda": {"kind": "conference"},
    "estat desconegut": {"status": "archived"},
    "mode desconegut": {"requirements_mode": "x"},
    "acaba abans de començar": {"ends_on": STARTS - datetime.timedelta(days=1)},
    "zero places": {"max_places": 0},
    "cancel·lada sense motiu": {"status": "cancelled"},
}


@pytest.mark.parametrize("fields", BROKEN_ROWS.values(), ids=BROKEN_ROWS.keys())
def test_activity_constraints_are_also_in_the_database(manager, fields):
    data = row(manager, **fields)
    with pytest.raises(IntegrityError), transaction.atomic():
        Activity.objects.create(**data)


def test_a_valid_row_and_a_cancelled_one_with_reason_are_accepted(manager):
    Activity.objects.create(**row(manager))
    Activity.objects.create(**row(manager, status="cancelled", cancellation_reason=REASON))
    assert Activity.objects.count() == 2


def test_entries_types_and_people_with_activities_are_not_deleted(manager):
    course = a_course(manager)
    outing = an_outing(manager)
    for obj in (course.catalogue_entry, outing.outing_type, course.responsible, course.department):
        with pytest.raises(ProtectedError):
            obj.delete()
