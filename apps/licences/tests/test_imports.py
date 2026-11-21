"""Pas únic dels registres del 01 al 06 (T-M06-14; P-M06-H; CA-M06-14; LC11). Només dades
inventades: mai dades reals de socis."""

import datetime

import pytest
from django.http import Http404

from apps.core import events
from apps.core.models import Event, ImportBatch, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import imports
from apps.licences.models import Licence, LicenceType
from apps.members.models import LicenceRecord
from apps.members.services import licence_record
from apps.members.tests.test_cards import make_member

D = datetime.date
R = Role.Code
END_2027 = D(2027, 12, 31)


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def records(annual):
    def record(first, number, licence_type="Aficionat anual (inventat)", expires=END_2027):
        member = make_member(first, number=number, document=f"{number:08d}Z")
        return LicenceRecord.objects.create(member=member, licence_type=licence_type,
                                            issued_on=D(2027, 1, 10), expires_on=expires,
                                            source="cluber")  # fmt: skip

    return {
        "new": record("Anna", 1),
        "lower": record("Pau", 2, licence_type="aficionat ANUAL (inventat)"),
        "no_expiry": record("Eva", 3, expires=None),
        "unknown": record("Joan", 4, licence_type="Tipus que el 06 no té"),
    }


def test_ca_m06_14_preview_writes_nothing(admin, records):
    rows = imports.preview(admin)
    assert imports.summary(rows) == {"new": 2, "no_expiry": 1, "unknown_type": 1}
    assert not Licence.objects.exists() and not ImportBatch.objects.exists()


def test_ca_m06_14_confirm_creates_imported_licences_and_the_01_keeps_one_row(admin, records):
    batch = imports.confirm(admin)
    assert (batch.kind, batch.status, batch.new_count, batch.error_count, batch.excluded_count) == (
        "licences", "confirmed", 3, 1, 0,
    )  # fmt: skip
    licences = Licence.objects.filter(import_batch=batch)
    assert {lic.m01_record_ref for lic in licences} == {
        records["new"].pk, records["lower"].pk, records["no_expiry"].pk,
    }  # fmt: skip
    assert all(lic.origin == "imported_m01" and lic.status == "active" and lic.charge is None
               for lic in licences)  # fmt: skip
    for event in Event.objects.filter(name=events.LICENCE_ISSUED):
        events.deliver(event.pk)
    records["new"].refresh_from_db()
    assert records["new"].licence_ref == licences.get(m01_record_ref=records["new"].pk).pk
    assert LicenceRecord.objects.count() == 4  # cap fila nova al 01 (RN-M01-35)
    assert imports.summary(imports.preview(admin))["existing"] == 3
    with pytest.raises(imports.NothingToImport):
        imports.confirm(admin)


def test_ca_m06_14_undo_the_batch(admin, records):
    batch = imports.confirm(admin)
    for event in Event.objects.filter(name=events.LICENCE_ISSUED):
        events.deliver(event.pk)
    undone = imports.undo(batch, admin)
    assert undone.status == "undone" and not Licence.objects.exists()
    records["new"].refresh_from_db()
    assert records["new"].licence_ref is None
    assert licence_record(records["new"].member.person).expires_on == D(2027, 12, 31)


def test_a_changed_batch_cannot_be_undone(admin, records):
    batch = imports.confirm(admin)
    licence = Licence.objects.filter(import_batch=batch).first()
    licence.federation_number = "F-1"
    licence.save(update_fields=["federation_number"])
    with pytest.raises(imports.CannotUndo):
        imports.undo(batch, admin)
    assert Licence.objects.filter(import_batch=batch).count() == 3


def test_a_referenced_licence_cannot_be_undone(admin, records, make_licence):
    batch = imports.confirm(admin)
    original = Licence.objects.filter(import_batch=batch).first()
    make_licence(person=original.person, renewal_of=original, starts_on=D(2028, 1, 1),
                 expires_on=D(2028, 12, 31))  # fmt: skip
    with pytest.raises(imports.CannotUndo):
        imports.undo(batch, admin)


def test_only_a_confirmed_licences_batch_can_be_undone(admin, records):
    batch = imports.confirm(admin)
    imports.undo(batch, admin)
    with pytest.raises(imports.CannotUndo):
        imports.undo(batch, admin)


@pytest.mark.parametrize("role", [R.SECRETARY, R.TREASURER, R.PRESIDENT])
def test_only_lc11(make_admin, records, role):  # noqa: F811
    actor = make_admin(role)
    with pytest.raises(Http404):
        imports.preview(actor)
    with pytest.raises(Http404):
        imports.confirm(actor)


def test_an_unknown_type_never_creates_a_type(admin, records):
    imports.confirm(admin)
    assert list(LicenceType.objects.values_list("name", flat=True)) == [
        "Aficionat anual (inventat)"
    ]
