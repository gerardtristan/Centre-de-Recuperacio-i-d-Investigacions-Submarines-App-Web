"""Cel·la inicial de l'ajust de la finestra de cobrament amb la targeta guardada (T-M05b-15a): el
Tresorer l'edita, com els altres valors de cobrament (VC-16), amb una versió nova de la matriu
(060). L'ajust el crea `payments/0017`. Patró de la 0043."""

from django.db import migrations
from django.db.models import Max

CODE = "settings.edit.payments.saved_card_charge_window_days"
NOTE = "Ajustos de pagaments: el Tresorer edita la finestra de cobrament amb la targeta guardada."


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
    dependencies = [
        ("core", "0043_settings_vc11_permission"),
        ("payments", "0017_cobrament_targeta_guardada"),
    ]

    operations = [migrations.RunPython(load, unload)]
