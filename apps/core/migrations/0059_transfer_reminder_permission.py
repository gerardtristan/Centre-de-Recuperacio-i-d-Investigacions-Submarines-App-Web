"""T-M05b-22c (VC-16; RN-M05b-09): el Tresorer edita els dies del recordatori de transferència,
amb una versió nova de la matriu (060). L'ajust el crea `payments/0029`. Patró de la 0042."""

from django.db import migrations
from django.db.models import Max

CODE = "settings.edit.payments.transfer_reminder_days"
NOTE = "Ajustos de pagaments: el Tresorer edita els dies del recordatori de transferència (T-M05b-22c)."


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    _cell, created = RolePermission.objects.get_or_create(
        role=Role.objects.get(code="treasurer"), permission_code=CODE, defaults={"scope": "all"}
    )
    if created:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        diff = [{"role": "treasurer", "permission": CODE, "before": None, "after": "all"}]
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    apps.get_model("core", "RolePermission").objects.filter(permission_code=CODE).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0058_payment_origin")]

    operations = [migrations.RunPython(load, unload)]
