"""Cel·les inicials de l'apartat d'ajustos de socis (T-M01-32; RN-RP-22; columna «Qui el canvia»
de l'addenda de la 055 i de l'ampliació de la 091), amb una versió nova de la matriu (060). Els
ajustos els crea `members/0022`. Patró de la 0031."""

from django.db import migrations
from django.db.models import Max

SECTION = "settings.section.members"
EDIT = "settings.edit.members."
CELLS = [
    ("treasurer", SECTION, "read"),
    ("administrator", SECTION, "read"),
    ("secretary", SECTION, "read"),
    ("treasurer", EDIT + "annual_fee_cents.full", "all"),
    ("administrator", EDIT + "annual_fee_cents.full", "all"),
    ("treasurer", EDIT + "annual_fee_cents.supporter", "all"),
    ("administrator", EDIT + "annual_fee_cents.supporter", "all"),
    ("treasurer", EDIT + "fee_reminder_offsets", "all"),
    ("treasurer", EDIT + "type_change_supplement_due_days", "all"),
    ("secretary", EDIT + "card_back_text", "all"),
    ("administrator", EDIT + "card_back_text", "all"),
    ("administrator", EDIT + "classic_member_years", "all"),
]
NOTE = "Ajustos de socis: veure l'apartat i editar els valors VC-01 a VC-04 i VC-53 (T-M01-32)."


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
    dependencies = [("core", "0045_manual_payment_permission")]

    operations = [migrations.RunPython(load, unload)]
