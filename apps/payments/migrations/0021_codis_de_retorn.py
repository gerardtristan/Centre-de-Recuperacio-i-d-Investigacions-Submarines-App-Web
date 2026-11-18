"""P-291 (095, provisional fins que el banc ho confirmi): els codis de retorn que proposen un
reintent i els que bloquegen el mandat passen a ajustos, amb els exemples de RN-M05b-15 com a valor
inicial. El Tresorer els edita, com els altres valors dels retornats (VC-16), amb una versió nova de
la matriu (060). Les cel·les són aquí i no en una migració de `core` perquè van amb els ajustos."""

from django.db import migrations
from django.db.models import Max

VALUES = {
    "payments.return_codes_retry": "AM04",
    "payments.return_codes_block_mandate": "AC04, MD01",
}
NOTE = "Ajustos de pagaments: el Tresorer edita els codis de retorn i l'acció de cada un (P-291)."


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    treasurer = Role.objects.get(code="treasurer")
    diff = []
    for key, value in VALUES.items():
        Setting.objects.get_or_create(
            key=key,
            defaults={"module": "payments", "value_type": "text", "initial_value": value,
                      "max_length": 200},
        )  # fmt: skip
        code = f"settings.edit.{key}"
        _cell, created = RolePermission.objects.get_or_create(
            role=treasurer, permission_code=code, defaults={"scope": "all"}
        )
        if created:
            diff.append({"role": "treasurer", "permission": code, "before": None, "after": "all"})
    if diff:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    """Les cel·les i la versió de la matriu se'n van; els ajustos es queden, com els de la 0013 i
    la 0014: un valor canviat té historial."""
    codes = [f"settings.edit.{key}" for key in VALUES]
    apps.get_model("core", "RolePermission").objects.filter(permission_code__in=codes).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0046_settings_members_permissions"),
        ("payments", "0020_campanya_darrer_recordatori"),
    ]

    operations = [migrations.RunPython(load, unload)]
