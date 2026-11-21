"""Esdeveniments i avisos del 06 (T-M06-15; RN-M06-17; CA-M06-07, 13, 17, 19 i 23)."""

import datetime

import pytest

from apps.core import audit, charges, events
from apps.core.models import Event, OutgoingEmail, Payment, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import day, filing
from apps.licences import events as licence_events
from apps.licences.models import Licence, ValidityRule
from apps.licences.services import cancel, declare_existing
from apps.licences.tests.test_request import ask, options, priced, soci  # noqa: F401 (fixtures)

D = datetime.date
R = Role.Code
SYSTEM = audit.system("proves-t-m06-15")


def emitted(name):
    return [event.payload for event in Event.objects.filter(name=name).order_by("pk")]


def mails(template):
    return sorted(
        OutgoingEmail.objects.filter(template=template).values_list("to_address", flat=True)
    )


@pytest.fixture
def staff(make_admin):  # noqa: F811
    accounts = {}
    for role, email in (
        (R.SECRETARY, "secretaria@example.org"),
        (R.TREASURER, "tresor@example.org"),
    ):
        account = make_admin(role)
        account.notification_email = email
        account.save()
        accounts[role] = account
    return accounts


def test_a_declared_licence_is_issued_with_version_1(options, soci, annual):  # noqa: F811
    licence = declare_existing(
        soci.person, annual, federation_number="F-1", expires_on=D(2027, 12, 31), actor=soci,
        today=D(2027, 3, 15),
    )  # fmt: skip
    (issued,) = emitted(events.LICENCE_ISSUED)
    keys = ("licence", "person", "version", "origin", "validity_rule", "starts_on", "expires_on",
            "m01_record_ref")  # fmt: skip
    assert {key: issued[key] for key in keys} == {
        "licence": licence.pk, "person": soci.person.pk, "version": 1, "origin": "external",
        "validity_rule": "calendar_year", "starts_on": "2027-03-15", "expires_on": "2027-12-31",
        "m01_record_ref": None,
    }  # fmt: skip
    assert issued["occurred_at"] and issued["licence_type"] == annual.name


def test_every_change_raises_the_version(make_licence):
    licence = make_licence(status="paid")
    assert licence.version == 1
    licence.federation_number = "F-2"
    licence.save(update_fields=["federation_number"])
    licence.refresh_from_db()
    assert licence.version == 2


def test_ca_m06_17_paid_then_active_emits_one_issued_and_a_renewal_emits_renewed(
    make_licence, staff
):
    previous = make_licence(status="active", federation_number="F-1",
                            origin="external", price_kind=None, price_cents=None)  # fmt: skip
    renewal = make_licence(status="paid", renewal_of=previous, starts_on=D(2028, 1, 1),
                           expires_on=D(2028, 12, 31))  # fmt: skip
    first = make_licence(status="paid", person=previous.person, licence_type=renewal.licence_type,
                         validity_rule=ValidityRule.SINGLE_DAY, starts_on=D(2027, 5, 10),
                         expires_on=D(2027, 5, 10))  # fmt: skip
    secretary = staff[R.SECRETARY]
    filing.mark_active(first, "F-3", actor=secretary, today=D(2027, 5, 1))
    filing.mark_filed(renewal, actor=secretary, today=D(2027, 12, 2))
    filing.mark_active(renewal, "F-4", actor=secretary, today=D(2027, 12, 20))
    assert [p["licence"] for p in emitted(events.LICENCE_ISSUED)] == [first.pk]
    (renewed,) = emitted(events.LICENCE_RENEWED)
    assert (renewed["licence"], renewed["version"]) == (renewal.pk, 3)  # creada, tramitada, vigent


def test_ca_m06_07_and_13_notices_once_and_cancelled_event(options, soci, annual, priced, staff):  # noqa: F811
    licence = ask(soci, annual)
    charges.record_payment(licence.charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM)
    event = Event.objects.get(name=events.CHARGE_PAID)
    events.deliver(event.pk)
    events.deliver(event.pk)
    assert mails("avis-llicencia-pagada") == ["secretaria@example.org"]
    cancel(licence, "Es dona de baixa", actor=staff[R.SECRETARY])
    assert mails("avis-devolucio-llicencia") == ["tresor@example.org"]
    (cancelled,) = emitted(events.LICENCE_CANCELLED)
    assert (cancelled["licence"], cancelled["version"]) == (
        licence.pk,
        3,
    )  # demanada, pagada, cancel·lada


def test_ca_m06_23_a_lapsed_licence_notifies_the_treasurer(make_licence, staff):
    licence = make_licence(status="paid", validity_rule=ValidityRule.SINGLE_DAY, price_cents=1500,
                           starts_on=D(2027, 5, 10), expires_on=D(2027, 5, 10))  # fmt: skip
    charge = charges.create_charge(
        licence.person, kind="licence", amount_cents=1500, concept="Llicència", origin="licences",
        by=SYSTEM, department=charges.Department.objects.get(name="General"),
    )  # fmt: skip
    charges.record_payment(charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM)
    Licence.objects.filter(pk=licence.pk).update(charge=charge)
    day.lapse_overdue(D(2027, 5, 11))
    assert mails("avis-devolucio-llicencia") == ["tresor@example.org"]


def test_expired_once_the_day_after(make_licence):
    licence = make_licence(status="active", federation_number="F-1",
                           origin="external", price_kind=None, price_cents=None)  # fmt: skip
    assert licence_events.expire_due(D(2027, 12, 31)) == 0
    assert licence_events.expire_due(D(2028, 1, 1)) == 1
    assert licence_events.expire_due(D(2028, 1, 2)) == 0
    (expired,) = emitted(events.LICENCE_EXPIRED)
    assert (expired["licence"], expired["version"]) == (licence.pk, 2)


def test_an_expiry_emitted_meanwhile_is_skipped(make_licence, monkeypatch):
    licence = make_licence(status="active", federation_number="F-1",
                           origin="external", price_kind=None, price_cents=None)  # fmt: skip
    real = Licence.objects.select_for_update

    def emitted_meanwhile():
        Licence.objects.filter(pk=licence.pk).update(expired_at="2028-01-01T03:25:00Z")
        return real()

    monkeypatch.setattr(Licence.objects, "select_for_update", emitted_meanwhile)
    assert licence_events.expire_due(D(2028, 1, 1)) == 0


def test_no_notice_to_accounts_without_an_email(make_admin, make_licence):  # noqa: F811
    make_admin(R.TREASURER)  # sense correu de notificació
    assert licence_events.notify("licences.refund", "avis-devolucio-llicencia",
                                 {"licence_id": 1, "amount": "1,00 €"}) == 0  # fmt: skip


def test_the_daily_task_calls_the_service(monkeypatch):
    from apps.licences import tasks

    calls = []
    monkeypatch.setattr(licence_events, "expire_due", lambda: calls.append(1))
    tasks.expire_due.func(timestamp=0)
    assert calls == [1]


def test_the_06_registers_its_source_and_it_reads_licences(make_licence):
    from apps.licences.events import read_source
    from apps.members import licence_copy

    assert licence_copy._source is read_source
    active = make_licence(status="active", federation_number="F-1", origin="external",
                          price_kind=None, price_cents=None)  # fmt: skip
    cancelled = make_licence(status="cancelled", cancellation_reason="Prova")
    rows = {r["licence"]: r for r in read_source()}
    assert rows[active.pk]["cancelled_on"] is None and rows[cancelled.pk]["cancelled_on"]
