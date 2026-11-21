"""Permisos de l'apartat «Activitats» dels ajustos (T-M02-28, part del nucli; 055): «Cons.» per al
responsable de cursos i sortides, el tresorer i l'administrador; el tresorer edita les hores per
pagar (VC-21) i el responsable, les hores per acceptar una oferta (VC-22) i el mode dels requisits
(VC-24), amb una versió nova de la matriu (060). Patró de la 0065."""

from django.db import migrations
from django.db.models import Max

CELLS = {
    "settings.section.activities": {
        "courses_manager": "read",
        "treasurer": "read",
        "administrator": "read",
    },
    "settings.edit.activities.default_payment_window_hours": {"treasurer": "all"},
    "settings.edit.activities.offer_accept_hours": {"courses_manager": "all"},
    "settings.edit.activities.default_requirements_mode": {"courses_manager": "all"},
}
NOTE = "Ajustos d'activitats: VC-21 el tresorer, VC-22 i VC-24 el responsable (T-M02-28)."


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
    dependencies = [("core", "0066_billing_settings_permissions")]

    operations = [migrations.RunPython(load, unload)]
