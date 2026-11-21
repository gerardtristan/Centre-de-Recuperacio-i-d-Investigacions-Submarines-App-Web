"""Avisos de venciment, part de servei (T-M06-11; CA-M06-08, 09, 24 i 26; RN-M06-12)."""

import datetime

import pytest

from apps.core import business_settings
from apps.core.models import AppendOnlyError
from apps.licences import reminders
from apps.licences.models import LicenceReminder, LicenceReminderDigest, LicenceType, ValidityRule

D = datetime.date
V = D(2027, 12, 31)
EXT = {"origin": "external", "price_kind": None, "price_cents": None, "status": "active"}


def at(days_before):
    return V - datetime.timedelta(days=days_before)


@pytest.fixture
def holder(make_licence, make_person):
    return make_licence(person=make_person("Anna", "Vila"), **EXT)


@pytest.mark.django_db
def test_the_initial_setting():
    assert business_settings.get(reminders.REMINDER_DAYS) == [60, 30, 7]


@pytest.mark.parametrize("days", [60, 30, 7])
def test_ca_m06_08_due_on_each_tram(holder, days):
    found = reminders.due(at(days))
    assert found[days] == [holder]
    assert all(lic == [] for tram, lic in found.items() if tram != days)


def test_nothing_on_other_days_or_for_single_day(holder, make_licence, make_person):
    single = {"validity_rule": ValidityRule.SINGLE_DAY, "starts_on": V, "expires_on": V}
    make_licence(person=make_person("Pau", "Roig"), **single, **EXT)
    assert not any(reminders.due(at(31)).values())
    assert reminders.due(at(30))[30] == [holder]


def test_an_already_sent_tram_is_not_due_again(holder):
    LicenceReminder.objects.create(licence=holder, days_before=30)
    assert reminders.due(at(30))[30] == []


def test_ca_m06_09_no_reminder_once_a_renewal_is_in_progress(holder, make_licence):
    make_licence(person=holder.person, status="paid", renewal_of=holder,
                 starts_on=D(2028, 1, 1), expires_on=D(2028, 12, 31))  # fmt: skip
    assert reminders.due(at(30))[30] == []


def test_ca_m06_26_the_trams_are_the_setting(holder, monkeypatch):
    real = business_settings.get
    monkeypatch.setattr(
        business_settings, "get",
        lambda key, at=None: [45, 15, 3] if key == reminders.REMINDER_DAYS else real(key, at),
    )  # fmt: skip
    assert list(reminders.due(at(45))) == [45, 15, 3]
    assert reminders.due(at(45))[45] == [holder]
    assert reminders.due(at(60)) == {45: [], 15: [], 3: []}


def test_ca_m06_24_digest_by_date_category_and_name(holder, make_licence, make_person):
    technical = LicenceType.objects.create(name="Tècnic (inventat)", category="technical",
                                           validity_rule="calendar_year")  # fmt: skip
    make_licence(person=make_person("Abel", "Vila"), **EXT)
    make_licence(person=make_person("Pere", "Roca"), licence_type=technical, **EXT)
    groups = reminders.digest(at(60))
    assert list(groups) == [60]
    (amateur_key, amateurs), (technical_key, technicals) = groups[60]
    assert (amateur_key, technical_key) == ((V, "amateur"), (V, "technical"))
    assert [lic.person.first_name for lic in amateurs] == ["Abel", "Anna"]
    assert [lic.person.first_name for lic in technicals] == ["Pere"]
    assert reminders.digest(at(59)) == {}


def test_reminder_rows_are_append_only(holder):
    reminder = LicenceReminder.objects.create(licence=holder, days_before=60)
    digest = LicenceReminderDigest.objects.create(day=at(60), days_before=60, count=1, sent_to=1)
    assert str(reminder).endswith("· 60") and str(digest) == "01/11/2027 · 60"
    with pytest.raises(AppendOnlyError):
        reminder.delete()
