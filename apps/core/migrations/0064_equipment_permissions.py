"""Cel·les inicials dels permisos del 03 Material (M03-4 i la matriu inicial de la 059;
T-M03-18): MT3 a MT13 (amb MT6b) i el camp C4, amb una sola versió nova de la matriu (060).
Mateix patró que la 0060 i la 0062. MT1 i MT2 són accions pròpies, fora de la matriu."""

from django.db import migrations
from django.db.models import Max

STAFF = {
    "courses_manager": "all",
    "equipment_manager": "all",
    "treasurer": "all",
    "administrator": "all",
    "president": "all",
}
SESSIONS = {"instructor": "own_sessions", **STAFF}
CELLS = {
    "equipment.inventory.manage": STAFF,
    "equipment.stock.view": {"instructor": "read", **STAFF, "board": "read"},
    "equipment.typical.manage": STAFF,
    "equipment.assignments.manage": SESSIONS,
    "equipment.rentals.adhoc": SESSIONS,
    "equipment.participants.view": SESSIONS,
    "equipment.centres.manage": {**STAFF, "courses_manager": "read"},
    "equipment.rental_lists.manage": SESSIONS,
    "equipment.actual_quantities": SESSIONS,
    "equipment.reviews.manage": STAFF,
    "equipment.costs.view": {**STAFF, "courses_manager": "own_activities", "board": "read"},
    "equipment.field.participant_price": SESSIONS,
    "equipment.import.run": {"equipment_manager": "all", "administrator": "all"},
}
NOTE = "Permisos del 03 Material: MT3 a MT13 (amb MT6b) i C4 (T-M03-18)."


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
    dependencies = [("core", "0063_licences_import_and_settings_permissions")]

    operations = [migrations.RunPython(load, unload)]
