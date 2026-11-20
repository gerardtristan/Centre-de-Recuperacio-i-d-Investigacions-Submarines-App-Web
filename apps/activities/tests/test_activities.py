"""Serveis de crear i editar activitats (T-M02-03c; M02-6; P-M02-B, passos 1 i 3; RN-M02-05 i
RN-M02-06; RN-M02-40 i 41 de l'addenda de llocs; la part de dades de CA-M02-01, 02, 03, 26 i 43).

Portades de la branca aparcada i adaptades al lloc (`place`) i a la còpia estàndard del preu. Les
restriccions de la base de dades són a `test_activity_models.py` i els estats, a `test_states.py`.
Només dades inventades.
"""

import datetime
import itertools

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils import timezone

from apps.activities import catalogue, services
from apps.activities.models import (
    Activity,
    EnvironmentalProject,
    EnvironmentalSubtype,
    OutingType,
    TrainingCatalogueEntry,
)
from apps.core.models import AuditEntry, Department, Person, Role, Setting, SettingVersion
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.treasury.models import CostCentre

pytestmark = pytest.mark.django_db

TODAY = datetime.date(2027, 5, 3)
NEXT_MONTH = datetime.date(2027, 6, 1)
STARTS, ENDS = datetime.date(2027, 6, 14), datetime.date(2027, 6, 15)
REASON = "Motiu inventat de proves"
S = Activity.Status
_numbers = itertools.count(1)


def at(year, month, day, hour=0, minute=0):
    return timezone.make_aware(datetime.datetime(year, month, day, hour, minute))


CLOSES = at(2027, 6, 10, 20)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def general():
    return Department.objects.get(name=Department.GENERAL)


def a_person(first_name="Responsable"):
    return Person.objects.create(first_name=first_name, last_name="Prova", origin="in_person")


def an_entry(manager, **fields):
    data = {
        "kind": TrainingCatalogueEntry.Kind.COURSE,
        "name": f"Curs inventat {next(_numbers)}",
        "default_places": 8,
        "price_member_cents": 4500,
        "price_non_member_cents": 6000,
        "department": general(),
        **fields,
    }
    return catalogue.create_entry(by=manager, today=TODAY, **data)


def a_place(manager, prices=(4500, 6000)):
    place = catalogue.create_place(by=manager, name=f"Lloc inventat {next(_numbers)}")
    if prices:
        catalogue.change_place_price(
            place,
            by=manager,
            price_member_cents=prices[0],
            price_non_member_cents=prices[1],
            valid_from=TODAY,
            note="Preu inicial inventat.",
            today=TODAY,
        )
    return place


def common_data(**fields):
    data = {
        "title": "Activitat inventada de proves",
        "starts_on": STARTS,
        "ends_on": ENDS,
        "registration_closes_at": CLOSES,
        **fields,
    }
    data.setdefault("responsible", a_person())
    return data


def a_course(manager, entry=None, **fields):
    entry = entry or an_entry(manager)
    return services.create_course(
        by=manager, catalogue_entry=entry, today=TODAY, **common_data(**fields)
    )


def outing_type(name="Immersió"):
    return OutingType.objects.get(name=name)


def an_outing(manager, **fields):
    classification = {
        "outing_type": fields.pop("outing_type", None) or outing_type(),
        "subtype": fields.pop("subtype", None),
        "project": fields.pop("project", None),
    }
    if "place" not in fields:
        fields["place"] = a_place(manager)
    data = {"max_places": 12, **fields}
    return services.create_outing(by=manager, today=TODAY, **classification, **common_data(**data))


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


def a_project():
    return EnvironmentalProject.objects.create(
        name=f"Projecte inventat {next(_numbers)}", objective="Objectiu.", department=general()
    )


# --- Crear un curs (P-M02-B, pas 1) ---------------------------------------------------------------


def test_a_course_is_a_draft_that_copies_the_entry(manager):
    entry = an_entry(manager, default_places=8, open_to_non_members=True)
    course = a_course(manager, entry)
    course.refresh_from_db()
    assert (course.kind, course.status, course.catalogue_entry) == ("course", S.DRAFT, entry)
    assert (course.outing_type, course.place, course.max_places) == (None, None, 8)
    assert (course.price_member_cents, course.price_non_member_cents) == (4500, 6000)
    assert (course.standard_price_member_cents, course.standard_price_non_member_cents) == (
        4500,
        6000,
    )
    assert course.open_to_non_members is True and course.department == general()
    assert course.price_override_note == ""
    assert (course.starts_on, course.ends_on, course.registration_closes_at) == (
        STARTS,
        ENDS,
        CLOSES,
    )


