"""T-M02-30 (part del nucli; VC-46; RN-M02-26): el responsable de cursos i sortides edita
`activities.instructor_requirements_mode`, amb una versió nova de la matriu (060). Patró de la
0067."""

from django.db import migrations
from django.db.models import Max

CELLS = {"settings.edit.activities.instructor_requirements_mode": {"courses_manager": "all"}}
NOTE = "Ajust VC-46 (requisits per fer classe): l'edita el responsable de cursos (T-M02-30)."


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
    dependencies = [("core", "0068_activities_filings_permissions")]

    operations = [migrations.RunPython(load, unload)]
