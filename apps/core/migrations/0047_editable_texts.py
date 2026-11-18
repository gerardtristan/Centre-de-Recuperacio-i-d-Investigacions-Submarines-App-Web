"""Textos editables dels correus (T-M00-08; 085, S-1 i S-3): un ajust de text per correu a
l'apartat «texts», buit (el text per defecte del codi), i les cel·les inicials de l'apartat
amb una versió nova de la matriu (060). Patró de la 0046 i de `members/0022`."""

from django.db import migrations
from django.db.models import Max

KEYS = ["texts.baixa-efectiva", "texts.recordatori-quota", "texts.recordatori-quota-vencuda"]
SECTION = "settings.section.texts"
CELLS = [("secretary", SECTION, "all"), ("administrator", SECTION, "read")]
NOTE = "Textos dels correus: la Secretaria els edita i l'administrador els veu (T-M00-08)."


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    for key in KEYS:
        Setting.objects.get_or_create(
            key=key,
            defaults={
                "module": "texts",
                "value_type": "text",
                "initial_value": "",
                "max_length": 5000,
            },
        )
    diff = []
    for role, code, scope in CELLS:
        _cell, created = RolePermission.objects.get_or_create(
            role=Role.objects.get(code=role), permission_code=code, defaults={"scope": scope}
        )
        if created:
            diff.append({"role": role, "permission": code, "before": None, "after": scope})
    if diff:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    apps.get_model("core", "RolePermission").objects.filter(permission_code=SECTION).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()
    apps.get_model("core", "SettingVersion").objects.filter(setting__key__in=KEYS).delete()
    apps.get_model("core", "Setting").objects.filter(key__in=KEYS).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0046_settings_members_permissions")]

    operations = [migrations.RunPython(load, unload)]
