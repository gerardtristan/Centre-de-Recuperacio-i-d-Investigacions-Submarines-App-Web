"""Cel·les inicials dels permisos del 02 Activitats (matriu inicial de la 059, «02 Activitats», i
addenda de llocs del 02; T-M02-33 i T-M02-38): AC5 a AC23 i el camp C7, amb una sola versió nova
de la matriu (060). Mateix patró que la 0060. C3 és protegit i no té fila."""

from django.db import migrations
from django.db.models import Max

MANAGERS = {"courses_manager": "all", "treasurer": "all", "administrator": "all",
            "president": "all"}  # fmt: skip
NO_TREASURER = {"courses_manager": "all", "administrator": "all", "president": "all"}
CELLS = {
    "activities.enrol_in_person": MANAGERS,  # AC5
    "activities.catalogue.manage": MANAGERS,  # AC6
    "activities.manage": MANAGERS,  # AC7
    "activities.participants.view": {
        **MANAGERS,
        "instructor": "own_sessions",
        "equipment_manager": "read",
    },  # AC8  # fmt: skip
    "activities.attendance.record": {**NO_TREASURER, "instructor": "own_sessions"},  # AC9
    "activities.assessment.record": {"instructor": "own_sessions"},  # AC10a
    "activities.reinforcement.propose": {"instructor": "own_sessions"},  # AC10b
    "activities.reinforcement.decide": NO_TREASURER,  # AC11
    "activities.outcome.record": {"instructor": "own_sessions"},  # AC12
    "activities.certificate.issue": NO_TREASURER,  # AC13
    "activities.environment.manage": {**NO_TREASURER, "board": "read"},  # AC14
    "activities.message.send": MANAGERS,  # AC15
    "activities.waitlist.manage": MANAGERS,  # AC16
    "activities.refund.propose": MANAGERS,  # AC17
    "activities.refund.execute": {"treasurer": "all"},  # AC18
    "activities.income.view": {
        "courses_manager": "read",
        "treasurer": "all",
        "administrator": "all",
    },  # AC19  # fmt: skip
    "activities.reports.view": {
        **MANAGERS,
        "instructor": "own_sessions",
        "equipment_manager": "read",
        "board": "read",
    },  # AC20  # fmt: skip
    "activities.places.view": {**MANAGERS, "equipment_manager": "all"},  # AC21
    "activities.places.manage": MANAGERS,  # AC22
    "activities.material_cost.edit": {
        "courses_manager": "own_activities",
        "treasurer": "all",
        "administrator": "all",
    },  # AC23  # fmt: skip
    "activities.field.material_cost": {
        "courses_manager": "own_activities",
        "equipment_manager": "all",
        "treasurer": "all",
        "administrator": "all",
        "president": "all",
        "board": "read",
    },  # C7  # fmt: skip
}
NOTE = "Permisos del 02 Activitats: AC5 a AC23 i C7 (T-M02-33 i T-M02-38)."


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
    dependencies = [("core", "0060_licences_permissions")]

    operations = [migrations.RunPython(load, unload)]
