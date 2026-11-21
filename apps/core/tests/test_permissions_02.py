"""Permisos del 02 Activitats per cel·la (T-M02-33 i T-M02-38; CA-RP-13). La taula és la matriu
inicial de la 059 per al 02 (planning.md#rols-i-permisos-059-matriu) i la de l'addenda de llocs
(planning.md#M02-addenda-llocs) i de la 104 (planning.md#M02-addenda-104), copiades a mà: si el catàleg se n'aparta, la prova falla."""

import pytest

from apps.core.models import Role
from apps.core.permission_catalog import CATALOG
from apps.core.permissions import has_perm, scope_for
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

R = Role.Code
Y, CONS, OWN_S, OWN_A = "all", "read", "own_sessions", "own_activities"
ROLES = (R.INSTRUCTOR, R.SECRETARY, R.COURSES_MANAGER, R.EQUIPMENT_MANAGER, R.TREASURER,
         R.HISTORY_DEPARTMENT, R.ADMINISTRATOR, R.PRESIDENT, R.BOARD)  # fmt: skip
# Instr., Secr., RCS, RM, Tres., DH, Admin., Pres., Junta («None» = «—»).
MATRIX = {
    "activities.enrol_in_person": (None, None, Y, None, Y, None, Y, Y, None),  # AC5
    "activities.catalogue.manage": (None, None, Y, None, Y, None, Y, Y, None),  # AC6
    "activities.manage": (None, None, Y, None, Y, None, Y, Y, None),  # AC7
    "activities.participants.view": (OWN_S, None, Y, CONS, Y, None, Y, Y, None),  # AC8
    "activities.attendance.record": (OWN_S, None, Y, None, None, None, Y, Y, None),  # AC9
    "activities.assessment.record": (OWN_S, None, None, None, None, None, None, None, None),
    "activities.reinforcement.propose": (OWN_S, None, None, None, None, None, None, None, None),
    "activities.reinforcement.decide": (None, None, Y, None, None, None, Y, Y, None),  # AC11
    "activities.outcome.record": (OWN_S, None, None, None, None, None, None, None, None),  # AC12
    "activities.certificate.issue": (None, None, Y, None, None, None, Y, Y, None),  # AC13
    "activities.environment.manage": (None, None, Y, None, None, None, Y, Y, CONS),  # AC14
    "activities.message.send": (None, None, Y, None, Y, None, Y, Y, None),  # AC15
    "activities.waitlist.manage": (None, None, Y, None, Y, None, Y, Y, None),  # AC16
    "activities.refund.propose": (None, None, Y, None, Y, None, Y, Y, None),  # AC17
    "activities.refund.execute": (None, None, None, None, Y, None, None, None, None),  # AC18
    "activities.income.view": (None, None, CONS, None, Y, None, Y, None, None),  # AC19
    "activities.reports.view": (OWN_S, None, Y, CONS, Y, None, Y, Y, CONS),  # AC20
    "activities.field.student_for_instructor": (OWN_S, *(None,) * 8),  # C3 (protegit)
    "activities.places.view": (None, None, Y, Y, Y, None, Y, Y, None),  # AC21
    "activities.places.manage": (None, None, Y, None, Y, None, Y, Y, None),  # AC22
    "activities.material_cost.edit": (None, None, OWN_A, None, Y, None, Y, None, None),  # AC23
    "activities.field.material_cost": (None, None, OWN_A, Y, Y, None, Y, Y, CONS),  # C7
    # Addenda de la 104 (T-M02-48).
    "activities.card_photos.view": (None, Y, None, None, None, None, None, None, CONS),  # AC24
    "activities.card_photos.manage": (None, Y, None, None, None, None, None, None, None),  # AC25
    "activities.filings.manage": (None, Y, None, None, None, None, Y, Y, None),  # AC26
}
CELLS = [(code, role, row[i]) for code, row in MATRIX.items() for i, role in enumerate(ROLES)]


def test_every_02_permission_is_in_the_table():
    assert {code for code in CATALOG if code.startswith("activities.")} == set(MATRIX)


@pytest.mark.parametrize(("code", "role", "expected"), CELLS, ids=[f"{c}-{r}" for c, r, _ in CELLS])
def test_cell(make_admin, code, role, expected):  # noqa: F811
    assert scope_for(make_admin(role), code) == expected


@pytest.mark.parametrize("role", [R.COMMUNICATIONS_MANAGER, R.SHOP_MANAGER])
def test_communications_and_shop_have_nothing_in_the_02(make_admin, role):  # noqa: F811
    account = make_admin(role)
    assert not [code for code in MATRIX if scope_for(account, code)]


def test_c3_is_protected_and_places_manage_needs_places_view():
    assert CATALOG["activities.field.student_for_instructor"].protected
    assert CATALOG["activities.places.manage"].requires == ("activities.places.view",)  # RN-RP-03


def test_read_only_cells_do_not_write(make_admin):  # noqa: F811
    board, equipment = make_admin(R.BOARD), make_admin(R.EQUIPMENT_MANAGER)
    assert has_perm(board, "activities.reports.view")
    assert not has_perm(board, "activities.reports.view", write=True)
    assert has_perm(equipment, "activities.places.view")
    assert not has_perm(equipment, "activities.places.manage")  # RN-M02-46
