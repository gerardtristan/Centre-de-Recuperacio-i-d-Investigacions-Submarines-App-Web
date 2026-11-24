"""Avisos de venciment, enviament (T-M06-11; CA-M06-08, 09 i 24; RN-M06-12). Dades inventades."""

import datetime

import pytest

from apps.accounts.models import Account
from apps.core.models import OutgoingEmail, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import reminders, tasks
from apps.licences.models import LicenceReminder, LicenceReminderDigest, LicenceType
from apps.licences.tests.test_reminders import EXT, at
from conftest import PASSWORD

D = datetime.date


def sent(template=reminders.REMINDER_TEMPLATE):
    return list(OutgoingEmail.objects.filter(template=template).order_by("pk"))


def run(today):
    """La tasca diària i els lots, com els faria la cua."""
    for days, ids in reminders.plan(today):
        reminders.send_batch(days, ids)


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    account = make_admin(Role.Code.SECRETARY)
    account.notification_email = "secretaria@example.org"
    account.save()
    return account


@pytest.fixture
def holders(make_licence, make_person):
    def make(n, **fields):
        return [
            make_licence(
                person=make_person(f"Titular{i}", "Inventat", contact_email=f"t{i}@example.org"),
                **EXT, **fields,
            )
            for i in range(n)
        ]  # fmt: skip

    return make


def test_ca_m06_08_one_reminder_per_tram_and_none_repeated(holders, secretary):
    (licence,) = holders(1)
    for days in (60, 30, 7):
        run(at(days))
        run(at(days))  # la tasca es repeteix el mateix dia
    emails = sent()
    assert [e.to_address for e in emails] == ["t0@example.org"] * 3
    assert sorted(licence.reminders.values_list("days_before", flat=True)) == [7, 30, 60]
    assert "31/12/2027" in emails[0].subject and "d'aquí a 60 dies" in emails[0].body_text


def test_ca_m06_24_batches_one_digest_and_nothing_more_on_a_repeat(
    holders, secretary, make_licence, make_person, settings
):
    settings.LICENCE_REMINDER_BATCH_SIZE = 3
    holders(6)
    technical = LicenceType.objects.create(name="Tècnic (inventat)", category="technical",
                                           validity_rule="calendar_year")  # fmt: skip
    make_licence(person=make_person("Pere", "Roca", contact_email="pere@example.org"),
                 licence_type=technical, **EXT)  # fmt: skip
    batches = reminders.plan(at(60))
    assert [(days, len(ids)) for days, ids in batches] == [(60, 3), (60, 3), (60, 1)]
    for days, ids in batches:
        reminders.send_batch(days, ids)
    run(at(60))
    assert len(sent()) == 7 and LicenceReminder.objects.count() == 7
    (digest,) = sent(reminders.DIGEST_TEMPLATE)
    assert digest.to_address == "secretaria@example.org"
    assert "- 31/12/2027 · Aficionat: 6" in digest.body_text
    assert "- 31/12/2027 · Tècnic: 1" in digest.body_text
    assert "Inventat" not in digest.body_text and "Roca" not in digest.body_text  # P-501
    row = LicenceReminderDigest.objects.get()
    assert (row.day, row.days_before, row.count, row.sent_to) == (at(60), 60, 7, 1)


def test_two_plans_before_the_batches_run_send_each_reminder_once(holders, secretary):
    holders(2)
    batches = reminders.plan(at(60)) + reminders.plan(at(60))  # la tasca diària, dues vegades
    assert len(batches) == 2  # els mateixos lots, encara sense enviar
    for days, ids in batches:
        reminders.send_batch(days, ids)
    assert len(sent()) == 2 and LicenceReminder.objects.count() == 2
    assert len(sent(reminders.DIGEST_TEMPLATE)) == 1


def test_a_digest_sent_meanwhile_is_not_repeated(holders, secretary):
    holders(1)
    groups = reminders.digest(at(30))[30]
    reminders._send_digest(at(30), 30, groups)
    reminders._send_digest(at(30), 30, groups)  # una altra execució alhora
    assert len(sent(reminders.DIGEST_TEMPLATE)) == 1


def test_ca_m06_09_a_renewal_after_planning_stops_the_reminder(holders, make_licence):
    (licence,) = holders(1)
    ((days, ids),) = reminders.plan(at(30))
    make_licence(person=licence.person, status="paid", renewal_of=licence,
                 starts_on=D(2028, 1, 1), expires_on=D(2028, 12, 31))  # fmt: skip
    assert reminders.send_batch(days, ids) == 0
    assert not sent() and not LicenceReminder.objects.exists()


def test_the_link_is_the_personal_area_or_the_public_page(holders):
    with_account, guest = holders(2)
    Account.objects.create_personal(with_account.person, "t0@example.org", PASSWORD)
    run(at(7))
    links = {e.to_address: e.body_text for e in sent()}
    assert "/socis/llicencia/" in links["t0@example.org"]
    assert "/llicencies/" in links["t1@example.org"]  # P-502


def test_without_an_address_it_is_recorded_but_not_sent(make_licence, make_person):
    licence = make_licence(person=make_person("Sense", "Correu"), **EXT)
    run(at(7))
    assert not sent() and licence.reminders.filter(days_before=7).exists()


def test_the_daily_task_defers_one_task_per_batch(monkeypatch):
    calls = []
    monkeypatch.setattr(reminders, "plan", lambda: [(60, [1, 2]), (30, [3])])
    monkeypatch.setattr(tasks.send_reminder_batch, "defer", lambda **kw: calls.append(kw))
    tasks.send_reminders.func(timestamp=0)
    assert calls == [{"days_before": 60, "licence_ids": [1, 2]},
                     {"days_before": 30, "licence_ids": [3]}]  # fmt: skip
    monkeypatch.setattr(reminders, "send_batch", lambda days, ids: calls.append((days, ids)))
    tasks.send_reminder_batch.func(days_before=7, licence_ids=[4])
    assert calls[-1] == (7, [4])
