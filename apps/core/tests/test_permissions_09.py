"""Permisos del 09 i de l'apartat d'ajuts per cel·la (T-M09-30; CA-M09-21, CA-RP-13). La taula és
la matriu inicial de la 059 per al 09 (planning.md#rols-i-permisos-059-matriu) i, per als ajuts,
M09-ajuts-4, copiades a mà: si el catàleg se n'aparta, la prova falla."""

import pytest

from apps.core.models import Role
from apps.core.permission_catalog import CATALOG
from apps.core.permissions import has_perm, scope_for
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

R = Role.Code
Y, CONS, OWN_A, OWN_G = "all", "read", "own_activities", "own_applications"
ROLES = (R.INSTRUCTOR, R.SECRETARY, R.COURSES_MANAGER, R.EQUIPMENT_MANAGER, R.TREASURER,
         R.HISTORY_DEPARTMENT, R.ADMINISTRATOR, R.PRESIDENT, R.BOARD)  # fmt: skip
_ = None
# Instr., Secr., RCS, RM, Tres., DH, Admin., Pres., Junta («_» = «—»).
MATRIX = {
    "expenses.record": (_, _, OWN_A, _, Y, _, Y, Y, _),  # MG1
    "expenses.pay": (_, _, _, _, Y, _, Y, _, _),  # MG2
    "expenses.allocate": (_, _, _, _, Y, _, Y, _, _),  # MG3
    "expenses.other_income": (_, _, _, _, Y, _, Y, _, _),  # MG4
    "expenses.planned_costs": (_, _, OWN_A, _, Y, _, Y, _, _),  # MG5
    "expenses.margin.view": (_, _, OWN_A, _, Y, _, Y, Y, CONS),  # MG6
    "expenses.margin.close_activity": (_, _, _, _, Y, _, Y, _, _),  # MG7
    "expenses.reports": (_, _, _, _, Y, _, Y, _, CONS),  # MG8
    "expenses.invoices.issue": (_, _, _, _, Y, _, Y, _, _),  # MG9
    "expenses.periods.close": (_, _, _, _, Y, _, Y, _, _),  # MG11
    "expenses.periods.reopen": (_, _, _, _, _, _, Y, _, _),  # MG12, protegit
    "expenses.volunteering": (_, _, _, _, Y, _, Y, _, _),  # MG13
    "expenses.catalogues": (_, _, _, _, Y, _, Y, _, _),  # MG14
    "expenses.documents.open": (_, _, _, _, Y, _, _, _, Y),  # C5, protegit (051)
    "grants.calls.manage": (_, _, _, _, Y, _, Y, _, Y),  # AJ1
    "grants.eligibility": (_, _, _, _, Y, _, Y, _, Y),  # AJ2
    "grants.view": (_, _, _, _, Y, _, Y, _, Y),  # AJ3
    "grants.applications.prepare": (_, _, _, _, Y, _, Y, _, OWN_G),  # AJ4
    "grants.applications.resolve": (_, _, _, _, Y, _, Y, _, OWN_G),  # AJ5
    "grants.income": (_, _, _, _, Y, _, Y, _, _),  # AJ6
    "grants.justification": (_, _, _, _, Y, _, Y, _, CONS),  # AJ7
    "grants.applications.close": (_, _, _, _, Y, _, Y, _, _),  # AJ8
    "grants.applications.undo": (_, _, _, _, _, _, Y, _, _),  # AJ9
    "grants.alert_days": (_, _, _, _, Y, _, Y, _, _),  # AJ10
    "grants.audit.view": (_, _, _, _, CONS, _, Y, _, _),  # AJ11
    "grants.documents.open": (_, _, _, _, Y, _, _, _, Y),  # AJ12, protegit (051)
    "grants.applications.amendments": (_, _, _, _, Y, _, Y, _, OWN_G),  # AJ13
}
CELLS = [(code, role, row[i]) for code, row in MATRIX.items() for i, role in enumerate(ROLES)]


def test_the_table_covers_every_permission_of_the_09():
    assert set(MATRIX) == {code for code in CATALOG if code.split(".")[0] in {"expenses", "grants"}}


@pytest.mark.parametrize(("code", "role", "expected"), CELLS, ids=[f"{c}-{r}" for c, r, _ in CELLS])
def test_cell(make_admin, code, role, expected):  # noqa: F811
    assert scope_for(make_admin(role), code) == expected


@pytest.mark.parametrize("role", [R.COMMUNICATIONS_MANAGER, R.SHOP_MANAGER])
def test_communications_and_shop_have_nothing_in_the_09(make_admin, role):  # noqa: F811
    account = make_admin(role)
    assert not [code for code in MATRIX if scope_for(account, code)]


def test_reopening_and_documents_are_protected():
    for code in ("expenses.periods.reopen", "expenses.documents.open", "grants.documents.open"):
        assert CATALOG[code].protected


def test_the_administrator_never_opens_justification_documents_051(make_admin):  # noqa: F811
    admin = make_admin(R.ADMINISTRATOR)
    assert has_perm(admin, "grants.justification", write=True)  # lliga despeses
    assert not has_perm(admin, "expenses.documents.open")
    assert not has_perm(admin, "grants.documents.open")


def test_the_board_only_reads_margins_and_reports(make_admin):  # noqa: F811
    board = make_admin(R.BOARD)
    assert has_perm(board, "expenses.margin.view")
    assert not has_perm(board, "expenses.margin.view", write=True)
    assert not has_perm(board, "expenses.record")


def test_an_own_applications_cell_lets_no_object_through_without_its_check(make_admin):  # noqa: F811
    # La comprovació per objecte la registra l'apartat d'ajuts (T-M09A); fins llavors, cap.
    assert not has_perm(make_admin(R.BOARD), "grants.applications.prepare", object())


SETTINGS = {
    "settings.section.billing": (_, _, _, _, _, _, CONS, _, _),  # AJ09
    "settings.edit.billing.enabled_charge_kinds": (_, _, _, _, _, _, Y, _, _),  # AJ09-1, VC-34
    "settings.section.margin": (_, _, _, _, CONS, _, CONS, _, _),  # AJ09-M (T-M09-26)
    "settings.edit.margin.low_margin_threshold_cents": (_, _, _, _, Y, _, _, _, _),  # VC-31
    "settings.edit.margin.period_length": (_, _, _, _, Y, _, _, _, _),  # VC-32
    "settings.section.grants": (_, _, _, _, CONS, _, CONS, _, _),  # AJ09-A (T-M09-26)
    "settings.edit.grants.deadline_reminder_days": (_, _, _, _, Y, _, _, _, _),  # VC-36
    "settings.edit.grants.requirement_reminder_days": (_, _, _, _, Y, _, _, _, _),  # VC-37
}
SETTINGS_CELLS = [
    (code, role, row[i]) for code, row in SETTINGS.items() for i, role in enumerate(ROLES)
]


@pytest.mark.parametrize(
    ("code", "role", "expected"), SETTINGS_CELLS, ids=[f"{c}-{r}" for c, r, _ in SETTINGS_CELLS]
)
def test_settings_cell(make_admin, code, role, expected):  # noqa: F811
    assert scope_for(make_admin(role), code) == expected
