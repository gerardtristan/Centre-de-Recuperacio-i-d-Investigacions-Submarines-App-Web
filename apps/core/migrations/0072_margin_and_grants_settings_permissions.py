"""Permisos dels apartats «Marges i períodes» i «Ajuts» dels ajustos (T-M09-26, part del nucli;
055): «Cons.» per al tresorer i l'administrador, i el tresorer edita el llindar de marge baix
(VC-31), la durada dels períodes nous (VC-32) i els dies dels avisos dels ajuts (VC-36 i VC-37).
Una versió nova de la matriu (060). El número de la migració el fixa el PILOT al torn del nucli."""

from django.db import migrations
from django.db.models import Max

CELLS = {
    "settings.section.margin": {"treasurer": "read", "administrator": "read"},
    "settings.edit.margin.low_margin_threshold_cents": {"treasurer": "all"},
    "settings.edit.margin.period_length": {"treasurer": "all"},
    "settings.section.grants": {"treasurer": "read", "administrator": "read"},
    "settings.edit.grants.deadline_reminder_days": {"treasurer": "all"},
    "settings.edit.grants.requirement_reminder_days": {"treasurer": "all"},
}
NOTE = (
    "Ajustos de marges, períodes i ajuts: el tresorer edita el llindar de marge baix, la durada "
    "dels períodes nous i els dies dels avisos dels ajuts (T-M09-26)."
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
    dependencies = [("core", "0071_equipment_settings_more_permissions")]

    operations = [migrations.RunPython(load, unload)]