def test_defaults_are_the_initial_values_of_the_plan(manager):
    # VC-21 i VC-24: 72 hores per pagar i requisits en mode «avís», mentre no es digui res més.
    course = a_course(manager)
    assert (course.payment_window_hours, course.requirements_mode) == (72, "warn")
    other = an_outing(manager, payment_window_hours=48, requirements_mode="block")
    assert (other.payment_window_hours, other.requirements_mode) == (48, "block")


def test_the_defaults_are_read_from_the_settings_not_from_the_code(manager):
    # VC-21 i VC-24 són ajustos (activities/0004): un valor desat mana sobre l'inicial.
    for key, value in (
        (services.PAYMENT_WINDOW_KEY, 96),
        (services.REQUIREMENTS_MODE_KEY, "block"),
    ):
        SettingVersion.objects.create(
            setting=Setting.objects.get(key=key), value=value, changed_by=manager, note="Prova."
        )
    course = a_course(manager)
    assert (course.payment_window_hours, course.requirements_mode) == (96, "block")


def test_creating_is_recorded_without_personal_data(manager):
    course = a_course(manager)
    (entry,) = entries_of(course, services.ACTIVITY_CREATED)
    assert entry.actor_account == manager
    assert entry.details == {
        "kind": "course",
        "price_member_cents": 4500,
        "price_non_member_cents": 6000,
    }


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
    entry = an_entry(manager)
    raise_price(manager, entry, NEXT_MONTH)
    today = a_course(manager, entry, title="Creat avui")
    later = services.create_course(
        by=manager, catalogue_entry=entry, today=NEXT_MONTH, **common_data(title="Creat després")
    )
    assert (today.price_member_cents, today.standard_price_member_cents) == (4500, 4500)
    assert (later.price_member_cents, later.standard_price_non_member_cents) == (5000, 6500)
    assert today.price_override_note == later.price_override_note == ""


def test_ca_m02_01_changing_the_catalogue_never_changes_an_existing_activity(manager):
    entry = an_entry(manager)
    course = a_course(manager, entry)
    raise_price(manager, entry, TODAY)
    course.refresh_from_db()
    assert (course.price_member_cents, course.standard_price_member_cents) == (4500, 4500)
    assert not entries_of(course, services.ACTIVITY_UPDATED).exists()


# --- RN-M02-41 i CA-M02-02: preu diferent de l'estàndard ------------------------------------------


def test_ca_m02_02_a_price_different_from_the_standard_needs_a_note(manager):
    entry = an_entry(manager)
    for note in ("", "   "):
        with pytest.raises(ValidationError):
            a_course(manager, entry, price_member_cents=4000, price_override_note=note)
    assert not Activity.objects.exists()
    course = a_course(manager, entry, price_member_cents=4000, price_override_note=REASON)
    assert (course.price_member_cents, course.price_override_note) == (4000, REASON)
    (created,) = entries_of(course, services.ACTIVITY_CREATED)
    assert created.reason == REASON
    assert created.details["price_member_cents"] == 4000
    assert created.details["standard_price_member_cents"] == 4500


def test_ca_m02_02_editing_a_price_away_from_the_standard_needs_a_note(manager):
    course = a_course(manager)
    with pytest.raises(ValidationError):
        services.update_activity(course, by=manager, price_non_member_cents=7000)
    course.refresh_from_db()
    assert course.price_non_member_cents == 6000
    changed = services.update_activity(
        course, by=manager, price_non_member_cents=7000, price_override_note=REASON
    )
    assert changed == ["price_non_member_cents", "price_override_note"]
    price = entries_of(course, services.ACTIVITY_UPDATED).get(field="price_non_member_cents")
    assert (price.old_value, price.new_value, price.reason) == (6000, 7000, REASON)


def test_going_back_to_the_standard_price_needs_no_note(manager):
    course = a_course(manager, price_member_cents=4000, price_override_note=REASON)
    assert services.update_activity(course, by=manager, price_member_cents=4500) == [
        "price_member_cents"
    ]


