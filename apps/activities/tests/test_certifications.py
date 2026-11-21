"""Nivells i titulacions d'una persona, i el RGPD del 02 (T-M02-23; addenda de la 058; RN-M02-27,
28, 30 i 32; L-M02-07). Només dades inventades.
"""

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

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
