"""Permís de l'ajust del tipus de la primera llicència (P-530; T-M02-51a, part del nucli): el
trien la secretaria i el tresorer, i el tresorer passa a veure l'apartat de llicències. Una versió
nova de la matriu (060)."""

from django.db import migrations
from django.db.models import Max

CELLS = {
    "settings.section.licences": {"treasurer": "read"},
    "settings.edit.licences.first_licence_type": {"secretary": "all", "treasurer": "all"},
}
NOTE = "Tipus de la primera llicència d'un alumne nou: la secretaria i el tresorer (P-530)."


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
    dependencies = [("core", "0073_activities_first_licence_permissions")]

    operations = [migrations.RunPython(load, unload)]
