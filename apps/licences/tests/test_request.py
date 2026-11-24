"""Demanar una llicència (T-M06-04; P-M06-B; CA-M06-03, 21, 22, 25 i 30; RN-M06-04, 10 i 21)."""

import datetime

import pytest
from django.db import IntegrityError
from django.http import Http404

from apps.accounts.models import Account
from apps.core.models import AuditEntry, Charge
from apps.licences import prices, reminders, services
from apps.licences.models import Licence, LicenceType, ValidityRule
from apps.licences.services import (
    AlreadyInProgress,
    DateInPast,
    DayLicencesDisabled,
    NextYearNotOpen,
    NonMembersDisabled,
    NotAvailable,
    request,
)

D = datetime.date
TODAY = D(2027, 3, 15)
PASSWORD = "contrasenya-de-proves-1954"  # noqa: S105 (dada inventada de proves)


@pytest.fixture
def options(monkeypatch):
    """Els ajustos del 06 (encara sense permís per editar-los, T-M06-20) i «és soci»."""
    values = {services.NON_MEMBERS_ENABLED: False, services.DAY_ENABLED: False,
              services.NEXT_YEAR_OPENS_ON: "12-01", "member": True}  # fmt: skip
    real_get = services.business_settings.get
    monkeypatch.setattr(
        services.business_settings, "get", lambda key, at=None: values.get(key, real_get(key, at))
    )
    calls = []

    def is_member(person, on=None):
        calls.append(on)
        return values["member"]

    monkeypatch.setattr(services, "is_member", is_member)
    values["is_member_calls"] = calls
    return values


@pytest.fixture
def soci(make_person):
    person = make_person("Marta", "Soler")
    account = Account.objects.create_personal(person, "marta@example.org", PASSWORD)
    return account


@pytest.fixture
def priced(annual, price_setter):
    def add(licence_type=annual, cost=9000, start=None, end=None):
        return prices.add_price(
            licence_type, federation_cost_cents=cost, non_member_surcharge_cents=2000,
            valid_from=start or D(2027, 1, 1), valid_to=end, note="Tarifa inventada",
            actor=price_setter,
        )  # fmt: skip

    add()
    return add


def ask(account, licence_type, starts_on=None, today=TODAY):
    return request(account.person, licence_type, starts_on, actor=account, today=today)


def test_a_member_requests_an_annual_licence_with_its_charge(options, soci, annual, priced):
    licence = ask(soci, annual)
    assert (licence.status, licence.origin, licence.price_kind) == ("requested", "club", "member")
    assert (licence.starts_on, licence.expires_on) == (TODAY, D(2027, 12, 31))
    assert licence.price_cents == 9000
    charge = licence.charge
    assert (charge.kind, charge.status, charge.amount_cents, charge.origin) == (
        Charge.Kind.LICENCE, Charge.Status.PENDING, 9000, "licences",
    )  # fmt: skip
    assert (charge.department.name, charge.cost_centre.name) == ("General", "Llicències")
    assert options["is_member_calls"] == [TODAY]
    entry = AuditEntry.objects.get(action=services.ACTION_REQUESTED)
    assert entry.new_value["price_cents"] == 9000


def test_ca_m06_30_a_non_member_pays_the_surcharge_only_if_enabled(options, soci, annual, priced):
    options["member"] = False
    with pytest.raises(NonMembersDisabled):
        ask(soci, annual)
    assert not Licence.objects.exists() and not Charge.objects.exists()
    options[services.NON_MEMBERS_ENABLED] = True
    licence = ask(soci, annual)
    assert (licence.price_kind, licence.price_cents, licence.charge.amount_cents) == (
        "non_member", 11000, 11000,
    )  # fmt: skip


def test_one_annual_licence_in_progress_per_type(options, soci, annual, priced):
    ask(soci, annual)
    with pytest.raises(AlreadyInProgress):
        ask(soci, annual)
    assert Licence.objects.count() == Charge.objects.count() == 1


def test_other_integrity_errors_are_not_hidden(options, soci, annual, priced, monkeypatch):
    def broken(**fields):
        raise IntegrityError("una altra restricció")

    monkeypatch.setattr(Licence.objects, "create", broken)
    with pytest.raises(IntegrityError, match="una altra"):
        ask(soci, annual)


def test_only_the_person_themself_can_request_it(options, soci, annual, priced, admin_account):
    with pytest.raises(Http404):
        request(soci.person, annual, actor=admin_account, today=TODAY)
    with pytest.raises(Http404):
        request(soci.person, annual, actor=None, today=TODAY)


def test_ca_m06_25_next_year(options, soci, annual, priced, make_licence):
    current = make_licence(person=soci.person, status="active", starts_on=D(2027, 1, 10))
    priced(cost=9500, start=D(2028, 1, 1))
    next_year = D(2028, 1, 1)
    with pytest.raises(NextYearNotOpen):
        ask(soci, annual, next_year, today=D(2027, 11, 30))
    licence = ask(soci, annual, next_year, today=D(2027, 12, 1))
    assert (licence.starts_on, licence.expires_on) == (next_year, D(2028, 12, 31))
    assert (licence.price_kind, licence.price_cents) == ("member", 9500)
    assert licence.renewal_of == current
    assert options["is_member_calls"][-1] == D(2027, 12, 1)  # soci el dia que la demana


