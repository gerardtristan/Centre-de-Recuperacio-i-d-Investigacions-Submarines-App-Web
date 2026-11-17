"""Cel·les inicials de VC-16 (T-M05b-12; apèndix de valors configurables, columna «Edita»): el
Tresorer edita els dies de l'avís previ i el màxim d'intents de domiciliació, amb una versió nova
de la matriu (060). Els ajustos els creen `payments/0010` i `payments/0013`. Patró de la 0031."""

from django.db import migrations
from django.db.models import Max

CODES = (
    "settings.edit.payments.prenotification_days",
    "settings.edit.payments.max_direct_debit_attempts",
)
NOTE = "Ajustos de pagaments: el Tresorer edita els valors de VC-16 (T-M05b-12)."


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    treasurer, diff = Role.objects.get(code="treasurer"), []
    for code in CODES:
        _cell, created = RolePermission.objects.get_or_create(
            role=treasurer, permission_code=code, defaults={"scope": "all"}
        )
        if created:
            diff.append({"role": "treasurer", "permission": code, "before": None, "after": "all"})
    if diff:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    apps.get_model("core", "RolePermission").objects.filter(permission_code__in=CODES).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0041_events")]

    operations = [migrations.RunPython(load, unload)]
