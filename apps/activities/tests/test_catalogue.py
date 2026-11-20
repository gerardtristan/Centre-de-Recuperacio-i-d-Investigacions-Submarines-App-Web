"""Catàlegs, tipus, subtipus, projectes i preus amb versions (T-M02-02; M02-6; RN-M02-01 i
RN-M02-05; VC-20; CA-M02-03; primera part de CA-M02-01 i de CA-M02-26).

No hi ha cap pantalla ni cap permís encara: les pantalles són de la T-M02-05 i els permisos, de la
T-M02-33. Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.activities import catalogue
from apps.activities.models import (
    EnvironmentalProject,
    EnvironmentalSubtype,
    OutingType,
    TrainingCatalogueEntry,
    TrainingCataloguePrice,
)
from apps.core.models import AppendOnlyError, AuditEntry, Department
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db

TODAY = datetime.date(2026, 11, 11)
NEXT_MONTH = datetime.date(2026, 12, 1)
K = TrainingCatalogueEntry.Kind


@pytest.fixture
def general():
    return Department.objects.get(name=Department.GENERAL)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")


def new_entry(manager, general, **fields):
    data = {
        "kind": K.COURSE,
        "name": "Curs inventat de proves",
        "default_places": 8,
        "price_member_cents": 4500,
        "price_non_member_cents": 6000,
        "department": general,
        **fields,
    }
    return catalogue.create_entry(by=manager, today=TODAY, **data)


# --- Dades inicials (M02-6; S-M02-07 i S-M02-13) ------------------------------------------------


def test_initial_data_has_the_outing_types_one_subtype_and_an_empty_catalogue(general):
    types = {t.name: t for t in OutingType.objects.all()}
    assert set(types) == {"Immersió", "Medi ambient", "Sèniors", "Jornada oberta"}
    assert [name for name, t in types.items() if t.is_environmental] == ["Medi ambient"]
    assert all(t.default_department == general and t.active for t in types.values())
    assert list(EnvironmentalSubtype.objects.values_list("name", "active")) == [("Neteja", True)]
    # S-M02-07: el catàleg neix buit; els cursos i els preus reals els dona la junta.
    assert not TrainingCatalogueEntry.objects.exists()
    assert not EnvironmentalProject.objects.exists()


# --- RN-M02-01: dos catàlegs separats -------------------------------------------------------------


def test_rn_m02_01_courses_and_specialities_are_separate_catalogues(manager, general):
    course = new_entry(manager, general, name="Nitrox inventat")
    speciality = new_entry(manager, general, kind=K.SPECIALITY, name="Nitrox inventat")
    assert course.pk != speciality.pk
    assert list(catalogue.entries(K.COURSE)) == [course]
    assert list(catalogue.entries(K.SPECIALITY)) == [speciality]
    with pytest.raises(ValidationError):
        new_entry(manager, general, name="Nitrox inventat")  # repetit dins del mateix catàleg


def test_entry_constraints_are_also_in_the_database(general):
    base = {
        "kind": K.COURSE,
        "name": "A",
        "default_places": 8,
        "price_member_cents": 1,
        "price_non_member_cents": 1,
        "department": general,
    }
    TrainingCatalogueEntry.objects.create(**base)
    for wrong in ({"name": "A"}, {"name": "B", "default_places": 0}, {"name": "C", "kind": "x"}):
        with pytest.raises(IntegrityError), transaction.atomic():
            TrainingCatalogueEntry.objects.create(**{**base, **wrong})


@pytest.mark.parametrize(
    "wrong",
    [
        {"name": "  "},
        {"default_places": 0},
        {"price_member_cents": -1},
        {"price_non_member_cents": 12.5},
        {"price_member_cents": True},
        {"reinforcement_price_cents": -5},
        {"kind": "conference"},
    ],
)
def test_create_entry_rejects_wrong_values(manager, general, wrong):
    with pytest.raises(ValidationError):
        new_entry(manager, general, **wrong)
    assert not TrainingCatalogueEntry.objects.exists()


def test_a_free_course_is_allowed(manager, general):
    # M02-6: preus ≥ 0 (L-M02-06, activitat gratuïta).
    entry = new_entry(manager, general, price_member_cents=0, price_non_member_cents=0)
    assert catalogue.price_on(entry, TODAY).member_cents == 0


def test_creating_an_entry_is_recorded_without_personal_data(manager, general):
    entry = new_entry(manager, general)
    record = AuditEntry.objects.get(action=catalogue.ENTRY_CREATED)
    assert record.actor_account == manager and record.target_id == str(entry.pk)
    assert record.details == {
        "kind": "course",
        "price_member_cents": 4500,
        "price_non_member_cents": 6000,
    }


# --- Preus amb versions (RN-M02-05; VC-20) --------------------------------------------------------


def test_the_first_version_is_the_price_of_the_entry(manager, general):
    entry = new_entry(manager, general, reinforcement_price_cents=3000)
    version = TrainingCataloguePrice.objects.get()
    assert (version.entry, version.valid_from, version.changed_by) == (entry, TODAY, manager)
    price = catalogue.price_on(entry, TODAY)
    assert (price.member_cents, price.non_member_cents, price.reinforcement_cents) == (
        4500,
        6000,
        3000,
    )


def test_ca_m02_26_a_new_price_applies_from_its_date_and_not_before(manager, general):
    """CA-M02-26, la part del catàleg: 4500 avui i 5000 a partir de l'1 del mes vinent. Una
    activitat nova copiarà el preu vigent el dia que es creï (`price_on`)."""
    entry = new_entry(manager, general)
    catalogue.change_prices(
        entry,
        by=manager,
        price_member_cents=5000,
        price_non_member_cents=6000,
        valid_from=NEXT_MONTH,
        note="Puja el preu de soci (nota inventada).",
        today=TODAY,
    )
    assert catalogue.price_on(entry, TODAY).member_cents == 4500
    assert catalogue.price_on(entry, NEXT_MONTH - datetime.timedelta(days=1)).member_cents == 4500
    assert catalogue.price_on(entry, NEXT_MONTH).member_cents == 5000
    assert catalogue.price_on(entry, NEXT_MONTH + datetime.timedelta(days=90)).member_cents == 5000
    assert catalogue.price_on(entry, TODAY).non_member_cents == 6000


def test_ca_m02_01_a_price_change_is_recorded_with_the_previous_value(manager, general):
    entry = new_entry(manager, general)
    catalogue.change_prices(
        entry,
        by=manager,
        price_member_cents=5000,
        price_non_member_cents=6500,
        valid_from=TODAY,
        note="Preu nou (nota inventada).",
        today=TODAY,
    )
    changes = {
        e.field: (e.old_value, e.new_value, e.reason)
        for e in AuditEntry.objects.filter(action=catalogue.PRICE_CHANGED)
    }
    assert changes["price_member_cents"] == (4500, 5000, "Preu nou (nota inventada).")
    assert changes["price_non_member_cents"] == (6000, 6500, "Preu nou (nota inventada).")
    assert "reinforcement_price_cents" not in changes  # no ha canviat
    assert catalogue.price_on(entry, TODAY).member_cents == 5000


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"note": "  "}, "motiu"),
        ({"valid_from": TODAY - datetime.timedelta(days=1)}, "passada"),
        ({"price_member_cents": -1}, "cèntims"),
        ({"price_member_cents": 4500, "price_non_member_cents": 6000}, "mateix"),
    ],
)
def test_change_prices_rejects_wrong_requests(manager, general, fields, message):
    entry = new_entry(manager, general)
    request = {
        "price_member_cents": 5000,
        "price_non_member_cents": 6000,
        "valid_from": TODAY,
        "note": "Nota inventada.",
        **fields,
    }
    with pytest.raises(ValidationError) as error:
        catalogue.change_prices(entry, by=manager, today=TODAY, **request)
    assert message in " ".join(error.value.messages)
    assert TrainingCataloguePrice.objects.count() == 1


def test_a_later_correction_for_the_same_date_wins(manager, general):
    entry = new_entry(manager, general)
    for cents in (5000, 5200):
        catalogue.change_prices(
            entry,
            by=manager,
            price_member_cents=cents,
            price_non_member_cents=6000,
            valid_from=NEXT_MONTH,
            note="Nota inventada.",
            today=TODAY,
        )
    assert catalogue.price_on(entry, NEXT_MONTH).member_cents == 5200
    assert TrainingCataloguePrice.objects.count() == 3  # les versions no s'esborren


def test_price_versions_are_append_only(manager, general):
    new_entry(manager, general)
    version = TrainingCataloguePrice.objects.get()
    version.price_member_cents = 1
    with pytest.raises(AppendOnlyError):
        version.save()
    with pytest.raises(AppendOnlyError):
        version.delete()
    with pytest.raises(AppendOnlyError):
        TrainingCataloguePrice.objects.all().update(price_member_cents=1)


# --- Tipus, subtipus i projectes -----------------------------------------------------------------


def test_types_and_subtypes_are_deactivated_not_deleted(manager):
    seniors = OutingType.objects.get(name="Sèniors")
    assert catalogue.set_active(seniors, False, by=manager) is True
    seniors.refresh_from_db()
    assert seniors.active is False
    record = AuditEntry.objects.get(action=catalogue.ACTIVE_CHANGED)
    assert (record.old_value, record.new_value) == (True, False)
    assert catalogue.set_active(seniors, False, by=manager) is False  # ja ho estava
    with pytest.raises(ValidationError):
        catalogue.set_active(EnvironmentalProject(name="x"), False, by=manager)


def test_names_are_unique_in_the_database(general):
    for model, fields in (
        (OutingType, {"name": "Immersió", "default_department": general}),
        (EnvironmentalSubtype, {"name": "Neteja"}),
    ):
        with pytest.raises(IntegrityError), transaction.atomic():
            model.objects.create(**fields)


# --- CA-M02-03: subtipus i projecte només a medi ambient ------------------------------------------


def test_ca_m02_03_environmental_outings_need_a_subtype_and_others_cannot_have_one(general):
    """CA-M02-03, a nivell de regla: la connectarà el desat d'una activitat (T-M02-06)."""
    environment = OutingType.objects.get(name="Medi ambient")
    dive = OutingType.objects.get(name="Immersió")
    cleaning = EnvironmentalSubtype.objects.get(name="Neteja")
    project = EnvironmentalProject.objects.create(
        name="Projecte inventat", objective="Objectiu inventat.", department=general
    )
    catalogue.check_outing_classification(environment, cleaning)
    catalogue.check_outing_classification(environment, cleaning, project)
    catalogue.check_outing_classification(dive)
    for wrong in ((environment, None, None), (dive, cleaning, None), (dive, None, project)):
        with pytest.raises(ValidationError):
            catalogue.check_outing_classification(*wrong)


def test_inactive_types_and_subtypes_cannot_be_chosen(manager):
    environment = OutingType.objects.get(name="Medi ambient")
    cleaning = EnvironmentalSubtype.objects.get(name="Neteja")
    catalogue.set_active(cleaning, False, by=manager)
    with pytest.raises(ValidationError):
        catalogue.check_outing_classification(environment, cleaning)
    catalogue.set_active(environment, False, by=manager)
    with pytest.raises(ValidationError):
        catalogue.check_outing_classification(environment, EnvironmentalSubtype(name="x"))
    with pytest.raises(ValidationError):
        catalogue.check_outing_classification(None)


# --- CA-M02-25 (part d'aquests models) ------------------------------------------------------------


def test_ca_m02_25_no_field_stores_health_card_or_iban_data():
    from django.apps import apps

    forbidden = ("health", "salut", "medical", "metge", "iban", "card_number", "cvv")
    for model in apps.get_app_config("activities").get_models():
        for field in model._meta.get_fields():
            name = field.name.lower()
            assert not any(part in name for part in forbidden), (model.__name__, field.name)
