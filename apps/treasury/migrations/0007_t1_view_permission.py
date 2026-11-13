"""T1, «Veure comptes, saldos i moviments» (M04-4; matriu inicial de la 059): les cel·les
inicials del tresorer i de l'administrador, amb una versió nova de la matriu (060: mai editant
la 0003 del nucli). És aquí i no al nucli perquè el permís és de la 04 i una migració nova del
nucli xocaria amb les que hi afegeixen altres tasques alhora."""

from django.db import migrations
from django.db.models import Max

CODE = "treasury.view"
CELLS = [("treasurer", CODE, "all"), ("administrator", CODE, "all")]
NOTE = "T1, veure comptes, saldos i moviments de tresoreria (T-M04-15)."


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
        ("core", "0028_p22_exempt_fee"),
        ("treasury", "0006_movement_immutable"),
    ]

    operations = [migrations.RunPython(load, unload)]
