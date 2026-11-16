"""Cel·les inicials de T5, «Anul·lar un moviment amb motiu» (M04-4; T-M04-08): Tresorer i
Administrador, tots dos «Sí» a la matriu, amb una versió nova de la matriu (060). Mateix patró
que la 0035."""

from django.db import migrations
from django.db.models import Max

CODE = "treasury.reverse"
NOTE = "T5, anul·lar un moviment de tresoreria amb motiu (T-M04-08)."
ROLES = ("treasurer", "administrator")


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    diff = []
    for role in ROLES:
        _cell, created = RolePermission.objects.get_or_create(
            role=Role.objects.get(code=role), permission_code=CODE, defaults={"scope": "all"}
        )
        if created:
            diff.append({"role": role, "permission": CODE, "before": None, "after": "all"})
    if diff:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    apps.get_model("core", "RolePermission").objects.filter(permission_code=CODE).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0035_payments_mandates_view_permission")]

    operations = [migrations.RunPython(load, unload)]
