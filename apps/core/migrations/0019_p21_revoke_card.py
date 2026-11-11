"""P21, «Revocar el carnet d'un soci, amb motiu» (079, A-21; RN-M01-92): la cel·la inicial de
la secretaria, amb una versió nova de la matriu (060: mai editant la 0003)."""

from django.db import migrations
from django.db.models import Max

CODE = "members.card.revoke"
CELLS = [("secretary", CODE, "all")]
NOTE = "P21, revocar el carnet d'un soci amb motiu (decisió 079)."


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
    apps.get_model("core", "RolePermission").objects.filter(permission_code=CODE).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0018_p7a_cancel_supplement"),
    ]

    operations = [migrations.RunPython(load, unload)]
