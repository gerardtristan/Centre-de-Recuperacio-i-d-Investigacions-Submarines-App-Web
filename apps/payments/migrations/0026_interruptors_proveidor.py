"""P-131 (095; VC-14): els mètodes actius del proveïdor (targeta, Bizum i targeta guardada) passen a
ajustos que edita l'Administrador (A7), amb una versió nova de la matriu (060). Tots comencen
actius: el que ofereix cada pantalla és el que el proveïdor declara i, a més, el club té actiu.
Patró de la 0021."""

from django.db import migrations
from django.db.models import Max

KEYS = [f"payments.provider.{m}_enabled" for m in ("card", "bizum", "saved_card")]
CODE = "settings.edit.payments.provider"
NOTE = "Ajustos de pagaments: l'Administrador edita els mètodes actius del proveïdor (P-131)."


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    for key in KEYS:
        Setting.objects.get_or_create(
            key=key,
            defaults={"module": "payments", "value_type": "boolean", "initial_value": True},
        )
    _cell, created = RolePermission.objects.get_or_create(
        role=Role.objects.get(code="administrator"), permission_code=CODE, defaults={"scope": "all"}
    )
    if created:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        diff = [{"role": "administrator", "permission": CODE, "before": None, "after": "all"}]
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    """La cel·la i la versió de la matriu se'n van; els ajustos es queden, com a la 0021."""
    apps.get_model("core", "RolePermission").objects.filter(permission_code=CODE).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0052_instalments_permission"),
        ("payments", "0025_decisio_del_tresorer"),
    ]

    operations = [migrations.RunPython(load, unload)]
