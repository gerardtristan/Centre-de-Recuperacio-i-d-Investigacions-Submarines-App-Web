"""Permisos de l'apartat «Material» dels ajustos que faltaven (T-M03-22, part del nucli; 055): el
responsable de material edita els dies de l'avís de material no retornat (VC-29,
`equipment.unreturned_after_days`) i el tresorer, el cost d'ús per tipus de material (VC-28, amb
data d'entrada en vigor i avís, RN-AJ-04); el tresorer veu l'apartat. Una versió nova de la matriu
(060)."""

from django.db import migrations
from django.db.models import Max

CELLS = {
    "settings.section.equipment": {"treasurer": "read"},
    "settings.edit.equipment.unreturned_after_days": {"equipment_manager": "all"},
    "settings.edit.equipment.usage_rates": {"treasurer": "all"},
}
NOTE = (
    "Ajustos de material: el responsable de material edita els dies del material no retornat i el "
    "tresorer, el cost d'ús per tipus (T-M03-22)."
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
    dependencies = [("core", "0070_importbatch_kind_equipment")]

    operations = [migrations.RunPython(load, unload)]
