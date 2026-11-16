"""Cel·les inicials de l'apartat d'ajustos de pagaments (RN-RP-22; VC-17), amb una versió nova
de la matriu (060). Els ajustos els crea la migració del 05b."""

from django.db import migrations
from django.db.models import Max

SECTION = "settings.section.payments"
CELLS = [
    ("treasurer", SECTION, "read"),
    ("administrator", SECTION, "read"),
    ("administrator", "settings.edit.payments.bizum_ui_timeout_minutes", "all"),
    ("administrator", "settings.edit.payments.safety_net_age_minutes", "all"),
]
NOTE = "Ajustos de pagaments: veure l'apartat i editar els valors de VC-17 (T-AJ-02)."


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
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
    apps.get_model("core", "RolePermission").objects.filter(
        permission_code__in={code for _role, code, _scope in CELLS}
    ).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0030_importline_bank_statement")]

    operations = [migrations.RunPython(load, unload)]
