"""Tramitació a la federació (T-M06-10; P-M06-E; RN-M06-02 i 11; CA-M06-10; LC5)."""

import codecs
import datetime
import hashlib

import pytest
from django.http import Http404

from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import filing
from apps.licences.filing import FederationNumberRequired, WrongStatus, mark_active, mark_filed
from apps.licences.models import Licence, ValidityRule

D = datetime.date
R = Role.Code
TODAY = D(2027, 4, 2)


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    return make_admin(R.SECRETARY)


@pytest.fixture
def paid(make_licence):
    return make_licence(status="paid")  # demanada el 15/3/2027


def test_filing_moves_an_annual_start_to_the_filing_day(paid, secretary):
    filed = mark_filed(paid, actor=secretary, today=TODAY)
    assert (filed.status, filed.filed_by) == ("filed", secretary) and filed.filed_at
    assert (filed.starts_on, filed.expires_on) == (TODAY, D(2027, 12, 31))
    entry = AuditEntry.objects.get(action=filing.ACTION_FILED)
    assert (entry.old_value, entry.new_value) == ("paid", "filed")


def test_a_365_day_licence_counts_from_the_filing_day(make_licence, annual, secretary):
    licence = make_licence(status="paid", validity_rule=ValidityRule.DAYS_365,
                           expires_on=D(2028, 3, 14))  # fmt: skip
    filed = mark_filed(licence, actor=secretary, today=TODAY)
    assert (filed.starts_on, filed.expires_on) == (TODAY, D(2028, 4, 1))


@pytest.mark.parametrize(
    ("fields", "start", "end"),
    [
        ({"starts_on": D(2028, 1, 1), "expires_on": D(2028, 12, 31)},
         D(2028, 1, 1), D(2028, 12, 31)),
        ({"validity_rule": ValidityRule.SINGLE_DAY, "starts_on": D(2027, 3, 15),
          "expires_on": D(2027, 3, 15)}, D(2027, 3, 15), D(2027, 3, 15)),
    ],
)  # fmt: skip
def test_next_year_and_single_day_keep_their_dates(make_licence, secretary, fields, start, end):
    filed = mark_filed(make_licence(status="paid", **fields), actor=secretary, today=TODAY)
    assert (filed.starts_on, filed.expires_on) == (start, end)


def test_activate_after_filing_with_the_federation_number(paid, secretary):
    mark_filed(paid, actor=secretary, today=D(2027, 3, 20))
    active = mark_active(paid, " F-998 ", actor=secretary, today=TODAY)
    assert (active.status, active.federation_number, active.activated_by) == (
        "active", "F-998", secretary,
    )  # fmt: skip
    assert active.starts_on == D(2027, 3, 20)  # la tramitació ja l'havia fixat


def test_activate_straight_from_paid(paid, secretary):
    active = mark_active(paid, "F-1", actor=secretary, today=TODAY)
    assert (active.status, active.starts_on) == ("active", TODAY)


@pytest.mark.parametrize("number", ["", "  ", None, "X" * 31])
def test_a_club_licence_needs_its_number(paid, secretary, number):
    with pytest.raises(FederationNumberRequired):
        mark_active(paid, number, actor=secretary, today=TODAY)


@pytest.mark.parametrize("status", ["requested", "active", "cancelled"])
def test_only_from_the_right_status(make_licence, secretary, status):
    licence = make_licence(status=status, cancellation_reason="Motiu")
    with pytest.raises(WrongStatus):
        mark_filed(licence, actor=secretary, today=TODAY)
    if status != "active":
        with pytest.raises(WrongStatus):
            mark_active(licence, "F-1", actor=secretary, today=TODAY)


@pytest.mark.parametrize("role", [R.COURSES_MANAGER, R.TREASURER, R.BOARD, None])
def test_only_lc5(paid, make_admin, role):  # noqa: F811
    actor = make_admin(*([role] if role else []))
    for call in (
        lambda: mark_filed(paid, actor=actor, today=TODAY),
        lambda: mark_active(paid, "F-1", actor=actor, today=TODAY),
        lambda: filing.export(actor),
    ):
        with pytest.raises(Http404):
            call()


def rows(content):
    text = content.removeprefix(codecs.BOM_UTF8).decode("utf-8")
    return [line.split(";") for line in text.strip().splitlines()]


def test_ca_m06_10_export_of_paid_licences(make_licence, make_person, secretary):
    make_licence(status="paid", person=make_person("Anna", "Vila", birth_date=D(1990, 5, 4)))
    make_licence(status="paid", person=make_person("=Pere", "Roca"))
    make_licence(status="requested", person=make_person("Eva", "Mas"))
    name, content = filing.export(secretary)
    assert name.startswith("llicencies-federacio-") and name.endswith(".csv")
    assert rows(content) == [
        ["Cognoms", "Nom", "Data de naixement", "Tipus de llicència", "Categoria", "Inici"],
        ["Roca", "'=Pere", "", "Aficionat anual (inventat)", "Aficionat", "15/03/2027"],
        ["Vila", "Anna", "04/05/1990", "Aficionat anual (inventat)", "Aficionat", "15/03/2027"],
    ]
    entry = AuditEntry.objects.get(action=filing.ACTION_EXPORTED)
    assert entry.details["count"] == 2
    assert entry.details["sha256"] == hashlib.sha256(content).hexdigest()
    assert not Licence.objects.exclude(status__in=["paid", "requested"]).exists()  # no desa res


def test_the_president_exports_without_the_birth_date(make_licence, make_admin):  # noqa: F811
    make_licence(status="paid")
    _name, content = filing.export(make_admin(R.PRESIDENT))
    assert rows(content)[0] == ["Cognoms", "Nom", "Tipus de llicència", "Categoria", "Inici"]
    assert AuditEntry.objects.get(action=filing.ACTION_EXPORTED).details["birth_date"] is False


def test_export_of_a_given_selection(make_licence, make_person, secretary):
    chosen = make_licence(status="filed", person=make_person("Anna", "Vila"))
    make_licence(status="paid", person=make_person("Pere", "Roca"))
    _name, content = filing.export(secretary, Licence.objects.filter(pk=chosen.pk))
    assert [row[0] for row in rows(content)[1:]] == ["Vila"]
