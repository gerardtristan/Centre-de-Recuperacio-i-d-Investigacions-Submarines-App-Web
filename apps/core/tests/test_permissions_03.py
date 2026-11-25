"""Permisos del 03 Material per cel·la (T-M03-18; CA-M03-16, CA-RP-13). La taula és la matriu
inicial de la 059 per al 03 (planning.md#rols-i-permisos-059-matriu), copiada a mà: si el catàleg
se n'aparta, la prova falla."""

import pytest

from apps.core.models import Role
from apps.core.permission_catalog import CATALOG
from apps.core.permissions import has_perm, scope_for
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

R = Role.Code
Y, CONS, OWN_S, OWN_A = "all", "read", "own_sessions", "own_activities"
ROLES = (R.INSTRUCTOR, R.SECRETARY, R.COURSES_MANAGER, R.EQUIPMENT_MANAGER, R.TREASURER,
         R.HISTORY_DEPARTMENT, R.ADMINISTRATOR, R.PRESIDENT, R.BOARD)  # fmt: skip
_ = None
# Instr., Secr., RCS, RM, Tres., DH, Admin., Pres., Junta («_» = «—»).
MATRIX = {
    "equipment.inventory.manage": (_, _, Y, Y, Y, _, Y, Y, _),  # MT3
    "equipment.stock.view": (CONS, _, Y, Y, Y, _, Y, Y, CONS),  # MT4
    "equipment.typical.manage": (_, _, Y, Y, Y, _, Y, Y, _),  # MT5
    "equipment.assignments.manage": (OWN_S, _, Y, Y, Y, _, Y, Y, _),  # MT6
    "equipment.rentals.adhoc": (OWN_S, _, Y, Y, Y, _, Y, Y, _),  # MT6b
    "equipment.participants.view": (OWN_S, _, Y, Y, Y, _, Y, Y, _),  # MT7
    "equipment.centres.manage": (_, _, CONS, Y, Y, _, Y, Y, _),  # MT8
    "equipment.rental_lists.manage": (OWN_S, _, Y, Y, Y, _, Y, Y, _),  # MT9
    "equipment.actual_quantities": (OWN_S, _, Y, Y, Y, _, Y, Y, _),  # MT10
    "equipment.reviews.manage": (_, _, Y, Y, Y, _, Y, Y, _),  # MT11
    "equipment.costs.view": (_, _, OWN_A, Y, Y, _, Y, Y, CONS),  # MT12
    "equipment.field.participant_price": (OWN_S, _, Y, Y, Y, _, Y, Y, _),  # C4
    "equipment.import.run": (_, _, _, Y, _, _, Y, _, _),  # MT13
}
CELLS = [(code, role, row[i]) for code, row in MATRIX.items() for i, role in enumerate(ROLES)]


def test_the_table_covers_every_permission_of_the_03():
    assert set(MATRIX) == {code for code in CATALOG if code.split(".")[0] == "equipment"}


@pytest.mark.parametrize(("code", "role", "expected"), CELLS, ids=[f"{c}-{r}" for c, r, _ in CELLS])
def test_cell(make_admin, code, role, expected):  # noqa: F811
    assert scope_for(make_admin(role), code) == expected


@pytest.mark.parametrize("role", [R.COMMUNICATIONS_MANAGER, R.SHOP_MANAGER])
def test_communications_and_shop_have_nothing_in_the_03(make_admin, role):  # noqa: F811
    account = make_admin(role)
    assert not [code for code in MATRIX if scope_for(account, code)]


def test_the_courses_manager_only_reads_centres_and_rates(make_admin):  # noqa: F811
    manager = make_admin(R.COURSES_MANAGER)
    assert has_perm(manager, "equipment.centres.manage")
    assert not has_perm(manager, "equipment.centres.manage", write=True)
    assert has_perm(make_admin(R.EQUIPMENT_MANAGER), "equipment.centres.manage", write=True)


def test_the_instructor_sees_the_participant_price_but_not_the_margin(make_admin):  # noqa: F811
    instructor = make_admin(R.INSTRUCTOR)
    assert scope_for(instructor, "equipment.field.participant_price") == OWN_S
    assert not has_perm(instructor, "equipment.costs.view")


SETTINGS = {
    "settings.section.equipment": (_, _, _, CONS, CONS, _, CONS, _, _),  # AJ03
    "settings.edit.equipment.review_notice_days": (_, _, _, Y, _, _, _, _, _),  # AJ03-1, VC-29
    "settings.edit.equipment.unreturned_after_days": (_, _, _, Y, _, _, _, _, _),  # AJ03-2, VC-29
    "settings.edit.equipment.usage_rates": (_, _, _, _, Y, _, _, _, _),  # AJ03-3, VC-28
    # AJ03-4, T-M03-11: interruptor del càrrec del lloguer (P-662).
    "settings.edit.equipment.rental_charges_enabled": (_, _, _, _, Y, _, Y, _, _),
}
SETTINGS_CELLS = [
    (code, role, row[i]) for code, row in SETTINGS.items() for i, role in enumerate(ROLES)
]


@pytest.mark.parametrize(
    ("code", "role", "expected"), SETTINGS_CELLS, ids=[f"{c}-{r}" for c, r, _ in SETTINGS_CELLS]
)
def test_settings_cell(make_admin, code, role, expected):  # noqa: F811
    assert scope_for(make_admin(role), code) == expected


def test_t_m03_11_the_treasurer_turns_on_the_rental_charges_switch_with_a_trace(make_admin):  # noqa: F811
    from django.urls import reverse

    from apps.core import business_settings
    from apps.core.tests.test_guest_links import admin_client

    key = "equipment.rental_charges_enabled"
    url = reverse("administration:setting_detail", args=["equipment", key])
    keeper = admin_client(make_admin(R.EQUIPMENT_MANAGER))
    assert keeper.post(url, {"value": "1", "note": "Prova"}).status_code == 404
    assert business_settings.get(key) is False  # apagat d'inici
    treasurer = admin_client(make_admin(R.TREASURER))
    response = treasurer.post(url, {"value": "1", "note": "Prova"})
    assert response.status_code == 302 and business_settings.get(key) is True