def test_p442_a_new_type_renews_the_licence_of_any_type_that_expires_latest(
    options, soci, annual, priced, make_licence
):
    """P-442 (105, opció B): passar d'aficionat a tècnic també renova l'anterior, i els avisos
    de l'anterior s'aturen."""
    current = make_licence(person=soci.person, status="active", starts_on=D(2027, 1, 10))
    make_licence(person=soci.person, status="active", starts_on=D(2026, 1, 1),
                 expires_on=D(2026, 12, 31))  # caducada: no es renova  # fmt: skip
    technical = LicenceType.objects.create(
        name="Tècnic anual (inventat)",
        category=LicenceType.Category.TECHNICAL,
        validity_rule=ValidityRule.CALENDAR_YEAR,
    )
    priced(technical, start=D(2028, 1, 1))
    assert reminders.due(D(2027, 12, 1))[30] == [current]  # 30 dies abans del venciment
    licence = ask(soci, technical, D(2028, 1, 1), today=D(2027, 12, 1))
    assert licence.renewal_of == current
    assert reminders.due(D(2027, 12, 1))[30] == []  # els avisos de l'anterior s'aturen


def test_the_opening_day_is_the_setting(options, soci, annual, priced):
    options[services.NEXT_YEAR_OPENS_ON] = "10-15"
    licence = ask(soci, annual, D(2028, 1, 1), today=D(2027, 10, 15))
    assert licence.starts_on == D(2028, 1, 1)


@pytest.mark.parametrize(
    ("starts_on", "error"),
    [(D(2027, 3, 14), DateInPast), (D(2027, 6, 1), NotAvailable), (D(2029, 1, 1), NotAvailable)],
)
def test_an_annual_licence_starts_today_or_next_year(
    options, soci, annual, priced, starts_on, error
):
    with pytest.raises(error):
        ask(soci, annual, starts_on)


def test_a_365_day_licence_has_no_next_year_request(options, soci, annual, priced):
    annual.validity_rule = ValidityRule.DAYS_365
    annual.save()
    with pytest.raises(NotAvailable):
        ask(soci, annual, D(2028, 1, 1), today=D(2027, 12, 1))
    assert ask(soci, annual).expires_on == D(2028, 3, 14)


def test_inactive_type_or_no_price_is_not_available(options, soci, annual):
    with pytest.raises(NotAvailable):  # cap preu
        ask(soci, annual)
    annual.active = False
    annual.save()
    with pytest.raises(NotAvailable):
        ask(soci, annual)


@pytest.fixture
def single_day(priced):
    day = LicenceType.objects.create(
        name="Un dia (inventat)", category="amateur", validity_rule=ValidityRule.SINGLE_DAY
    )
    priced(licence_type=day, cost=1500)
    return day


def test_ca_m06_21_no_single_day_licence_while_disabled(options, soci, single_day):
    with pytest.raises(DayLicencesDisabled):
        ask(soci, single_day, D(2027, 5, 10))


def test_p442_a_single_day_licence_renews_nothing(options, soci, single_day, annual, make_licence):
    """Les d'un dia no s'avisen: ni renoven la vigent (que deixaria de rebre els avisos) ni es
    renoven."""
    options[services.DAY_ENABLED] = True
    current = make_licence(person=soci.person, status="active", starts_on=D(2027, 1, 10))
    day = ask(soci, single_day, D(2027, 12, 31))
    assert day.renewal_of is None
    Licence.objects.filter(pk=current.pk).update(status="cancelled", cancellation_reason="Prova")
    Licence.objects.filter(pk=day.pk).update(status=Licence.Status.ACTIVE)
    assert ask(soci, annual).renewal_of is None


def test_ca_m06_22_single_day_licences_per_date(options, soci, single_day, annual, priced):
    options[services.DAY_ENABLED] = True
    first = ask(soci, single_day, D(2027, 5, 10))
    assert (first.starts_on, first.expires_on, first.price_cents) == (D(2027, 5, 10),) * 2 + (1500,)
    assert ask(soci, single_day, D(2027, 5, 17))
    with pytest.raises(AlreadyInProgress):
        ask(soci, single_day, D(2027, 5, 10))
    with pytest.raises(DateInPast):  # L-M06-07
        ask(soci, single_day, D(2027, 3, 14))
    with pytest.raises(DateInPast):
        ask(soci, single_day)
    ask(soci, annual)
    with pytest.raises(AlreadyInProgress):
        ask(soci, annual)


def test_errors_have_a_message():
    assert str(NextYearNotOpen()) == "Encara no es pot demanar la llicència de l'any vinent."


@pytest.mark.django_db
def test_the_settings_exist_with_their_initial_values():
    from apps.core import business_settings

    assert business_settings.get(services.NON_MEMBERS_ENABLED) is False
    assert business_settings.get(services.DAY_ENABLED) is False
    assert business_settings.get(services.NEXT_YEAR_OPENS_ON) == "12-01"
