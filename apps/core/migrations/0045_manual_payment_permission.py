"""Cel·la inicial de M14, registrar un cobrament manual (P-12; 072, Q-037): el Tresorer, amb una
versió nova de la matriu (060). Patró de la 0043."""

from django.db import migrations
from django.db.models import Max

CODE = "core.charges.record_manual"
NOTE = "P-12: el Tresorer registra cobraments manuals (efectiu o presencial) amb motiu."


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
    dependencies = [("core", "0044_settings_saved_card_window_permission")]

    operations = [migrations.RunPython(load, unload)]
