"""Nivells i titulacions d'una persona, i el RGPD del 02 (T-M02-23; addenda de la 058; RN-M02-27,
28, 30 i 32; L-M02-07). Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils import timezone

from apps.activities import certification_records as records
from apps.activities import certifications, privacy
from apps.activities.models import (
    CertificationLevel,
    DiverCertification,
    TrainingCatalogueEntry,
)
from apps.core import privacy as core_privacy
from apps.core.models import AuditEntry, Department, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db
SOURCE = DiverCertification.Source


@pytest.fixture
def person():
    return Person.objects.create(first_name="Bussejadora", last_name="Prova", origin="in_person")


@pytest.fixture
def levels():
    return {
        name: CertificationLevel.objects.create(name=name, rank=rank)
        for name, rank in (("B1", 10), ("B2", 20), ("B3", 30))
    }


@pytest.fixture
def nitrox():
    return TrainingCatalogueEntry.objects.create(
        kind="speciality",
        name="Nitrox inventat",
        default_places=6,
        price_member_cents=0,
        price_non_member_cents=0,
        department=Department.objects.get(name=Department.GENERAL),
    )


def held(person, **fields):
    return DiverCertification.objects.create(person=person, **{"source": SOURCE.DECLARED, **fields})


def verify(certification, account):
    DiverCertification.objects.filter(pk=certification.pk).update(
        verified_by=account, verified_at=timezone.now()
    )
    certification.refresh_from_db()
    return certification


def test_rn_m02_30_the_three_origins_and_what_counts_in_each_mode(person, levels, make_admin):  # noqa: F811
    secretary = make_admin(Role.Code.SECRETARY)
    declared = held(person, level=levels["B1"])
    club = held(person, level=levels["B1"], source=SOURCE.CLUB_COURSE)
    checked = verify(held(person, level=levels["B1"], source=SOURCE.IMPORTED), secretary)
    assert [certifications.origin(c) for c in (declared, club, checked)] == [
        "unverified",
        "club",
        "verified",
    ]
    assert not certifications.counts(declared, "block") and certifications.counts(declared, "warn")
    assert certifications.counts(club, "block") and certifications.counts(checked, "block")


def test_rn_m02_27_a_higher_level_meets_a_lower_minimum_and_the_best_origin_wins(person, levels):
    assert certifications.level_held(person, levels["B1"]) is None
    held(person, level=levels["B2"])
    best = certifications.level_held(person, levels["B1"])
    assert (best.certification.level, best.origin) == (levels["B2"], "unverified")
    assert certifications.level_held(person, levels["B3"]) is None
    club = held(person, level=levels["B3"], source=SOURCE.CLUB_COURSE)
    assert certifications.level_held(person, levels["B1"]).certification == club
    assert str(certifications.level_held(person, levels["B1"]).origin_label) == "d'un curs del club"


def test_a_speciality_is_held_by_its_catalogue_entry(person, nitrox):
    assert certifications.speciality_held(person, nitrox) is None
    held(person, speciality=nitrox)
    assert certifications.speciality_held(person, nitrox).certification.speciality == nitrox


@pytest.mark.parametrize(
    "wrong",
    [
        {},  # ni nivell ni especialitat
        {"source": "found", "with_level": True},
        {"verified_at": timezone.now(), "with_level": True},  # verificada sense qui
    ],
)
def test_certification_constraints_are_in_the_database(person, levels, wrong):
    data = dict(wrong)
    if data.pop("with_level", False):
        data["level"] = levels["B1"]
    with pytest.raises(IntegrityError), transaction.atomic():
        DiverCertification.objects.create(person=person, **{"source": SOURCE.DECLARED, **data})


def test_level_names_and_ranks_are_unique(levels):
    for data in ({"name": "B1", "rank": 99}, {"name": "B9", "rank": 10}):
        with pytest.raises(IntegrityError), transaction.atomic():
            CertificationLevel.objects.create(**data)


# --- RGPD (M02-8, L-M02-07) -----------------------------------------------------------------------


def test_the_02_is_registered_for_export_and_erasure():
    module = core_privacy._MODULES["activitats"]
    assert (module.export, module.anonymise) == (privacy.export, privacy.anonymise)


def test_export_has_the_certifications_and_nobody_else(person, levels, nitrox):
    held(person, level=levels["B2"], number="N-123", issuer="Agència inventada")
    held(person, speciality=nitrox)
    other = Person.objects.create(first_name="Altra", origin="in_person")
    held(other, level=levels["B3"], number="N-999")
    data = privacy.export(person)
    assert [(c["nivell"], c["especialitat"], c["numero"]) for c in data["titulacions"]] == [
        ("B2", None, "N-123"),
        (None, "Nitrox inventat", ""),
    ]
    assert "N-999" not in str(data)
    assert data["sessions_on_fa_classe"] == data["activitats_de_que_es_responsable"] == []


def test_erasure_clears_the_certificate_number_and_keeps_the_rest(person, levels, make_admin):  # noqa: F811
    admin = make_admin(Role.Code.ADMINISTRATOR)
    cert = held(person, level=levels["B2"], number="N-123")
    assert privacy.describe(person) == ["Té 1 titulació: se n'esborrarà el número."]
    assert privacy.audit_targets(person) == {"activities.divercertification": [str(cert.pk)]}
    privacy.anonymise(person, by=admin)
    cert.refresh_from_db()
    assert (cert.number, cert.level) == ("", levels["B2"])
    assert AuditEntry.objects.get(action=privacy.CERTIFICATION_ANONYMISED).actor_account == admin


# --- Titulacions inicials carregades a mà i verificades amb AC29 (T-M02-52; RN-M02-32) -------

R = Role.Code


@pytest.mark.parametrize("role", [R.SECRETARY, R.COURSES_MANAGER, R.ADMINISTRATOR])
def test_rn_m02_32_ac29_loads_an_unverified_certification_and_verifies_it(
    person,
    levels,
    make_admin,  # noqa: F811
    role,
):
    account = make_admin(role)
    loaded = records.load(
        person, by=account, source=SOURCE.IMPORTED, level=levels["B2"], number=" 123 ",
        issued_on=datetime.date(2020, 5, 4),
    )  # fmt: skip
    assert (loaded.source, loaded.number, loaded.is_verified) == (SOURCE.IMPORTED, "123", False)
    assert loaded.agency_id == levels["B2"].agency_id
    assert not certifications.counts(loaded, "block")  # RN-M02-30: sense verificar
    when = datetime.datetime(2026, 11, 24, 10, tzinfo=datetime.UTC)
    verified = records.verify(loaded, by=account, now=when)
    assert (verified.verified_by, verified.verified_at) == (account, when)
    assert certifications.counts(verified, "block")
    actions = set(AuditEntry.objects.values_list("action", flat=True))
    assert {records.LOADED, records.VERIFIED} <= actions


def test_a_speciality_is_loaded_as_declared(person, nitrox, make_admin):  # noqa: F811
    account = make_admin(R.SECRETARY)
    loaded = records.load(person, by=account, source=SOURCE.DECLARED, speciality=nitrox)
    assert (loaded.speciality, loaded.level, loaded.source) == (nitrox, None, SOURCE.DECLARED)


@pytest.mark.parametrize("role", [R.BOARD, R.TREASURER, R.PRESIDENT, R.INSTRUCTOR])
def test_without_ac29_or_read_only_nothing_is_loaded_or_verified(person, levels, make_admin, role):  # noqa: F811
    account = make_admin(role)
    with pytest.raises(Http404):
        records.load(person, by=account, source=SOURCE.DECLARED, level=levels["B1"])
    pending = held(person, level=levels["B1"])
    with pytest.raises(Http404):
        records.verify(pending, by=account)
    pending.refresh_from_db()
    assert not pending.is_verified and DiverCertification.objects.count() == 1


@pytest.mark.parametrize(
    "case",
    ["club_course", "federation", "both", "none", "long_number", "not_a_level", "not_a_speciality"],
)
def test_an_invalid_load_is_rejected_and_nothing_is_saved(person, levels, nitrox, make_admin, case):  # noqa: F811
    fields = {"source": SOURCE.DECLARED, "level": levels["B1"]}
    if case in ("club_course", "federation"):
        fields["source"] = case
    elif case == "both":
        fields["speciality"] = nitrox
    elif case == "none":
        del fields["level"]
    elif case == "long_number":
        fields["number"] = "x" * 41
    elif case == "not_a_level":
        fields["level"] = nitrox
    else:
        fields = {"source": SOURCE.DECLARED, "speciality": levels["B1"]}
    with pytest.raises(ValidationError):
        records.load(person, by=make_admin(R.SECRETARY), **fields)
    assert not DiverCertification.objects.exists()


def test_verifying_twice_keeps_the_first_and_club_ones_are_not_verified_by_hand(
    person,
    levels,
    make_admin,  # noqa: F811
):
    first, second = make_admin(R.SECRETARY), make_admin(R.ADMINISTRATOR)
    loaded = records.load(person, by=first, source=SOURCE.DECLARED, level=levels["B1"])
    records.verify(loaded, by=first)
    assert records.verify(loaded, by=second).verified_by == first
    assert AuditEntry.objects.filter(action=records.VERIFIED).count() == 1
    club = held(person, level=levels["B2"], source=SOURCE.CLUB_COURSE)
    with pytest.raises(ValidationError):
        records.verify(club, by=first)