def test_the_comparison_is_with_the_copy_not_with_todays_catalogue(manager):
    # RN-M02-41: amb el catàleg pujat a 5000, tornar al 4500 copiat no demana motiu.
    entry = an_entry(manager)
    course = a_course(manager, entry, price_member_cents=4000, price_override_note=REASON)
    raise_price(manager, entry, TODAY)
    assert services.update_activity(course, by=manager, price_member_cents=4500) == [
        "price_member_cents"
    ]
    assert services.update_activity(course, by=manager, title="Títol nou") == ["title"]


# --- Sortides: lloc i preu estàndard (RN-M02-40, CA-M02-43) ---------------------------------------


def test_ca_m02_43_an_outing_copies_the_standard_price_of_its_place(manager):
    place = a_place(manager, (4500, 6000))
    outing = an_outing(manager, place=place)
    assert (outing.kind, outing.status, outing.place) == ("outing", S.DRAFT, place)
    assert outing.department == outing_type().default_department
    assert (outing.price_member_cents, outing.price_non_member_cents) == (4500, 6000)
    assert (outing.standard_price_member_cents, outing.standard_price_non_member_cents) == (
        4500,
        6000,
    )
    with pytest.raises(ValidationError):  # 4000 sense nota
        an_outing(manager, place=place, price_member_cents=4000)
    other = an_outing(manager, place=place, price_member_cents=4000, price_override_note=REASON)
    (created,) = entries_of(other, services.ACTIVITY_CREATED)
    assert created.details["standard_price_member_cents"] == 4500


def test_a_place_without_standard_price_needs_prices_but_no_note(manager):
    room = a_place(manager, prices=None)
    with pytest.raises(ValidationError):
        an_outing(manager, place=room)  # cap preu per copiar
    outing = an_outing(manager, place=room, price_member_cents=0, price_non_member_cents=1500)
    assert (outing.price_member_cents, outing.standard_price_member_cents) == (0, None)
    assert outing.price_override_note == ""


def test_an_outing_needs_an_active_place(manager):
    place = a_place(manager)
    catalogue.set_active(place, False, by=manager)
    for wrong in (None, place, "Illes inventades"):
        with pytest.raises(ValidationError):
            an_outing(manager, place=wrong)
    assert not Activity.objects.exists()


def test_rn_m02_40_changing_the_place_of_a_draft_copies_its_standard_price(manager):
    outing = an_outing(manager)
    dearer = a_place(manager, (5000, 7000))
    assert services.update_activity(outing, by=manager, place=dearer, today=TODAY) == [
        "place",
        "price_member_cents",
        "price_non_member_cents",
        "standard_price_member_cents",
        "standard_price_non_member_cents",
    ]
    outing.refresh_from_db()
    assert (outing.price_member_cents, outing.standard_price_non_member_cents) == (5000, 7000)


def test_rn_m02_40_changing_the_place_of_an_open_outing_touches_no_price(manager):
    outing = an_outing(manager)
    Activity.objects.filter(pk=outing.pk).update(status=S.OPEN)
    assert services.update_activity(outing, by=manager, place=a_place(manager, (5000, 7000))) == [
        "place"
    ]
    outing.refresh_from_db()
    assert (outing.price_member_cents, outing.standard_price_member_cents) == (4500, 4500)


# --- CA-M02-03 connectat amb el desat -------------------------------------------------------------


def test_ca_m02_03_saving_an_outing_checks_the_subtype(manager):
    environment = outing_type("Medi ambient")
    project = a_project()
    for wrong in (
        {"outing_type": environment},
        {"outing_type": environment, "project": project},
        {"subtype": cleaning()},
        {"project": project},
    ):
        with pytest.raises(ValidationError):
            an_outing(manager, **wrong)
    with pytest.raises(ValidationError):
        services.create_outing(by=manager, outing_type=None, **common_data())
    assert not Activity.objects.exists()
    outing = an_outing(manager, outing_type=environment, subtype=cleaning(), project=project)
    assert (outing.subtype, outing.project) == (cleaning(), project)
    assert an_outing(manager, outing_type=environment, subtype=cleaning()).project is None


def test_ca_m02_03_editing_an_outing_checks_the_subtype_too(manager):
    environment = outing_type("Medi ambient")
    dive = an_outing(manager)
    with pytest.raises(ValidationError):
        services.update_activity(dive, by=manager, subtype=cleaning())
    with pytest.raises(ValidationError):
        services.update_activity(dive, by=manager, outing_type=environment)
    for wrong in ("Neteja", cleaning().pk):
        with pytest.raises(ValidationError):
            services.update_activity(dive, by=manager, outing_type=environment, subtype=wrong)
    assert services.update_activity(
        dive, by=manager, outing_type=environment, subtype=cleaning()
    ) == ["outing_type", "subtype"]
    with pytest.raises(ValidationError):
        services.update_activity(dive, by=manager, subtype=None)


