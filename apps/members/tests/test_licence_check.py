"""Comprovació diària de la còpia de la llicència (T-M01-31b; CA-M01-32 a 34; RN-M01-41 a 44).
Només dades inventades."""

import datetime

import pytest

from apps.core.models import AuditEntry, Person
from apps.members import licence_copy
from apps.members.models import LicenceRecord
from apps.members.tests.test_cards import make_member

pytestmark = pytest.mark.django_db
D = datetime.date


def row(person, licence=41, version=2, **fields):
    data = {"licence": licence, "person": person.pk, "licence_type": "Aficionat anual (inventat)",
            "starts_on": D(2027, 3, 15), "expires_on": D(2027, 12, 31), "cancelled_on": None,
            "version": version}  # fmt: skip
    data.update(fields)
    return data


@pytest.fixture
def source(monkeypatch):
    rows = []
    monkeypatch.setattr(licence_copy, "_source", lambda: list(rows))
    return rows


@pytest.fixture
def copy():
    member = make_member()
    return LicenceRecord.objects.create(
        member=member, licence_type="Aficionat anual (inventat)", issued_on=D(2027, 3, 15),
        expires_on=D(2027, 11, 30), source="licences", licence_ref=41, source_version=1,
    )  # fmt: skip


def test_ca_m01_32_a_different_expiry_is_corrected_once(source, copy):
    source.append(row(copy.member.person))
    assert licence_copy.daily_check()["corrected"] == 1
    copy.refresh_from_db()
    assert (copy.expires_on, copy.source_version) == (D(2027, 12, 31), 2)
    entry = AuditEntry.objects.get(action=licence_copy.ACTION_CORRECTED, field="expires_on")
    assert (entry.old_value, entry.actor_origin) == ("2027-11-30", "comprovació diària")
    assert licence_copy.daily_check()["corrected"] == 0


def test_ca_m01_33_without_a_source_nothing_happens(monkeypatch, copy):
    monkeypatch.setattr(licence_copy, "_source", None)
    assert licence_copy.daily_check() == {"skipped": "no_source"}


def test_ca_m01_33_a_row_the_06_does_not_have_is_kept_for_review(source, copy, make_person):
    source.append(row(make_person("Altra", "Persona"), licence=99))
    counts = licence_copy.daily_check()
    assert counts["to_review"] == [copy.pk]
    assert LicenceRecord.objects.filter(pk=copy.pk).exists()


@pytest.mark.parametrize("broken", ["error", "empty"])
def test_ca_m01_34_a_failing_or_empty_source_skips_everything(monkeypatch, copy, broken):
    def failing():
        raise ConnectionError("font inventada caiguda")

    monkeypatch.setattr(licence_copy, "_source", failing if broken == "error" else list)
    assert licence_copy.daily_check()["skipped"] in {"ConnectionError", "empty"}
    copy.refresh_from_db()
    assert copy.expires_on == D(2027, 11, 30)
    assert AuditEntry.objects.filter(action=licence_copy.ACTION_SKIPPED).exists()


def test_a_missing_copy_of_a_member_is_created_and_not_for_others(source):
    member = make_member("Pau", number=88, document="00000088Z")
    outsider = Person.objects.create(first_name="Laia", last_name="Fora", origin="web")
    source.extend([row(member.person, licence=50), row(outsider, licence=51),
                   row(member.person, licence=52, cancelled_on=D(2027, 4, 1))])  # fmt: skip
    assert licence_copy.daily_check()["created"] == 1
    assert list(LicenceRecord.objects.values_list("licence_ref", flat=True)) == [50]


def test_the_daily_task_calls_the_check(monkeypatch):
    from apps.members import tasks

    calls = []
    monkeypatch.setattr(licence_copy, "daily_check", lambda: calls.append(1))
    tasks.licence_check.func(timestamp=0)
    assert calls == [1]
