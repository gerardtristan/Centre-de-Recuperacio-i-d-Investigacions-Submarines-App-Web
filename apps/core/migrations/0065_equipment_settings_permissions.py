"""Permisos de l'apartat «Material» dels ajustos (T-M03-22, part del nucli; 055): «Cons.» per al
responsable de material i l'administrador, i el responsable de material edita els dies de l'avís
de revisió (VC-29, `equipment.review_notice_days`), amb una versió nova de la matriu (060)."""

from django.db import migrations
from django.db.models import Max

CELLS = {
    "settings.section.equipment": {"equipment_manager": "read", "administrator": "read"},
    "settings.edit.equipment.review_notice_days": {"equipment_manager": "all"},
}
NOTE = "Ajustos de material: el responsable de material edita els dies de l'avís de revisió (T-M03-22)."


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
    dependencies = [("core", "0064_equipment_permissions")]

    operations = [migrations.RunPython(load, unload)]
