"""Nucli del 02 Activitats (T-M02-34, T-M02-35 i T-M02-28): el text «Soc major d'edat» a la
llista de M12, els esdeveniments de cancel·lació aprovats i els permisos de l'apartat d'ajustos
del 02 per cel·la. Només dades inventades."""

import pytest

from apps.core import consents, events
from apps.core.models import Role
from apps.core.permission_catalog import CATALOG
from apps.core.permissions import has_perm, scope_for
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db
R = Role.Code


def test_the_adult_declaration_text_can_be_published_from_m12():
    assert "adult_declaration" in consents.KINDS


def test_no_migration_publishes_the_adult_declaration():
    """P-458: a producció cap versió fins que la junta la validi (el formulari rebutja)."""
    assert consents.current_text("adult_declaration") is None


@pytest.mark.parametrize("name", ["enrolment.cancelled", "activity.cancelled"])
def test_the_cancellation_events_of_the_02_are_approved(name, monkeypatch):
    # RN-M02-36 (060): el 02 els emet i qualsevol mòdul s'hi pot subscriure (03, 09).
    monkeypatch.setattr(events, "_subscribers", {})
    events.subscribe(name, lambda event: None)
    assert events.emit(name, {"enrolment": 1}).name == name


SECTION = "settings.section.activities"
EDIT = "settings.edit.activities."
# Rol: (apartat, VC-21, VC-22, VC-24). «None» = sense permís.
CELLS = {
    R.COURSES_MANAGER: ("read", None, "all", "all"),
    R.TREASURER: ("read", "all", None, None),
    R.ADMINISTRATOR: ("read", None, None, None),
    R.SECRETARY: ("read", None, None, None),  # VC-57 (T-M02-48)
    R.INSTRUCTOR: (None, None, None, None),
    R.PRESIDENT: ("read", None, None, None),  # VC-55 (T-M02-48)
    R.BOARD: (None, None, None, None),
}
CODES = (
    SECTION,
    EDIT + "default_payment_window_hours",
    EDIT + "offer_accept_hours",
    EDIT + "default_requirements_mode",
)


@pytest.mark.parametrize(("role", "expected"), CELLS.items())
def test_t_m02_28_initial_cells_of_the_activities_settings(make_admin, role, expected):  # noqa: F811
    account = make_admin(role)
    for code, scope in zip(CODES, expected, strict=True):
        assert scope_for(account, code) == scope, (role, code)
        assert has_perm(account, code, write=True) is (scope == "all"), (role, code)


# T-M02-48 (addenda de la 104): AC24, AC25 i AC26. Rol: (AC24, AC25, AC26).
FILING_CELLS = {
    R.SECRETARY: ("all", "all", "all"),
    R.BOARD: ("read", None, None),
    R.ADMINISTRATOR: (None, None, "all"),
    R.PRESIDENT: (None, None, "all"),
    R.INSTRUCTOR: (None, None, None),
    R.COURSES_MANAGER: (None, None, None),
    R.TREASURER: (None, None, None),
}
FILING_CODES = (
    "activities.card_photos.view",
    "activities.card_photos.manage",
    "activities.filings.manage",
)


@pytest.mark.parametrize(("role", "expected"), FILING_CELLS.items())
def test_t_m02_48_initial_cells_of_ac24_ac25_and_ac26(make_admin, role, expected):  # noqa: F811
    account = make_admin(role)
    for code, scope in zip(FILING_CODES, expected, strict=True):
        assert scope_for(account, code) == scope, (role, code)


VC_55_59 = {
    "homologation_target_agency": {R.COURSES_MANAGER, R.TREASURER, R.ADMINISTRATOR, R.PRESIDENT},
    "card_photos_enabled": {R.ADMINISTRATOR},
    "card_photo_retention_months": {R.SECRETARY},
    "homologation_fee_cents": {R.TREASURER},
    "course_filing_fee_cents": {R.TREASURER},
    "filing_fees_enabled": {R.TREASURER},
}


@pytest.mark.parametrize(("key", "editors"), VC_55_59.items())
def test_t_m02_48_who_edits_vc_55_to_59(make_admin, key, editors):  # noqa: F811
    for role in (R.COURSES_MANAGER, R.SECRETARY, R.TREASURER, R.ADMINISTRATOR, R.PRESIDENT,
                 R.INSTRUCTOR, R.BOARD):  # fmt: skip
        account = make_admin(role)
        assert has_perm(account, EDIT + key, write=True) is (role in editors), (role, key)


@pytest.mark.parametrize("role", [R.COURSES_MANAGER, R.TREASURER, R.ADMINISTRATOR, R.SECRETARY,
                                  R.INSTRUCTOR, R.PRESIDENT, R.BOARD])  # fmt: skip
def test_t_m02_30_only_the_courses_manager_edits_vc_46(make_admin, role):  # noqa: F811
    from apps.core import business_settings
    from apps.core.models import Setting

    account = make_admin(role)
    setting = Setting.objects.get(key="activities.instructor_requirements_mode")
    code = EDIT + "instructor_requirements_mode"
    assert has_perm(account, code, write=True) is (role == R.COURSES_MANAGER)
    assert business_settings.can_edit(account, setting) is (role == R.COURSES_MANAGER)


@pytest.mark.parametrize("key", ["included_licence_expense_category", "homologation_department"])
def test_t_m02_50_only_the_treasurer_edits_vc_60_and_61(make_admin, key):  # noqa: F811
    for role in (R.COURSES_MANAGER, R.SECRETARY, R.TREASURER, R.ADMINISTRATOR, R.PRESIDENT):
        account = make_admin(role)
        assert has_perm(account, EDIT + key, write=True) is (role == R.TREASURER), (role, key)


def test_t_m02_50_ac28_needs_ac27(make_admin):  # noqa: F811
    secretary = make_admin(R.SECRETARY)
    assert has_perm(secretary, "activities.first_licence.view")
    assert not has_perm(secretary, "activities.first_licence.manage", write=True)
    assert CATALOG["activities.first_licence.manage"].requires == ("activities.first_licence.view",)
