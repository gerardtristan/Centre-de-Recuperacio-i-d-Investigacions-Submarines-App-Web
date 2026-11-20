"""T-M01-49c (072, tercera instrucció, punt 2): permís propi per editar l'import i el venciment
dels terminis d'una quota (P23), només per a la Secretaria (P-413), amb una versió nova de la
matriu (060). Patró de la 0052."""

from django.db import migrations
from django.db.models import Max

CODE = "members.fees.edit_instalments"
CELLS = [("secretary", CODE, "all")]
NOTE = "Socis: editar l'import i el venciment dels terminis d'una quota (T-M01-49c)."


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
    dependencies = [("core", "0054_import_line_last_renewal")]

    operations = [migrations.RunPython(load, unload)]
