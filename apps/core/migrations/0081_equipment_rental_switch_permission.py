"""Permís per editar l'interruptor `equipment.rental_charges_enabled` (T-M03-11; RN-M03-11
[A validar: junta i tresorer, S-M03-03]): el pla no diu qui el canvia; d'inici, l'administrador i
el tresorer (P-662). L'interruptor continua apagat. Una versió nova de la matriu (060). La còpia
fixa de les cel·les és la del catàleg d'aquest moment: una migració no importa el catàleg."""

from django.db import migrations
from django.db.models import Max

CELLS = {
    "settings.edit.equipment.rental_charges_enabled": {"administrator": "all", "treasurer": "all"},
}
NOTE = "Material: cobrar al participant el material llogat (T-M03-11; P-662)."


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
    """Només les cel·les que va crear `load` (les del `diff` de la seva versió de la matriu): una
    cel·la que ja hi era (p. ex. «Cons.» de l'apartat posat des de l'app) es queda."""
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    for version in PermissionMatrixVersion.objects.filter(note=NOTE):
        for cell in version.diff:
            RolePermission.objects.filter(
                permission_code=cell["permission"], role__code=cell["role"]
            ).delete()
        version.delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0080_dashboard_settings_permissions")]

    operations = [migrations.RunPython(load, unload)]
