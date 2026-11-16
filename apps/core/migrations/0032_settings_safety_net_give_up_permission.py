"""Cel·la inicial del valor nou de VC-17 (decisió 093; T-M05b-28): només l'Administrador edita
les hores que la xarxa de seguretat torna a provar una ordre, amb una versió nova de la matriu
(060). L'ajust el crea `payments/0005`. Mateix patró que la 0031."""

from django.db import migrations
from django.db.models import Max

CODE = "settings.edit.payments.safety_net_give_up_hours"
NOTE = "Ajustos de pagaments: editar les hores de la xarxa de seguretat (decisió 093; T-M05b-28)."


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    _cell, created = RolePermission.objects.get_or_create(
        role=Role.objects.get(code="administrator"), permission_code=CODE, defaults={"scope": "all"}
    )
    if created:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        PermissionMatrixVersion.objects.create(
            number=last + 1,
            note=NOTE,
            diff=[{"role": "administrator", "permission": CODE, "before": None, "after": "all"}],
        )


def unload(apps, schema_editor):
    apps.get_model("core", "RolePermission").objects.filter(permission_code=CODE).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0031_settings_payments_permissions")]

    operations = [migrations.RunPython(load, unload)]
