"""Cel·les de la 095 (P-190 i P-193): la migració dona T8 a qui tenia T4 i T10 a qui tenia T1, i
«Cons.» d'A4 a la Secretaria, amb una versió nova de la matriu. Un rol que el propietari havia
canviat a mà no guanya ni perd accés. Només dades inventades."""

import importlib

import pytest
from django.apps import apps as django_apps

from apps.core.models import PermissionMatrixVersion, Role, RolePermission

pytestmark = pytest.mark.django_db
migration = importlib.import_module("apps.payments.migrations.0023_permisos_095")


def cells(code):
    return dict(
        RolePermission.objects.filter(permission_code=code).values_list("role__code", "scope")
    )


def test_the_migration_copies_t4_and_t1_and_gives_a4_read_to_the_secretary():
    RolePermission.objects.filter(permission_code__in=migration.NEW).delete()
    RolePermission.objects.filter(permission_code=migration.A4, role__code="secretary").delete()
    RolePermission.objects.create(  # un canvi a mà: la Junta veu la tresoreria
        role=Role.objects.get(code="board"), permission_code=migration.T1, scope="all"
    )
    migration.load(django_apps, None)
    assert cells(migration.T8) == {"treasurer": "all"}
    assert cells(migration.T10) == {"treasurer": "all", "administrator": "all", "board": "all"}
    assert cells(migration.A4)["secretary"] == "read"
    version = PermissionMatrixVersion.objects.order_by("-number").first()
    assert version.note == migration.NOTE
    added = {"role": "secretary", "permission": migration.A4, "before": None, "after": "read"}
    assert added in version.diff and len(version.diff) == 5


def test_running_it_again_changes_nothing():
    last = PermissionMatrixVersion.objects.order_by("-number").first().number
    migration.load(django_apps, None)
    assert PermissionMatrixVersion.objects.order_by("-number").first().number == last
