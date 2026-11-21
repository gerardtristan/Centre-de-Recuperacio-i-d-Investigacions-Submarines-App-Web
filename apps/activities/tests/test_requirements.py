"""Nivell mínim, especialitats, mode per defecte i càlcul dels requisits (T-M02-29; addenda de la
058; RN-M02-10 i RN-M02-27 a 30; CA-M02-31, 32 i 34). El càlcul encara no el crida cap inscripció
(T-M02-11). Portades de la branca aparcada. Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.activities import (
    catalogue,
    certifications,
    duplicate,
    public,
    requirements,
    services,
    states,
)
from apps.activities.models import (
    CertificationLevel,
    DiverCertification,
    OutingType,
    TrainingCatalogueEntry,
)
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences.models import Licence, LicenceType, ValidityRule

from .helpers import a_course, a_person, an_entry, an_outing
from .helpers import moment as at

pytestmark = pytest.mark.django_db

Source = DiverCertification.Source
WARN, BLOCK = "warn", "block"
K = TrainingCatalogueEntry.Kind


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


@pytest.fixture
def levels(manager):
    """B1 < B2 < B3 (noms inventats; la llista real la dona el responsable, S-M02-11)."""
    return [
        catalogue.create_level(by=manager, name=f"Nivell inventat B{n}", rank=n * 10)
        for n in (1, 2, 3)
    ]


@pytest.fixture
def specialities(manager):
    return [
        an_entry(manager, kind=K.SPECIALITY, name=f"Especialitat inventada {letter}")
        for letter in "AB"
    ]


def cert(person, *, level=None, speciality=None, source=Source.DECLARED, verified_by=None):
    return DiverCertification.objects.create(
        person=person,
        level=level,
        speciality=speciality,
        source=source,
        verified_by=verified_by,
        verified_at=timezone.now() if verified_by else None,
    )


def test_an_activity_without_requirements_asks_nothing(manager):
    result = requirements.check(an_outing(manager), a_person("Participant"))
    assert result.checks == () and result.met and result.allowed and not result.warnings


# --- CA-M02-31, RN-M02-27 i RN-M02-30: nivell mínim -----------------------------------------------


def test_ca_m02_31_minimum_level_verified_or_declared(manager, levels):
    b1, b2, _b3 = levels
    activity = an_outing(manager, min_level=b1, requirements_mode=BLOCK)
    verified, declared = a_person("Verificada"), a_person("Declarada")
    cert(verified, level=b2, verified_by=manager)
    cert(declared, level=b2)
    result = requirements.check(activity, verified)
    assert result.met and result.allowed and not result.warnings
    blocked = requirements.check(activity, declared)
    (check,) = blocked.blocking
    assert (check.key, check.state) == (requirements.LEVEL, requirements.NOT_MET)
    assert "sense verificar" in check.detail
    warned = requirements.check(activity, declared, mode=WARN)
    assert warned.allowed and warned.met
    (flagged,) = warned.warnings
    assert flagged.flagged and "sense verificar" in flagged.detail


def test_rn_m02_27_the_same_or_a_higher_rank_counts(manager, levels):
    b1, b2, b3 = levels
    activity = an_outing(manager, min_level=b2, requirements_mode=BLOCK)
    for level, expected in ((b1, False), (b2, True), (b3, True)):
        person = a_person(f"Nivell {level.rank}")
        cert(person, level=level, verified_by=manager)
        assert requirements.check(activity, person).allowed is expected, level.name
    nobody = requirements.check(activity, a_person("Sense titulació"))
    assert not nobody.allowed and "No té cap titulació" in nobody.blocking[0].detail


@pytest.mark.parametrize(
    ("source", "verified", "counts_in_block", "origin"),
    [
        (Source.DECLARED, True, True, "verificada"),
        (Source.IMPORTED, True, True, "verificada"),
        (Source.CLUB_COURSE, False, True, "curs del club"),
        (Source.DECLARED, False, False, "sense verificar"),
        (Source.IMPORTED, False, False, "sense verificar"),
    ],
)
def test_rn_m02_30_which_certifications_count(
    manager, levels, source, verified, counts_in_block, origin
):
    activity = an_outing(manager, min_level=levels[0])
    person = a_person("Participant")
    cert(person, level=levels[0], source=source, verified_by=manager if verified else None)
    assert requirements.check(activity, person, mode=BLOCK).allowed is counts_in_block
    warned = requirements.check(activity, person, mode=WARN)
    assert warned.allowed and warned.met and origin in warned.checks[0].detail
    assert bool(warned.warnings) is not counts_in_block


def test_the_best_origin_is_the_one_shown(manager, levels):
    person = a_person("Dues titulacions")
    cert(person, level=levels[0])
    cert(person, level=levels[1], verified_by=manager)
    assert certifications.level_held(person, levels[0]).origin == certifications.VERIFIED
    assert requirements.check(an_outing(manager, min_level=levels[0]), person).warnings == ()


# --- CA-M02-32 i RN-M02-28: especialitats ---------------------------------------------------------


def test_ca_m02_32_all_or_any_of_the_specialities(manager, specialities):
    a, b = specialities
    person, both = a_person("Només A"), a_person("A i B")
    cert(person, speciality=a, verified_by=manager)
    for entry in (a, b):
        cert(both, speciality=entry, verified_by=manager)
    wants_any = an_outing(
        manager, required_specialities=[a, b], specialities_rule="any", requirements_mode=BLOCK
    )
    wants_all = an_outing(
        manager, required_specialities=[a, b], specialities_rule="all", requirements_mode=BLOCK
    )
    assert requirements.check(wants_any, person).allowed
    assert not requirements.check(wants_all, person).allowed
    assert requirements.check(wants_all, both).allowed
    assert (
        "Alguna d'aquestes especialitats" in requirements.check(wants_any, person).checks[0].label
    )
    nothing = requirements.check(wants_any, a_person("Cap"))
    assert not nothing.allowed and "Li falten" in nothing.blocking[0].detail


def test_unverified_specialities_only_warn(manager, specialities):
    person = a_person("Declarada")
    cert(person, speciality=specialities[0])
    activity = an_outing(manager, required_specialities=specialities[:1])
    assert not requirements.check(activity, person, mode=BLOCK).allowed
    warned = requirements.check(activity, person, mode=WARN)
    assert warned.allowed and warned.warnings


# --- CA-M02-34 i RN-M02-29: mode per defecte ------------------------------------------------------


def test_ca_m02_34_an_outing_is_born_with_the_mode_of_its_type(manager):
    seniors = OutingType.objects.get(name="Sèniors")
    assert catalogue.set_outing_type_mode(seniors, BLOCK, by=manager) is True
    assert catalogue.set_outing_type_mode(seniors, BLOCK, by=manager) is False
    outing = an_outing(manager, outing_type=seniors)
    assert outing.requirements_mode == BLOCK
    assert services.update_activity(outing, by=manager, requirements_mode=WARN) == [
        "requirements_mode"
    ]
    assert an_outing(manager).requirements_mode == WARN  # sense mode propi, l'ajust general
    assert an_outing(manager, outing_type=seniors, requirements_mode=WARN).requirements_mode == WARN
    change = AuditEntry.objects.get(action=catalogue.MODE_CHANGED)
    assert (change.old_value, change.new_value, change.actor_account) == ("", BLOCK, manager)
    with pytest.raises(ValidationError):
        catalogue.set_outing_type_mode(seniors, "ignore", by=manager)


def test_a_course_copies_the_mode_of_its_entry(manager):
    entry = an_entry(manager, default_requirements_mode=BLOCK)
    assert a_course(manager, entry).requirements_mode == BLOCK
    assert a_course(manager, entry, requirements_mode=WARN).requirements_mode == WARN
    assert catalogue.update_entry(entry, by=manager, default_requirements_mode="") == [
        "default_requirements_mode"
    ]
    entry.refresh_from_db()
    assert a_course(manager, entry).requirements_mode == WARN
    with pytest.raises(ValidationError):
        an_entry(manager, name="Una altra fitxa", default_requirements_mode="ignore")


# --- Nivells i especialitats ----------------------------------------------------------------------


def test_levels_have_a_unique_name_and_order_and_are_deactivated(manager, levels):
    for name, rank in (("Nivell inventat B1", 99), ("Un altre nivell", 10), ("", 5), ("Zero", 0)):
        with pytest.raises(ValidationError):
            catalogue.create_level(by=manager, name=name, rank=rank)
    assert catalogue.set_active(levels[2], False, by=manager) is True
    assert CertificationLevel.objects.count() == 3  # no s'esborra
    assert AuditEntry.objects.filter(action=catalogue.LEVEL_CREATED).count() == 3


def test_a_deactivated_level_or_speciality_cannot_be_asked_by_a_new_activity(
    manager, levels, specialities
):
    kept = an_outing(manager, min_level=levels[0], required_specialities=specialities[:1])
    catalogue.set_active(levels[0], False, by=manager)
    catalogue.set_active(specialities[0], False, by=manager)
    with pytest.raises(ValidationError):
        an_outing(manager, min_level=levels[0])
    with pytest.raises(ValidationError):
        an_outing(manager, required_specialities=specialities[:1])
    assert services.update_activity(
        kept, by=manager, title="Títol nou", required_specialities=specialities[:1]
    ) == ["title"]
    with pytest.raises(ValidationError):
        services.update_activity(an_outing(manager), by=manager, min_level=levels[0])


def test_required_specialities_must_come_from_the_specialities_catalogue(manager, specialities):
    for wrong in ([an_entry(manager)], ["Especialitat"], [specialities[0].pk]):
        with pytest.raises(ValidationError):
            an_outing(manager, required_specialities=wrong)
    for wrong in ({"specialities_rule": "some"}, {"min_level": "B1"}):
        with pytest.raises(ValidationError):
            an_outing(manager, **wrong)


def test_changing_the_required_specialities_is_recorded(manager, specialities):
    a, b = specialities
    outing = an_outing(manager, required_specialities=[a])
    assert services.update_activity(outing, by=manager, required_specialities=[a]) == []
    assert services.update_activity(outing, by=manager, required_specialities=[a, b]) == [
        "required_specialities"
    ]
    entry = AuditEntry.objects.get(action=services.ACTIVITY_UPDATED, field="required_specialities")
    assert (entry.old_value, entry.new_value) == ([a.pk], sorted([a.pk, b.pk]))
    assert services.update_activity(outing, by=manager, required_specialities=[]) == [
        "required_specialities"
    ]
    assert not outing.required_specialities.exists()


def test_requirements_travel_with_the_copy_and_show_on_the_public_page(
    manager, levels, specialities
):
    outing = an_outing(
        manager, min_level=levels[1], required_specialities=specialities, specialities_rule="any"
    )
    copy = duplicate.duplicate(outing, datetime.date(2028, 6, 13), by=manager)
    assert (copy.min_level, copy.specialities_rule) == (levels[1], "any")
    assert set(copy.required_specialities.all()) == set(specialities)
    states.publish(outing, by=manager, now=at(2027, 6, 1, 9))
    data = public.get_activity(outing.pk, today=datetime.date(2027, 6, 1))
    assert (data.min_level, data.any_speciality) == ("Nivell inventat B2", True)
    assert set(data.specialities) == {"Especialitat inventada A", "Especialitat inventada B"}


# --- RN-M02-10: llicència vigent (amb licences.current) -------------------------------------------


@pytest.mark.parametrize(
    ("status", "starts_on", "expected", "detail"),
    [
        (Licence.Status.ACTIVE, datetime.date(2027, 1, 1), requirements.MET, ""),
        (Licence.Status.REQUESTED, datetime.date(2027, 1, 1), requirements.NOT_MET, "En tràmit."),
        (Licence.Status.ACTIVE, datetime.date(2027, 6, 15), requirements.NOT_MET, "No consta"),
    ],
    ids=["vigent", "en tràmit", "comença després de l'activitat"],
)
def test_rn_m02_10_the_licence_must_be_valid_the_day_the_activity_starts(
    manager, status, starts_on, expected, detail
):
    person = a_person("Bussejadora")
    kind = LicenceType.objects.create(
        name="Aficionat (inventat)",
        category=LicenceType.Category.AMATEUR,
        validity_rule=ValidityRule.CALENDAR_YEAR,
    )
    Licence.objects.create(
        person=person, licence_type=kind, validity_rule=kind.validity_rule, status=status,
        origin=Licence.Origin.CLUB, starts_on=starts_on, expires_on=datetime.date(2027, 12, 31),
        price_kind="member", price_cents=9000,
    )  # fmt: skip
    activity = an_outing(manager, licence_required=True, requirements_mode=BLOCK)
    (check,) = requirements.check(activity, person).checks
    assert (check.key, check.state) == (requirements.LICENCE, expected)
    assert detail in check.detail
    warned = requirements.check(activity, person, mode=WARN)
    assert warned.allowed and bool(warned.warnings) is (expected != requirements.MET)
    for private in ("2027-12-31", "Aficionat", "amateur"):
        assert private not in repr(warned)


def test_without_a_licence_the_requirement_is_not_met(manager):
    activity = an_outing(manager, licence_required=True, requirements_mode=BLOCK)
    assert not requirements.check(activity, a_person("Sense llicència")).allowed
