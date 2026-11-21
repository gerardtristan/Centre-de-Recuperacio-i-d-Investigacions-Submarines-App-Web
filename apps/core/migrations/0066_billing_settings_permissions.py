"""Permisos de l'apartat «Facturació» dels ajustos (T-M09-26, part del nucli; 055): «Cons.» per a
l'administrador, que és qui activa la facturació (VC-34, `billing.enabled_charge_kinds`) per
decisió de la junta (RN-M09-19), amb una versió nova de la matriu (060)."""

from django.db import migrations
from django.db.models import Max

CELLS = {
    "settings.section.billing": {"administrator": "read"},
    "settings.edit.billing.enabled_charge_kinds": {"administrator": "all"},
}
NOTE = "Ajustos de facturació: l'administrador activa la facturació per tipus de càrrec (T-M09-26)."


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
    dependencies = [("core", "0065_equipment_settings_permissions")]

    operations = [migrations.RunPython(load, unload)]
