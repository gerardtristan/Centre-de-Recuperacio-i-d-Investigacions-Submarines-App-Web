"""Cel·la inicial de T4, «Conciliar i desfer una conciliació» (M04-4; T-M04-12): només el
Tresorer, amb una versió nova de la matriu (060). L'Administrador, [A validar] al M04-4, comença
sense (P-112). Mateix patró que la 0032."""

from django.db import migrations
from django.db.models import Max

CODE = "treasury.reconcile"
NOTE = "T4, conciliar i desfer una conciliació de l'extracte (T-M04-12)."


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    _cell, created = RolePermission.objects.get_or_create(
        role=Role.objects.get(code="treasurer"), permission_code=CODE, defaults={"scope": "all"}
    )
    if created:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        PermissionMatrixVersion.objects.create(
            number=last + 1,
            note=NOTE,
            diff=[{"role": "treasurer", "permission": CODE, "before": None, "after": "all"}],
        )


def unload(apps, schema_editor):
    apps.get_model("core", "RolePermission").objects.filter(permission_code=CODE).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0032_settings_safety_net_give_up_permission")]

    operations = [migrations.RunPython(load, unload)]
