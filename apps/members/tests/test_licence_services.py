"""Proves de contracte del servei de lectura de la llicència (T-M01-30; decisió 049, M01-8).

`members.licence_record(person)` i `members.licence_records()`: no escriuen res, tornen res (o
una llista buida) si no hi ha registre, tornen dades immutables amb la forma del contracte i
segueixen l'ordre de RN-M01-50 (caducitat coneguda més tardana primer). La marca explícita de
caducitat desconeguda és de la T-M01-34. Només dades inventades.
"""

import contextlib
import dataclasses
import datetime

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.core.models import AuditEntry, Person
from apps.members.models import LicenceRecord
from apps.members.services import LicenceInfo, licence_record, licence_records
from apps.members.tests.test_member_edit import a_member

pytestmark = pytest.mark.django_db

ISSUED = datetime.date(2026, 1, 15)
EXPIRES = datetime.date(2026, 12, 31)


def a_record(member, *, licence_type="Anual FECDAS", issued_on=ISSUED, expires_on=EXPIRES):
    return LicenceRecord.objects.create(
        member=member,
        licence_type=licence_type,
        issued_on=issued_on,
        expires_on=expires_on,
        source=LicenceRecord.Source.MANUAL,
    )


@contextlib.contextmanager
def read_only(max_queries=1):
    """Falla si el bloc fa cap consulta que no sigui de lectura o canvia cap recompte."""
    before = (LicenceRecord.objects.count(), AuditEntry.objects.count())
    with CaptureQueriesContext(connection) as queries:
        yield
    sql = [q["sql"].lstrip().upper() for q in queries]
    assert sql and all(s.startswith("SELECT") for s in sql), sql
    assert len(sql) <= max_queries
    assert (LicenceRecord.objects.count(), AuditEntry.objects.count()) == before


def info(record):
    return LicenceInfo(
        record_id=record.pk,
        person_id=record.member.person_id,
        licence_type=record.licence_type,
        issued_on=record.issued_on,
        expires_on=record.expires_on,
    )


class TestContract:
    def test_shape_is_exact(self):
        assert [f.name for f in dataclasses.fields(LicenceInfo)] == [
            "record_id",
            "person_id",
            "licence_type",
            "issued_on",
            "expires_on",
        ]

    def test_result_is_immutable_and_not_the_model(self):
        member = a_member()
        a_record(member)
        result = licence_record(member.person)
        assert not isinstance(result, LicenceRecord)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.expires_on = datetime.date(2030, 1, 1)
        assert not hasattr(result, "save")


class TestLicenceRecord:
    def test_returns_the_record(self):
        member = a_member()
        record = a_record(member)
        with read_only():
            result = licence_record(member.person)
        assert result == info(record)
        assert result.licence_type == "Anual FECDAS"
        assert (result.issued_on, result.expires_on) == (ISSUED, EXPIRES)

    def test_member_without_record_returns_none(self):
        member = a_member()
        with read_only():
            assert licence_record(member.person) is None

    def test_person_who_is_not_a_member_returns_none(self):
        person = Person.objects.create(first_name="Pere", origin=Person.Origin.GUEST)
        with read_only():
            assert licence_record(person) is None

    def test_only_the_persons_own_record(self):
        anna, bernat = a_member(), a_member("Bernat", document=("passport", "PROVA0002"))
        a_record(bernat)
        assert licence_record(anna.person) is None
        assert licence_record(bernat.person).person_id == bernat.person_id

    def test_latest_known_expiry_first(self):
        member = a_member()
        a_record(
            member, expires_on=datetime.date(2025, 12, 31), issued_on=datetime.date(2025, 1, 1)
        )
        latest = a_record(member, expires_on=datetime.date(2027, 12, 31))
        a_record(member, expires_on=EXPIRES)
        with read_only():
            assert licence_record(member.person) == info(latest)

    def test_unknown_expiry_only_if_no_known_one(self):
        # RN-M01-50: la fila sense data, només si no n'hi ha cap amb data. La marca «desconeguda»
        # és de la T-M01-34; aquí, `expires_on` és None.
        member = a_member()
        a_record(member, expires_on=None, issued_on=datetime.date(2026, 6, 1))
        known = a_record(member, expires_on=datetime.date(2026, 3, 31))
        assert licence_record(member.person) == info(known)

        other = a_member("Bernat", document=("passport", "PROVA0002"))
        unknown = a_record(other, expires_on=None)
        result = licence_record(other.person)
        assert result == info(unknown)
        assert result.expires_on is None

    def test_same_expiry_latest_issue_then_latest_record(self):
        member = a_member()
        a_record(member, issued_on=datetime.date(2026, 1, 1))
        later = a_record(member, issued_on=datetime.date(2026, 2, 1))
        assert licence_record(member.person) == info(later)
        newest = a_record(member, issued_on=datetime.date(2026, 2, 1))
        assert licence_record(member.person) == info(newest)

    def test_member_status_does_not_filter(self):
        # Supòsit (per revisar): el servei llegeix el registre; si és soci o no, ho diu
        # `members.is_member`.
        member = a_member()
        record = a_record(member)
        member.status = member.Status.LEFT
        member.save(update_fields=["status"])
        assert licence_record(member.person) == info(record)

    def test_anonymised_person_still_returns_the_record(self):
        # Supòsit (per revisar): el registre no porta dades personals (tipus i dates) i no
        # s'esborra (RN-M01-36); el servei no filtra les persones anonimitzades.
        member = a_member()
        record = a_record(member)
        Person.objects.filter(pk=member.person_id).update(
            status=Person.Status.ANONYMISED, anonymous_ref="A-0001"
        )
        member.person.refresh_from_db()
        with read_only():
            assert licence_record(member.person) == info(record)


class TestLicenceRecords:
    def test_no_records_returns_an_empty_list(self):
        a_member()
        with read_only():
            assert licence_records() == []

    def test_every_record_of_every_member(self):
        anna = a_member()
        bernat = a_member("Bernat", document=("passport", "PROVA0002"))
        a_member("Carla", document=("passport", "PROVA0003"))  # sense registre
        old = a_record(
            anna, expires_on=datetime.date(2025, 12, 31), issued_on=datetime.date(2025, 1, 1)
        )
        unknown = a_record(anna, expires_on=None)
        current = a_record(anna, expires_on=datetime.date(2027, 12, 31))
        other = a_record(bernat)
        with read_only():
            result = licence_records()
        assert sorted(r.record_id for r in result) == sorted(
            r.pk for r in (old, unknown, current, other)
        )
        assert set(result) == {info(r) for r in (old, unknown, current, other)}
        assert all(isinstance(r, LicenceInfo) for r in result)

    def test_first_of_each_person_is_licence_record(self):
        anna = a_member()
        bernat = a_member("Bernat", document=("passport", "PROVA0002"))
        a_record(anna, expires_on=None)
        a_record(anna, expires_on=datetime.date(2027, 12, 31))
        a_record(bernat, expires_on=None)
        result = licence_records()
        first = {}
        for row in result:
            first.setdefault(row.person_id, row)
        assert first == {
            anna.person_id: licence_record(anna.person),
            bernat.person_id: licence_record(bernat.person),
        }
        persons = [row.person_id for row in result]
        assert persons == sorted(persons)

    def test_one_query_whatever_the_number_of_records(self):
        for n in range(5):
            member = a_member(f"Soci{n}", document=("passport", f"PROVA01{n:02d}"))
            a_record(member)
        with read_only(max_queries=1):
            assert len(licence_records()) == 5
