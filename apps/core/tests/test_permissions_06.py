"""Permisos del 06 Llicències per cel·la (T-M06-16; CA-M06-16, CA-M06-33; CA-RP-13). La taula
és la matriu inicial de la 059 per al 06 (planning.md#rols-i-permisos-059-matriu), copiada a
mà: si el catàleg se n'aparta, la prova falla."""

import pytest

from apps.core.models import Role
from apps.core.permissions import has_perm, scope_for
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

R = Role.Code
Y, CONS, OWN_S, OWN_A = "all", "read", "own_sessions", "own_activities"
ROLES = (R.INSTRUCTOR, R.SECRETARY, R.COURSES_MANAGER, R.EQUIPMENT_MANAGER, R.TREASURER,
         R.HISTORY_DEPARTMENT, R.ADMINISTRATOR, R.PRESIDENT, R.BOARD)  # fmt: skip
# Instr., Secr., RCS, RM, Tres., DH, Admin., Pres., Junta («None» = «—»).
MATRIX = {
    "licences.declare_existing": (None, Y, Y, None, Y, None, Y, Y, None),  # LC3
    "licences.list": (None, Y, Y, None, Y, None, Y, Y, None),  # LC4
    "licences.file": (None, Y, None, None, None, None, Y, Y, None),  # LC5
    "licences.cancel": (None, Y, None, None, None, None, Y, Y, None),  # LC6
    "licences.refund": (None, None, None, None, Y, None, None, None, None),  # LC7
    "licences.prices": (None, None, None, None, Y, None, Y, Y, CONS),  # LC8
    "licences.participant_status": (OWN_S, Y, OWN_A, None, None, None, Y, Y, None),  # LC10
    "licences.import_m01": (None, None, None, None, None, None, Y, None, None),  # LC11
    "licences.field.details": (None, Y, Y, None, Y, None, Y, Y, None),  # C6
}
CELLS = [(code, role, row[i]) for code, row in MATRIX.items() for i, role in enumerate(ROLES)]


@pytest.mark.parametrize(("code", "role", "expected"), CELLS, ids=[f"{c}-{r}" for c, r, _ in CELLS])
def test_cell(make_admin, code, role, expected):  # noqa: F811
    assert scope_for(make_admin(role), code) == expected


@pytest.mark.parametrize("role", [R.COMMUNICATIONS_MANAGER, R.SHOP_MANAGER])
def test_communications_and_shop_have_nothing_in_the_06(make_admin, role):  # noqa: F811
    account = make_admin(role)
    assert not [code for code in MATRIX if scope_for(account, code)]


def test_courses_manager_sees_the_list_but_not_the_birth_date_ca_m06_33(make_admin):  # noqa: F811
    account = make_admin(R.COURSES_MANAGER)
    assert has_perm(account, "licences.list")
    assert has_perm(account, "licences.field.details")
    assert not has_perm(account, "members.field.birth_date")
    assert not has_perm(account, "licences.file")
    assert not has_perm(account, "licences.cancel")


def test_the_board_only_reads_prices(make_admin):  # noqa: F811
    board = make_admin(R.BOARD)
    assert has_perm(board, "licences.prices")
    assert not has_perm(board, "licences.prices", write=True)
