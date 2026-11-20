"""Llicència d'un dia (T-M06-19; CA-M06-21 i 23; RN-M06-20), amb l'opció activada a la prova."""

import datetime

import pytest
from django.core.exceptions import ValidationError

from apps.core import audit, business_settings, charges
from apps.core.models import AuditEntry, Department, Payment
from apps.licences import day
from apps.licences.models import Licence, LicenceRefundProposal, LicenceType, ValidityRule

D = datetime.date
SYSTEM = audit.system("proves-t-m06-19")
DAY = {"validity_rule": ValidityRule.SINGLE_DAY, "starts_on": D(2027, 5, 10),
       "expires_on": D(2027, 5, 10)}  # fmt: skip


@pytest.fixture
def day_enabled(monkeypatch):
    real = business_settings.get
    monkeypatch.setattr(
        business_settings, "get",
        lambda key, at=None: True if key == "licences.day_enabled" else real(key, at),
    )  # fmt: skip


def single_day_type(**fields):
    return LicenceType(name="Un dia (inventat)", category="amateur",
                       validity_rule=ValidityRule.SINGLE_DAY, **fields)  # fmt: skip


@pytest.mark.django_db
def test_ca_m06_21_no_active_single_day_type_while_disabled():
    with pytest.raises(ValidationError, match="un dia"):
        single_day_type().full_clean()
    single_day_type(active=False).full_clean()  # inactiu, sí


@pytest.mark.django_db
def test_with_the_option_a_single_day_type_is_allowed(day_enabled):
    single_day_type().full_clean()


def paid_charge(person, amount=1500):
    charge = charges.create_charge(
        person, kind="licence", amount_cents=amount, concept="Llicència", origin="licences",
        by=SYSTEM, department=Department.objects.get(name=Department.GENERAL),
    )  # fmt: skip
    charges.record_payment(charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM)
    return charge


@pytest.mark.parametrize("status", ["paid", "filed"])
def test_ca_m06_23_lapsed_once_with_a_refund_proposal(make_licence, status):
    licence = make_licence(status=status, price_cents=1500, **DAY)
    Licence.objects.filter(pk=licence.pk).update(charge=paid_charge(licence.person))
    assert day.lapse_overdue(D(2027, 5, 10)) == 0  # el dia encara no s'ha acabat
    assert day.lapse_overdue(D(2027, 5, 11)) == 1
    licence.refresh_from_db()
    assert licence.status == "lapsed"
    proposal = LicenceRefundProposal.objects.get(licence=licence)
    assert (proposal.status, proposal.amount_cents) == ("proposed", 1500)
    assert day.lapse_overdue(D(2027, 5, 12)) == 0  # una sola vegada
    entry = AuditEntry.objects.get(action=day.ACTION_LAPSED)
    assert (entry.old_value, entry.new_value) == (status, "lapsed")


def test_others_are_not_touched(make_licence, make_person):
    active = make_licence(status="active", person=make_person("Pau", "Roig"), **DAY)
    requested = make_licence(status="requested", person=make_person("Eva", "Mas"), **DAY)
    annual = make_licence(status="paid", expires_on=D(2027, 3, 20))
    assert day.lapse_overdue(D(2028, 1, 1)) == 0
    for licence in (active, requested, annual):
        before = licence.status
        licence.refresh_from_db()
        assert licence.status == before


def test_a_lapsed_licence_without_a_paid_charge_has_no_proposal(make_licence):
    licence = make_licence(status="filed", **DAY)
    assert day.lapse_overdue(D(2027, 5, 11)) == 1
    assert not LicenceRefundProposal.objects.filter(licence=licence).exists()


def test_a_licence_changed_meanwhile_is_skipped(make_licence, monkeypatch):
    licence = make_licence(status="paid", **DAY)
    real = Licence.objects.select_for_update

    def changed_meanwhile():
        Licence.objects.filter(pk=licence.pk).update(status="active")
        return real()

    monkeypatch.setattr(Licence.objects, "select_for_update", changed_meanwhile)
    assert day.lapse_overdue(D(2027, 5, 11)) == 0


def test_the_daily_task_calls_the_service(monkeypatch):
    from apps.licences import tasks

    calls = []
    monkeypatch.setattr(day, "lapse_overdue", lambda: calls.append(1))
    tasks.lapse_overdue.func(timestamp=0)
    assert calls == [1]
