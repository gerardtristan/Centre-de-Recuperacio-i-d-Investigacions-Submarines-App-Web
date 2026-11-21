"""Agències com a dada, `source = federation`, `official_level` i els ajustos VC-55 a VC-59
(T-M02-41; addenda de la 104). Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models import ProtectedError
from django.http import Http404

from apps.activities import catalogue
from apps.activities.models import (
    CertificationAgency,
    CertificationLevel,
    DiverCertification,
    TrainingCatalogueEntry,
)
from apps.core import business_settings
from apps.core.models import Person, Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from conftest import CommittedDataTestCase

from .helpers import a_person, an_entry

pytestmark = pytest.mark.django_db


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def test_the_initial_agencies_and_the_target_are_data(manager):
    names = set(CertificationAgency.objects.values_list("name", flat=True))
    assert {"FECDAS", "PADI", "SSI", "CMAS", "NAUI"} <= names
    assert business_settings.get(catalogue.TARGET_AGENCY_KEY) == "FECDAS"
    assert catalogue.target_agency().name == "FECDAS"


@pytest.mark.parametrize(
    ("key", "initial", "bounds"),
    [
        ("activities.card_photos_enabled", False, (None, None)),
        ("activities.card_photo_retention_months", 3, (0, 24)),
        ("activities.homologation_fee_cents", 0, (0, None)),
        ("activities.course_filing_fee_cents", 0, (0, None)),
        ("activities.filing_fees_enabled", False, (None, None)),
    ],
)
def test_vc_56_to_59_start_off_or_at_zero(key, initial, bounds):
    setting = Setting.objects.get(key=key)
    assert business_settings.get(key) == initial
    assert (setting.min_value, setting.max_value) == bounds
    if key.endswith("_fee_cents"):  # diners: data d'entrada en vigor i avís (RN-AJ-04)
        assert setting.affects_money and setting.effective_dated


def test_vc_55_the_target_must_be_an_active_agency(manager):
    catalogue.check_target_agency("PADI")
    for wrong in ("Una agència inventada", ""):
        with pytest.raises(ValidationError):
            catalogue.check_target_agency(wrong)
    padi = CertificationAgency.objects.get(name="PADI")
    catalogue.set_active(padi, False, by=manager)
    with pytest.raises(ValidationError):
        catalogue.check_target_agency("PADI")


def test_vc_55_agencies_are_kept_by_ac6_and_never_deleted_with_certifications(
    manager,
    make_admin,  # noqa: F811
):
    agency = catalogue.create_agency(by=manager, name="Agència inventada")
    with pytest.raises(ValidationError):
        catalogue.create_agency(by=manager, name="Agència inventada")
    with pytest.raises(Http404):
        catalogue.create_agency(by=make_admin("secretary"), name="Una altra inventada")
    level = catalogue.create_level(by=manager, name="Nivell inventat", rank=10, agency=agency)
    DiverCertification.objects.create(
        person=a_person("Bussejadora"), level=level, agency=agency, source="federation"
    )
    with pytest.raises(ProtectedError):
        agency.delete()
    assert catalogue.set_active(agency, False, by=manager) is True
    assert CertificationAgency.objects.get(pk=agency.pk).active is False


def test_source_federation_is_valid_and_others_are_not(manager):
    level = catalogue.create_level(by=manager, name="Nivell inventat", rank=10)
    person = a_person("Bussejadora")
    DiverCertification.objects.create(person=person, level=level, source="federation")
    with pytest.raises(IntegrityError), transaction.atomic():
        DiverCertification.objects.create(person=person, level=level, source="altre")


def test_official_level_on_the_catalogue_entry(manager):
    level = catalogue.create_level(by=manager, name="Primera estrella (inventada)", rank=10)
    entry = an_entry(manager)
    TrainingCatalogueEntry.objects.filter(pk=entry.pk).update(official_level=level)
    entry.refresh_from_db()
    assert entry.official_level == level


class TestAgencyTextToForeignKey(CommittedDataTestCase):
    """La migració converteix el text en agències (i les crea si no hi són) i torna enrere."""

    BEFORE = [("activities", "0012_void_pending_since")]

    def test_text_becomes_an_agency_and_back(self):
        executor = MigrationExecutor(connection)
        leaves = executor.loader.graph.leaf_nodes()
        person = Person.objects.create(first_name="Bussejadora", origin="in_person")
        try:
            MigrationExecutor(connection).migrate(self.BEFORE)
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO activities_certificationlevel (name, rank, agency, active) "
                    "VALUES ('Nivell antic inventat', 77, 'PADI', true) RETURNING id"
                )
                level_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO activities_divercertification (person_id, level_id, agency, "
                    "issuer, number, certificate_number, source, created_at) VALUES "
                    "(%s, %s, 'Agència antiga inventada', '', '', '', 'declared', now()) "
                    "RETURNING id",
                    [person.pk, level_id],
                )
                cert_id = cursor.fetchone()[0]
        finally:
            MigrationExecutor(connection).migrate(leaves)
        assert CertificationLevel.objects.get(pk=level_id).agency.name == "PADI"
        cert = DiverCertification.objects.get(pk=cert_id)
        assert cert.agency.name == "Agència antiga inventada"  # creada en convertir
        try:
            MigrationExecutor(connection).migrate(self.BEFORE)
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT agency FROM activities_divercertification WHERE id = %s", [cert_id]
                )
                assert cursor.fetchone()[0] == "Agència antiga inventada"
        finally:
            MigrationExecutor(connection).migrate(leaves)
