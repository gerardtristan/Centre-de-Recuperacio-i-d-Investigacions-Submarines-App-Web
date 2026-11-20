"""Cel·les inicials dels permisos del 06 Llicències (M06-4 i la matriu inicial de la 059;
T-M06-16): LC3 a LC8, LC10, LC11 i el camp C6, amb una sola versió nova de la matriu (060).
Mateix patró que la 0040, amb l'abast de cada cel·la. LC9 arriba amb l'ajust (T-M06-20)."""

from django.db import migrations
from django.db.models import Max

LIST = {"secretary": "all", "courses_manager": "all", "treasurer": "all",
        "administrator": "all", "president": "all"}  # fmt: skip
CELLS = {
    "licences.declare_existing": LIST,
    "licences.list": LIST,
    "licences.file": {"secretary": "all", "administrator": "all", "president": "all"},
    "licences.cancel": {"secretary": "all", "administrator": "all", "president": "all"},
    "licences.refund": {"treasurer": "all"},
    "licences.prices": {
        "treasurer": "all",
        "administrator": "all",
        "president": "all",
        "board": "read",
    },  # fmt: skip
    "licences.participant_status": {
        "instructor": "own_sessions",
        "secretary": "all",
        "courses_manager": "own_activities",
        "administrator": "all",
        "president": "all",
    },  # fmt: skip
    "licences.import_m01": {"administrator": "all"},
    "licences.field.details": LIST,
}
NOTE = "Permisos del 06 Llicències: LC3 a LC8, LC10, LC11 i C6 (T-M06-16)."


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    diff = []
    for code, cells in CELLS.items():
        for role, scope in cells.items():
            _cell, created = RolePermission.objects.get_or_create(
                role=Role.objects.get(code=role), permission_code=code, defaults={"scope": scope}
            )
            if created:
                diff.append({"role": role, "permission": code, "before": None, "after": scope})
    if diff:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    RolePermission = apps.get_model("core", "RolePermission")
    RolePermission.objects.filter(permission_code__in=CELLS).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0059_transfer_reminder_permission")]

    operations = [migrations.RunPython(load, unload)]
