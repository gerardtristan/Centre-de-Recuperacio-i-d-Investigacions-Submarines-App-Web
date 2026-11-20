"""T-M01-43e (P-399): permís d'editar els mesos de l'avís de renovació, per al Tresorer, amb una
versió nova de la matriu (060). Veure'l és l'apartat de socis. L'ajust el crea `members/0025`.
Patró de la 0052."""

from django.db import migrations
from django.db.models import Max

CODE = "settings.edit.members.renewal_notice_months"
CELLS = [("treasurer", CODE, "all")]
NOTE = "Ajustos de socis: editar els mesos de l'avís de renovació (T-M01-43e)."


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
    dependencies = [("core", "0056_erasure_in_person")]

    operations = [migrations.RunPython(load, unload)]
