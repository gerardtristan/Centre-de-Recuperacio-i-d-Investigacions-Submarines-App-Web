"""Permís d'editar l'ajust VC-23 (`activities.reminder_days_before`, dies del recordatori d'una
activitat; RN-M02-19; T-M02-21, part del nucli): la secretaria. Una versió nova de la matriu (060)."""

from django.db import migrations
from django.db.models import Max

CELLS = {"settings.edit.activities.reminder_days_before": {"secretary": "all"}}
NOTE = "Dies del recordatori d'una activitat (VC-23): la secretaria (T-M02-21)."


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
    dependencies = [("core", "0075_marine_forecast_url_permission")]

    operations = [migrations.RunPython(load, unload)]
