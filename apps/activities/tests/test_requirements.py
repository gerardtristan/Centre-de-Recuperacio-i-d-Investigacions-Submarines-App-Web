"""Nivells, titulacions i càlcul dels requisits (T-M02-23, T-M02-29 i T-M02-32; addenda de la 058;
RN-M02-10 i RN-M02-27 a RN-M02-33; CA-M02-31, CA-M02-32 i CA-M02-34; RGPD del 02, L-M02-07).

El càlcul encara no el crida cap inscripció (T-M02-11): aquí es prova tot sol. Només dades
inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.activities import (
    catalogue,
    certifications,
    duplicate,
    privacy,
    public,
    requirements,
    services,
    sessions,
    states,
)
from apps.activities.models import (
    Activity,
    CertificationLevel,
    DiverCertification,
    OutingType,
    Session,
    TrainingCatalogueEntry,
)
from apps.core import privacy as core_privacy
from apps.core.models import AuditEntry, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.models import LicenceRecord, Member, MembershipType

from .helpers import BEFORE_DEADLINE, STARTS, a_course, a_person, an_entry, an_outing, at

pytestmark = pytest.mark.django_db

Source = DiverCertification.Source
WARN, BLOCK = "warn", "block"
K = TrainingCatalogueEntry.Kind


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")


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


def cert(person, *, level=None, speciality=None, source=Source.DECLARED, verified_by=None, **more):
    return DiverCertification.objects.create(
        person=person,
        level=level,
        speciality=speciality,
        source=source,
        verified_by=verified_by,
        verified_at=timezone.now() if verified_by else None,
        **more,
    )


def by_key(result):
    return {check.key: check for check in result.checks}


# --- Sense requisits ------------------------------------------------------------------------------


def test_an_activity_without_requirements_asks_nothing(manager):
    result = requirements.check(an_outing(manager), a_person("Participant"))
    assert result.checks == ()
    assert result.met and result.allowed and not result.warnings


# --- CA-M02-31, RN-M02-27 i RN-M02-30: nivell mínim -----------------------------------------------


def test_ca_m02_31_minimum_level_verified_or_declared(manager, levels):
    """CA-M02-31: activitat amb nivell mínim B1. Amb una titulació B2 verificada, s'accepta en
    mode `block`. Amb una B2 declarada sense verificar, es rebutja en `block` i s'accepta amb avís
    en `warn`."""
    b1, b2, _b3 = levels
    activity = an_outing(manager, min_level=b1, requirements_mode=BLOCK)
    verified, declared = a_person("Verificada"), a_person("Declarada")
    cert(verified, level=b2, verified_by=manager)
    cert(declared, level=b2)

    result = requirements.check(activity, verified)
    assert result.met and result.allowed and not result.warnings

    blocked = requirements.check(activity, declared)
    assert not blocked.allowed
    (check,) = blocked.blocking
    assert (check.key, check.state) == (requirements.LEVEL, requirements.NOT_MET)
    assert "sense verificar" in check.detail

    warned = requirements.check(activity, declared, mode=WARN)
    assert warned.allowed and warned.met
    (flagged,) = warned.warnings  # s'accepta, i el responsable ho veu marcat
    assert flagged.flagged and "sense verificar" in flagged.detail


def test_rn_m02_27_the_same_or_a_higher_rank_counts(manager, levels):
    b1, b2, b3 = levels
    activity = an_outing(manager, min_level=b2, requirements_mode=BLOCK)
    for level, expected in ((b1, False), (b2, True), (b3, True)):
        person = a_person(f"Nivell {level.rank}")
        cert(person, level=level, verified_by=manager)
        assert requirements.check(activity, person).allowed is expected, level.name
    nobody = requirements.check(activity, a_person("Sense titulació"))
    assert not nobody.allowed
    assert "No té cap titulació" in nobody.blocking[0].detail


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
    """RN-M02-30: en `block` només compten les verificades i les d'un curs del club. En `warn`
    compten totes i el responsable veu de quin origen és."""
    activity = an_outing(manager, min_level=levels[0])
    person = a_person("Participant")
    cert(person, level=levels[0], source=source, verified_by=manager if verified else None)
    assert requirements.check(activity, person, mode=BLOCK).allowed is counts_in_block
    warned = requirements.check(activity, person, mode=WARN)
    assert warned.allowed and warned.met
    assert origin in warned.checks[0].detail
    assert bool(warned.warnings) is not counts_in_block


def test_the_best_origin_is_the_one_shown(manager, levels):
    person = a_person("Dues titulacions")
    cert(person, level=levels[0])
    cert(person, level=levels[1], verified_by=manager)
    held = certifications.level_held(person, levels[0])
    assert held.origin == certifications.VERIFIED
    assert requirements.check(an_outing(manager, min_level=levels[0]), person).warnings == ()


# --- CA-M02-32 i RN-M02-28: especialitats ---------------------------------------------------------


def test_ca_m02_32_all_or_any_of_the_specialities(manager, specialities):
    """CA-M02-32: es demanen A i B. Amb `any`, qui només té A compleix; amb `all`, no."""
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
    a, _b = specialities
    person = a_person("Declarada")
    cert(person, speciality=a)
    activity = an_outing(manager, required_specialities=[a])
    assert not requirements.check(activity, person, mode=BLOCK).allowed
    warned = requirements.check(activity, person, mode=WARN)
    assert warned.allowed and warned.warnings


# --- RN-M02-10: llicència vigent ------------------------------------------------------------------


def a_member_with_licence(first, *, issued, expires, declared=False):
    person = a_person(first)
    member = Member.objects.create(
        person=person,
        member_number=9000 + Member.objects.count(),
        type=MembershipType.objects.get(code="supporter"),
        status=Member.Status.ACTIVE,
        joined_on=datetime.date(2019, 3, 12),
    )
    LicenceRecord.objects.create(
        member=member,
        licence_type="Anual inventada",
        issued_on=issued,
        expires_on=expires,
        expiry_declared=declared,
        source=LicenceRecord.Source.MANUAL if expires else LicenceRecord.Source.CLUBER,
    )
    return person


LICENCES = {
    "vigent": (datetime.date(2027, 1, 15), datetime.date(2027, 12, 31), False, True, ""),
    "caduca el mateix dia": (datetime.date(2027, 1, 15), STARTS, False, True, ""),
    "caducada": (datetime.date(2026, 1, 15), datetime.date(2026, 12, 31), False, False, "vigent"),
    "encara no vigent": (
        datetime.date(2027, 7, 1),
        datetime.date(2027, 12, 31),
        False,
        False,
        "vigent",
    ),
    "caducitat desconeguda": (datetime.date(2027, 1, 15), None, False, False, "pendent"),
    "només declarada pel soci": (
        datetime.date(2027, 1, 15),
        datetime.date(2027, 12, 31),
        True,
        False,
        "pendent",
    ),
}


@pytest.mark.parametrize(
    ("issued", "expires", "declared", "met", "detail"), LICENCES.values(), ids=LICENCES.keys()
)
def test_rn_m02_10_the_licence_must_be_valid_the_day_the_activity_starts(
    manager, issued, expires, declared, met, detail
):
    person = a_member_with_licence("Llicenciada", issued=issued, expires=expires, declared=declared)
    activity = an_outing(manager, licence_required=True, requirements_mode=BLOCK)
    result = requirements.check(activity, person)
    assert result.allowed is met
    check = by_key(result)[requirements.LICENCE]
    assert detail in check.detail
    # Ni el tipus, ni el número, ni cap data de la llicència surten del càlcul.
    assert "Anual inventada" not in str(result)
    for date in (issued, expires):
        if date:
            assert str(date) not in str(result) and f"{date:%d/%m/%Y}" not in str(result)


def test_someone_without_a_licence_record_does_not_meet_it(manager):
    activity = an_outing(manager, licence_required=True, requirements_mode=BLOCK)
    result = requirements.check(activity, a_person("No sòcia"))
    assert not result.allowed
    assert "No consta cap llicència" in result.blocking[0].detail
    assert requirements.check(activity, a_person("No sòcia 2"), mode=WARN).allowed


# --- RN-M02-33: edat mínima (major, menor i sense data) -------------------------------------------

AGES = {
    "major": (datetime.date(1990, 2, 14), requirements.MET),
    "fa els anys el dia d'inici": (datetime.date(2011, 6, 14), requirements.MET),
    "menor per un dia": (datetime.date(2011, 6, 15), requirements.NOT_MET),
    "menor": (datetime.date(2015, 1, 1), requirements.NOT_MET),
    "sense data": (None, requirements.UNKNOWN),
    "data posterior a l'activitat": (datetime.date(2030, 1, 1), requirements.UNKNOWN),
}


@pytest.mark.parametrize(("birth", "state"), AGES.values(), ids=AGES.keys())
def test_rn_m02_33_minimum_age_on_the_start_day(manager, birth, state):
    """Edat mínima de 16 anys el dia que comença l'activitat (14/06/2027). Sense data de
    naixement, «edat desconeguda»: el responsable ho veu marcat i no bloqueja."""
    person = a_person("Participant")
    Person.objects.filter(pk=person.pk).update(birth_date=birth)
    person.refresh_from_db()
    activity = an_outing(manager, min_age=16, requirements_mode=BLOCK)
    result = requirements.check(activity, person)
    check = by_key(result)[requirements.AGE]
    assert check.state == state
    assert result.allowed is (state != requirements.NOT_MET)
    assert bool(result.warnings) is (state != requirements.MET)
    if state == requirements.UNKNOWN:
        assert check.detail == "Edat desconeguda." and check.flagged
    # RN-M01-48: ni la data de naixement ni l'edat surten del càlcul.
    if birth:
        assert str(birth) not in str(result) and f"{birth:%d/%m/%Y}" not in str(result)
        assert str(birth.year) not in str(result)


def test_several_requirements_are_checked_together(manager, levels, specialities):
    activity = an_outing(
        manager,
        min_level=levels[0],
        required_specialities=specialities[:1],
        licence_required=True,
        min_age=18,
        requirements_mode=BLOCK,
    )
    result = requirements.check(activity, a_person("Sense res"))
    assert [c.key for c in result.checks] == ["level", "specialities", "licence", "age"]
    assert [c.key for c in result.blocking] == ["level", "specialities", "licence"]
    assert not result.met and not result.allowed
    assert len(requirements.check(activity, a_person("Sense res 2"), mode=WARN).warnings) == 4


# --- CA-M02-34 i RN-M02-29: mode per defecte per tipus i per fitxa --------------------------------


def test_ca_m02_34_an_outing_is_born_with_the_mode_of_its_type(manager):
    """CA-M02-34: tipus de sortida amb mode per defecte `block`: la sortida neix en `block` i el
    responsable la pot canviar a `warn`."""
    seniors = OutingType.objects.get(name="Sèniors")
    assert catalogue.set_outing_type_mode(seniors, BLOCK, by=manager) is True
    assert catalogue.set_outing_type_mode(seniors, BLOCK, by=manager) is False
    outing = an_outing(manager, outing_type=seniors)
    assert outing.requirements_mode == BLOCK
    assert services.update_activity(outing, by=manager, requirements_mode=WARN) == [
        "requirements_mode"
    ]
    # Sense mode propi, val l'ajust general (avís); i el que escriu el responsable guanya.
    assert an_outing(manager).requirements_mode == WARN
    assert an_outing(manager, outing_type=seniors, requirements_mode=WARN).requirements_mode == WARN
    change = AuditEntry.objects.get(action=catalogue.MODE_CHANGED)
    assert (change.old_value, change.new_value, change.actor_account) == ("", BLOCK, manager)
    with pytest.raises(ValidationError):
        catalogue.set_outing_type_mode(seniors, "ignore", by=manager)


def test_a_course_copies_mode_and_minimum_age_from_its_entry(manager):
    entry = an_entry(manager, default_requirements_mode=BLOCK, min_age=14)
    course = a_course(manager, entry)
    assert (course.requirements_mode, course.min_age) == (BLOCK, 14)
    older = a_course(manager, entry, min_age=18, requirements_mode=WARN)
    assert (older.requirements_mode, older.min_age) == (WARN, 18)
    assert catalogue.update_entry(
        entry, by=manager, min_age=None, default_requirements_mode=""
    ) == [
        "default_requirements_mode",
        "min_age",
    ]
    entry.refresh_from_db()
    assert a_course(manager, entry).min_age is None


@pytest.mark.parametrize("wrong", [{"min_age": 0}, {"min_age": 100}, {"min_age": True}])
def test_wrong_minimum_ages_are_rejected_everywhere(manager, wrong):
    with pytest.raises(ValidationError):
        an_entry(manager, **wrong)
    with pytest.raises(ValidationError):
        an_outing(manager, **wrong)
    with pytest.raises(ValidationError):
        an_entry(manager, name="Una altra fitxa", default_requirements_mode="ignore")


# --- Nivells --------------------------------------------------------------------------------------


def test_levels_have_a_unique_name_and_order_and_are_deactivated(manager, levels):
    assert [level.rank for level in catalogue.levels()] == [10, 20, 30]
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
    # La que ja ho demanava ho conserva i es pot continuar editant.
    assert services.update_activity(
        kept, by=manager, title="Títol nou", required_specialities=specialities[:1]
    ) == ["title"]
    other = an_outing(manager)
    with pytest.raises(ValidationError):
        services.update_activity(other, by=manager, min_level=levels[0])


def test_required_specialities_must_come_from_the_specialities_catalogue(manager, specialities):
    course_entry = an_entry(manager)
    for wrong in ([course_entry], ["Especialitat"], [specialities[0].pk]):
        with pytest.raises(ValidationError):
            an_outing(manager, required_specialities=wrong)
    with pytest.raises(ValidationError):
        an_outing(manager, specialities_rule="some")
    with pytest.raises(ValidationError):
        an_outing(manager, min_level="B1")


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
        manager,
        min_level=levels[1],
        required_specialities=specialities,
        specialities_rule="any",
        min_age=16,
    )
    copy = duplicate.duplicate(outing, datetime.date(2028, 6, 13), by=manager)
    assert (copy.min_level, copy.specialities_rule, copy.min_age) == (levels[1], "any", 16)
    assert set(copy.required_specialities.all()) == set(specialities)
    states.publish(outing, by=manager, now=BEFORE_DEADLINE)
    data = public.get_activity(outing.pk, today=datetime.date(2027, 6, 1))
    assert (data.min_level, data.any_speciality, data.min_age) == ("Nivell inventat B2", True, 16)
    assert set(data.specialities) == {"Especialitat inventada A", "Especialitat inventada B"}


# --- Titulacions: model ---------------------------------------------------------------------------


def test_a_certification_is_a_level_or_a_speciality(manager, levels):
    person = a_person("Titulada")
    for broken in (
        {"source": Source.DECLARED},  # ni nivell ni especialitat
        {"level": levels[0], "source": "inventat"},
        {"level": levels[0], "source": Source.DECLARED, "verified_by": manager},  # sense data
    ):
        with pytest.raises(IntegrityError), transaction.atomic():
            DiverCertification.objects.create(person=person, **broken)
    kept = cert(person, level=levels[0], source=Source.CLUB_COURSE, issuer="C.R.I.S.")
    assert certifications.origin(kept) == certifications.CLUB
    assert list(certifications.of(person)) == [kept]
    assert str(kept) == "Nivell inventat B1"


# --- RGPD del mòdul (M02-8; L-M02-07) -------------------------------------------------------------


def test_the_module_registers_its_gdpr_part_in_the_common_base():
    module = core_privacy._MODULES["activitats"]
    assert module.export is privacy.export_personal_data
    assert module.anonymise is privacy.anonymise


def test_the_export_has_only_the_data_of_the_person(manager, levels, make_admin):  # noqa: F811
    teacher = make_admin("instructor")
    other = a_person("Una altra persona")
    cert(teacher.person, level=levels[0], number="NUM-INVENTAT-1", agency="Agència inventada")
    cert(other, level=levels[1], number="NUM-D-UNA-ALTRA")
    course = a_course(manager, responsible=teacher.person)
    sessions.add_session(
        course,
        by=manager,
        kind=Session.Kind.SEA,
        starts_at=at(2027, 6, 14, 9),
        ends_at=at(2027, 6, 14, 11),
        instructors=[teacher.person],
    )
    data = privacy.export_personal_data(teacher.person)
    assert [c["numero"] for c in data["titulacions"]] == ["NUM-INVENTAT-1"]
    assert data["titulacions"][0]["nivell"] == "Nivell inventat B1"
    assert len(data["sessions_on_fa_classe"]) == 1
    assert [a["activitat"] for a in data["activitats_de_que_es_responsable"]] == [course.title]
    assert "NUM-D-UNA-ALTRA" not in str(data)
    assert privacy.export_personal_data(a_person("Sense res")) == {
        "titulacions": [],
        "sessions_on_fa_classe": [],
        "activitats_de_que_es_responsable": [],
    }


def test_l_m02_07_anonymising_removes_what_identifies_and_frees_future_sessions(
    manager,
    levels,
    make_admin,  # noqa: F811
):
    admin = make_admin("administrator")
    teacher = make_admin("instructor")
    person = teacher.person
    kept = cert(person, level=levels[0], number="NUM-INVENTAT-1")
    course = a_course(manager, responsible=person)
    session = sessions.add_session(
        course,
        by=manager,
        kind=Session.Kind.SEA,
        starts_at=at(2027, 6, 14, 9),
        ends_at=at(2027, 6, 14, 11),
        instructors=[person],
    )
    lines = privacy.describe(person)
    assert len(lines) == 3 and "NUM-INVENTAT-1" not in " ".join(lines)
    assert privacy.audit_targets(person) == {"activities.divercertification": [str(kept.pk)]}
    with pytest.raises(ValueError, match="anonimitzada"):
        privacy.anonymise(person, by=admin)

    Person.objects.filter(pk=person.pk).update(
        status=Person.Status.ANONYMISED, anonymous_ref="anonima-de-proves-3"
    )
    person.refresh_from_db()
    privacy.anonymise(person, by=admin)
    kept.refresh_from_db()
    assert kept.number == "" and kept.level == levels[0]  # el nivell es conserva, sense número
    assert not session.instructors.exists()
    entry = AuditEntry.objects.get(action=privacy.CERTIFICATION_ANONYMISED)
    assert entry.actor_account == admin
    # L'activitat no es reassigna sola: continua lligada a la persona, que ja no té nom.
    course.refresh_from_db()
    assert course.responsible == person and Activity.objects.count() == 1
    assert privacy.describe(a_person("Sense res")) == []
