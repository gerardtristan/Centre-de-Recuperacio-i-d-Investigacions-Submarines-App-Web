"""P22, «Eximir o anul·lar una quota, amb motiu» (RN-M01-72; decisió 085, J-2): la cel·la inicial
del tresorer, amb una versió nova de la matriu (060: mai editant la 0003)."""

from django.db import migrations
from django.db.models import Max

CODE = "members.fees.exempt"
CELLS = [("treasurer", CODE, "all")]
NOTE = "P22, eximir o anul·lar una quota amb motiu (decisió 085)."


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
        ("core", "0027_charge_cancel_category"),
    ]

    operations = [migrations.RunPython(load, unload)]
