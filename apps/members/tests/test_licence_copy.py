"""Còpia de lectura de la llicència del 06 (T-M01-31a; CA-M01-26, 27, 28, 30 i 31; RN-M01-35 a
40). Només dades inventades."""

import datetime

import pytest

from apps.core import events
from apps.core.models import AuditEntry, Event, Person
from apps.members import licence_copy
from apps.members.models import LicenceRecord
from apps.members.services import licence_record, licence_records
from apps.members.tests.test_cards import make_member

pytestmark = pytest.mark.django_db
D = datetime.date


def payload(person, licence=41, version=1, **fields):
    data = {"licence": licence, "person": person.pk, "licence_type": "Aficionat anual (inventat)",
            "category": "amateur", "validity_rule": "calendar_year", "starts_on": "2027-03-15",
            "expires_on": "2027-12-31", "origin": "club", "m01_record_ref": None,
            "version": version, "occurred_at": "2027-03-20T10:00:00+00:00"}  # fmt: skip
    data.update(fields)
    return data


def apply(name, data):
    licence_copy.on_licence_event(Event.objects.create(name=name, payload=data))


@pytest.fixture
def member():
    return make_member()


def test_ca_m01_26_issued_creates_the_copy(member):
    apply(events.LICENCE_ISSUED, payload(member.person))
    record = LicenceRecord.objects.get()
    assert (record.source, record.licence_ref, record.source_version) == ("licences", 41, 1)
    assert licence_record(member.person).expires_on == D(2027, 12, 31)
    assert AuditEntry.objects.filter(action=licence_copy.ACTION).count() == 1


def test_ca_m01_27_the_same_event_twice_changes_nothing(member):
    apply(events.LICENCE_ISSUED, payload(member.person))
    apply(events.LICENCE_ISSUED, payload(member.person, expires_on="2030-12-31"))
    assert LicenceRecord.objects.get().expires_on == D(2027, 12, 31)
    assert AuditEntry.objects.filter(action=licence_copy.ACTION).count() == 1


def test_ca_m01_28_cancelled_hides_it(member):
    apply(events.LICENCE_ISSUED, payload(member.person))
    apply(events.LICENCE_CANCELLED, payload(member.person, version=2))
    assert LicenceRecord.objects.get().cancelled_on == D(2027, 3, 20)
    assert licence_record(member.person) is None
    assert licence_records() == []


def test_a_cancellation_without_copy_does_nothing(member):
    apply(events.LICENCE_CANCELLED, payload(member.person, version=3))
    assert not LicenceRecord.objects.exists()


@pytest.mark.parametrize(("version", "applied"), [(2, False), (3, False), (4, True)])
def test_ca_m01_30_only_newer_versions(member, version, applied):
    apply(events.LICENCE_ISSUED, payload(member.person, version=3))
    apply(events.LICENCE_RENEWED, payload(member.person, version=version, expires_on="2028-12-31"))
    expected = D(2028, 12, 31) if applied else D(2027, 12, 31)
    assert LicenceRecord.objects.get().expires_on == expected


def test_ca_m01_31_renewed_before_issued_keeps_the_renewal(member):
    apply(events.LICENCE_RENEWED, payload(member.person, version=2, expires_on="2028-12-31"))
    apply(events.LICENCE_ISSUED, payload(member.person, version=1))
    assert LicenceRecord.objects.get().expires_on == D(2028, 12, 31)


def test_rn_m01_35_an_imported_licence_updates_its_origin_row(member):
    origin = LicenceRecord.objects.create(member=member, licence_type="De Cluber",
                                          issued_on=D(2026, 1, 1), source="cluber")  # fmt: skip
    apply(events.LICENCE_ISSUED, payload(member.person, origin="imported_m01",
                                          m01_record_ref=origin.pk))  # fmt: skip
    origin.refresh_from_db()
    assert LicenceRecord.objects.count() == 1
    assert (origin.licence_ref, origin.source, origin.expires_on) == (41, "cluber", D(2027, 12, 31))


def test_rn_m01_39_a_non_member_has_no_copy():
    person = Person.objects.create(first_name="Laia", last_name="Fora", origin="web")
    apply(events.LICENCE_ISSUED, payload(person))
    assert not LicenceRecord.objects.exists()


def test_the_members_app_subscribes_to_the_three_events():
    for name in licence_copy.NAMES:
        assert any(
            key.endswith("licence_copy.on_licence_event") for key in events._subscribers[name]
        )


def test_delivered_through_the_queue_mechanism(member):
    # 049: l'esdeveniment emès i lliurat (com ho fa la cua) arriba al subscriptor del 01.
    event = events.emit(events.LICENCE_ISSUED, payload(member.person))
    events.deliver(event.pk)
    events.deliver(event.pk)
    assert LicenceRecord.objects.get().licence_ref == 41
