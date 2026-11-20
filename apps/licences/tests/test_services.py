"""`licences.current` i la visibilitat de LC10 (T-M06-13; CA-M06-11, 15 i 27; RN-M06-13 i 22).
Proves de contracte per al 02: forma de la resposta, només lectura i una sola consulta."""

import dataclasses
import datetime

import pytest
from django.db import connection
from django.http import Http404
from django.test.utils import CaptureQueriesContext

from apps.core import permissions
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences.models import Licence, LicenceType, ValidityRule
from apps.licences.services import CurrentLicence, current, participant_status

D = datetime.date
R = Role.Code
S = Licence.Status
YEAR_365 = {"validity_rule": ValidityRule.DAYS_365, "starts_on": D(2026, 3, 15)}


@pytest.fixture
def technical_365(make_licence, annual):
    annual.validity_rule = ValidityRule.DAYS_365
    annual.category = LicenceType.Category.TECHNICAL
    annual.save()
    return make_licence(status=S.ACTIVE, expires_on=D(2027, 3, 14), **YEAR_365)


def test_ca_m06_11_covers_its_last_day_and_not_the_next(technical_365):
    person = technical_365.person
    found = current(person, D(2027, 3, 14))
    assert found == CurrentLicence(
        status="active",
        licence_type="Aficionat anual (inventat)",
        category="technical",
        validity_rule="days_365",
        expires_on=D(2027, 3, 14),
        origin="club",
    )
    assert current(person, D(2027, 3, 15)) is None
    assert current(person, D(2026, 3, 14)) is None


@pytest.mark.parametrize("status", ["requested", "paid", "filed"])
def test_ca_m06_27_in_progress_with_the_category(make_licence, status):
    licence = make_licence(status=status)
    found = current(licence.person, D(2027, 5, 10))
    assert found.status == "in_progress"
    assert found.category == "amateur"


def test_cancelled_and_lapsed_do_not_count(make_licence):
    licence = make_licence(status=S.CANCELLED, cancellation_reason="Duplicada")
    make_licence(
        status=S.LAPSED,
        validity_rule=ValidityRule.SINGLE_DAY,
        starts_on=D(2027, 5, 10),
        expires_on=D(2027, 5, 10),
    )
    assert current(licence.person, D(2027, 5, 10)) is None


def test_an_active_one_wins_over_one_in_progress_and_the_latest_expiry_wins(make_licence):
    make_licence(status=S.REQUESTED, starts_on=D(2027, 1, 1), expires_on=D(2027, 12, 31))
    make_licence(status=S.ACTIVE, starts_on=D(2027, 1, 1), expires_on=D(2027, 6, 30))
    latest = make_licence(
        status=S.ACTIVE, origin="external", price_kind=None, price_cents=None,
        starts_on=D(2027, 2, 1), expires_on=D(2027, 9, 30),
    )  # fmt: skip
    found = current(latest.person, D(2027, 5, 10))
    assert (found.status, found.expires_on, found.origin) == ("active", D(2027, 9, 30), "external")


def test_contract_is_read_only_one_query_and_never_the_model(technical_365):
    with CaptureQueriesContext(connection) as queries:
        found = current(technical_365.person, D(2026, 6, 1))
    assert len(queries) == 1
    assert queries[0]["sql"].lstrip().upper().startswith("SELECT")
    assert dataclasses.is_dataclass(found)
    assert {f.name for f in dataclasses.fields(found)} == {
        "status", "licence_type", "category", "validity_rule", "expires_on", "origin",
    }  # fmt: skip
    with pytest.raises(dataclasses.FrozenInstanceError):
        found.status = "in_progress"


# --- Visibilitat (LC10, RN-M06-22) ----------------------------------------------------------


@pytest.fixture
def scope_checks(monkeypatch):
    """El 02 registrarà les comprovacions d'abast; aquí, una sessió o activitat «meva»."""
    for scope in ("own_sessions", "own_activities"):
        monkeypatch.setitem(permissions._SCOPE_CHECKS, scope, lambda account, obj: obj == "meva")


@pytest.mark.parametrize(
    ("role", "active", "in_progress", "none"),
    [
        (R.INSTRUCTOR, "valid", "no", "no"),  # només «vigent sí o no»
        (R.COURSES_MANAGER, "valid", "in_progress", "no"),
        (R.SECRETARY, "valid", "in_progress", "no"),
    ],
)
def test_ca_m06_15_and_27_what_each_role_sees(
    make_admin,  # noqa: F811
    make_licence,
    make_person,
    scope_checks,
    role,
    active,
    in_progress,
    none,
):
    account = make_admin(role)
    valid = make_licence(status=S.ACTIVE)
    pending = make_licence(status=S.PAID, person=make_person("Pau", "Roig"))
    on = D(2027, 5, 10)
    assert participant_status(account, valid.person, on, "meva") == active
    assert participant_status(account, pending.person, on, "meva") == in_progress
    assert participant_status(account, make_person("Eva", "Mas"), on, "meva") == none


@pytest.mark.parametrize("role", [R.INSTRUCTOR, R.COURSES_MANAGER])
def test_outside_their_sessions_or_activities_is_not_found(
    make_admin,  # noqa: F811
    make_licence,
    scope_checks,
    role,
):
    account, licence = make_admin(role), make_licence(status=S.ACTIVE)
    with pytest.raises(Http404):
        participant_status(account, licence.person, D(2027, 5, 10), "d-un-altre")
    with pytest.raises(Http404):  # sense context no hi ha res a comprovar
        participant_status(account, licence.person, D(2027, 5, 10))


def test_without_the_02_scope_check_it_is_denied(make_admin, make_licence):  # noqa: F811
    with pytest.raises(Http404):
        participant_status(make_admin(R.INSTRUCTOR), make_licence().person, D(2027, 5, 10), "meva")


@pytest.mark.parametrize("role", [R.TREASURER, R.EQUIPMENT_MANAGER, R.BOARD, None])
def test_roles_without_lc10_get_not_found(make_admin, make_licence, role):  # noqa: F811
    account = make_admin(*([role] if role else []))
    with pytest.raises(Http404):
        participant_status(account, make_licence().person, D(2027, 5, 10))


def test_the_answer_never_carries_dates_numbers_or_category(make_admin, make_licence):  # noqa: F811
    licence = make_licence(status=S.ACTIVE, federation_number="F-123")
    answer = participant_status(make_admin(R.SECRETARY), licence.person, D(2027, 5, 10))
    assert answer == "valid" and isinstance(answer, str)
