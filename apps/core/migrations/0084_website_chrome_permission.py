"""WP9 (`website.chrome`: menús, capçalera, peu i blocs compartits de la web) a la matriu inicial,
amb la configuració de l'actual WP1: l'administrador i el President (addenda 106 del M07,
T-M07-21). Una versió nova de la matriu (060). La còpia fixa de les cel·les és la del catàleg
d'aquest moment: una migració no importa el catàleg."""

from django.db import migrations
from django.db.models import Max

CELLS = {"website.chrome": {"administrator": "all", "president": "all"}}
NOTE = "Web pública: menús, capçalera, peu i blocs compartits (WP9, addenda 106)."


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
    """Només les cel·les que va crear `load` (les del `diff` de la seva versió de la matriu)."""
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    for version in PermissionMatrixVersion.objects.filter(note=NOTE):
        for cell in version.diff:
            RolePermission.objects.filter(
                permission_code=cell["permission"], role__code=cell["role"]
            ).delete()
        version.delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0083_environment_photo_kind")]

    operations = [migrations.RunPython(load, unload)]
