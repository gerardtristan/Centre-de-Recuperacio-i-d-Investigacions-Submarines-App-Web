"""Cel·les inicials de T6, «Registrar un traspàs», i T7, «Registrar un arqueig» (M04-4;
T-M04-09): Tresorer i Administrador, tots dos «Sí» a la matriu, amb una versió nova de la matriu
(060). Mateix patró que la 0036, amb dos codis."""

from django.db import migrations
from django.db.models import Max

CODES = ("treasury.transfer", "treasury.cash_count")
NOTE = "T6 i T7, registrar un traspàs i un arqueig de tresoreria (T-M04-09)."
ROLES = ("treasurer", "administrator")


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    diff = []
    for code in CODES:
        for role in ROLES:
            _cell, created = RolePermission.objects.get_or_create(
                role=Role.objects.get(code=role), permission_code=code, defaults={"scope": "all"}
            )
            if created:
                diff.append({"role": role, "permission": code, "before": None, "after": "all"})
    if diff:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    apps.get_model("core", "RolePermission").objects.filter(permission_code__in=CODES).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0038_payments_mandates_revoke_permission")]

    operations = [migrations.RunPython(load, unload)]
