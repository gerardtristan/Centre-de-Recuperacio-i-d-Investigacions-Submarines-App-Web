"""Permisos dels ajustos del dashboard `dashboard.low_occupancy_pct` i `dashboard.default_period`
(M08-4 i M08-6; P-645): el llindar d'ocupació, el RCS i l'Administrador; el període, només
l'Administrador. El RCS entra a l'apartat amb «Cons.», que és el que demana RN-RP-22 per editar
un sol valor. Una versió nova de la matriu (060). La còpia fixa de les cel·les és la del catàleg
d'aquest moment: una migració no importa el catàleg."""

from django.db import migrations
from django.db.models import Max

ADMIN, RCS = "administrator", "courses_manager"
CELLS = {
    "settings.section.dashboard": {RCS: "read"},
    "settings.edit.dashboard.low_occupancy_pct": {ADMIN: "all", RCS: "all"},
    "settings.edit.dashboard.default_period": {ADMIN: "all"},
}
NOTE = "Ajustos del dashboard: llindar d'ocupació baixa i període per defecte (M08-6; P-645)."


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
    dependencies = [("core", "0079_activities_certifications_permission")]

    operations = [migrations.RunPython(load, unload)]
