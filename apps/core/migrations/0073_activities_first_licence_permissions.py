"""Permisos de «Inclou la primera llicència» i dels ajustos VC-60 i VC-61 (T-M02-50, part del
nucli; addenda de la 104; RN-M02-57 i 59; respostes provisionals del propietari a P-426 i P-427,
21/11/2026): AC27 per veure el camp, AC28 per canviar-lo (com els preus del catàleg) i el
tresorer, els dos ajustos. Una versió nova de la matriu (060)."""

from django.db import migrations
from django.db.models import Max

MANAGERS = {"courses_manager": "all", "treasurer": "all", "administrator": "all",
            "president": "all"}  # fmt: skip
CELLS = {
    "activities.first_licence.view": {**MANAGERS, "secretary": "all"},  # AC27
    "activities.first_licence.manage": MANAGERS,  # AC28
    "settings.edit.activities.included_licence_expense_category": {"treasurer": "all"},  # VC-60
    "settings.edit.activities.homologation_department": {"treasurer": "all"},  # VC-61
}
NOTE = (
    "«Inclou la primera llicència» (AC27 i AC28) i ajustos de la categoria de despesa de la "
    "llicència inclosa i del departament de les homologacions (T-M02-50)."
)


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
    for code, cells in CELLS.items():
        RolePermission.objects.filter(permission_code=code, role__code__in=cells).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0072_margin_and_grants_settings_permissions")]

    operations = [migrations.RunPython(load, unload)]
