"""T-M01-49 (097, P-61): permís d'editar els ajustos del pagament a terminis, per al tresorer i
l'administrador (com el preu de la quota; P-396), amb una versió nova de la matriu (060). Veure'ls
és l'apartat de socis (`core/0046`). Els ajustos els crea `members/0024`. Patró de la 0046."""

from django.db import migrations
from django.db.models import Max

CODE = "settings.edit.members.instalments"
CELLS = [("treasurer", CODE, "all"), ("administrator", CODE, "all")]
NOTE = "Ajustos de socis: editar el pagament a terminis de la quota de ple dret (T-M01-49)."


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
    dependencies = [("core", "0051_help_texts")]

    operations = [migrations.RunPython(load, unload)]