def test_a_course_has_neither_type_nor_subtype(manager):
    with pytest.raises(ValidationError):
        a_course(manager, outing_type=outing_type())
    course = a_course(manager)
    with pytest.raises(ValidationError):
        services.update_activity(course, by=manager, subtype=cleaning())


# --- Centre de cost -------------------------------------------------------------------------------


def test_the_cost_centre_must_be_active_and_of_the_same_department(manager):
    other = Department.objects.create(name="Departament inventat")
    foreign = CostCentre.objects.create(department=other, name="Centre inventat")
    own = CostCentre.objects.create(department=general(), name="Centre propi inventat")
    with pytest.raises(ValidationError):
        a_course(manager, cost_centre=foreign)
    course = a_course(manager, cost_centre=own)
    assert course.cost_centre == own
    CostCentre.objects.filter(pk=own.pk).update(active=False)
    with pytest.raises(ValidationError):
        services.update_activity(course, by=manager, department=other)
    with pytest.raises(ValidationError):
        a_course(manager, cost_centre=CostCentre.objects.get(pk=own.pk))


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
    "còpia estàndard": {"standard_price_member_cents": 1},
    "cost de material": {"material_cost_cents": 1},
    "centre de cost que no ho és": {"cost_centre": 1},
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
        services.update_activity(course, by=manager, **fields)
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
    closed = Department.objects.create(name="Departament tancat inventat", active=False)
    with pytest.raises(ValidationError):
        a_course(manager, department=closed)


def test_the_forecast_is_only_a_link(manager):
    url = "https://example.org/previsio-maritima"  # RN-M02-24
    assert an_outing(manager, forecast_url=f"  {url} ").forecast_url == url


# --- Editar ---------------------------------------------------------------------------------------


def test_editing_records_the_previous_value_of_each_field(manager):
    course = a_course(manager)
    other, pool = a_person("Altra"), a_place(manager, prices=None)
    changed = services.update_activity(
        course,
        by=manager,
        title="  Títol nou inventat ",
        max_places=10,
        place=pool,
        responsible=other,
        starts_on=STARTS,  # igual que abans: no és cap canvi
    )
    assert changed == ["max_places", "place", "responsible", "title"]
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
    assert logged["responsible"][1] == other.pk  # l'identificador, mai el nom
    assert logged["place"] == (None, pool.pk)
    assert set(logged) == set(changed)


def test_editing_without_changes_records_nothing(manager):
    course = a_course(manager)
    assert services.update_activity(course, by=manager, title=course.title, max_places=8) == []
    assert services.update_activity(course, by=manager) == []
    assert not entries_of(course, services.ACTIVITY_UPDATED).exists()


@pytest.mark.parametrize("field", ["kind", "catalogue_entry", "status", "published_at", "done_at"])
def test_class_entry_and_status_are_never_edited(manager, field):
    with pytest.raises(ValidationError):
        services.update_activity(a_course(manager), by=manager, **{field: None})


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


@pytest.mark.parametrize("status", [S.DRAFT, S.OPEN, S.REGISTRATION_CLOSED, S.IN_PROGRESS])
def test_an_activity_is_edited_until_it_is_done(manager, status):
    course = a_course(manager)
    Activity.objects.filter(pk=course.pk).update(status=status)
    assert services.update_activity(course, by=manager, title="Títol nou") == ["title"]


# --- Permís (AC7) ---------------------------------------------------------------------------------


@pytest.mark.parametrize("role", [Role.Code.INSTRUCTOR, Role.Code.SECRETARY, Role.Code.BOARD])
def test_without_ac7_creating_and_editing_are_not_found(make_admin, manager, role):  # noqa: F811
    other = make_admin(role)
    entry, course = an_entry(manager), a_course(manager)
    with pytest.raises(Http404):
        services.create_course(by=other, catalogue_entry=entry, **common_data())
    with pytest.raises(Http404):
        services.create_outing(by=other, outing_type=outing_type(), **common_data())
    with pytest.raises(Http404):
        services.update_activity(course, by=other, title="Títol nou")
    assert Activity.objects.count() == 1
