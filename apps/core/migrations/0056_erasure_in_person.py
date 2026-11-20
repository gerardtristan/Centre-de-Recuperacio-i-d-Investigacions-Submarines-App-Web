"""T-M01-22c (085, A-2): canal «presencial» a la sol·licitud d'esborrat i el permís de
registrar-la (M11b), només per a la Secretaria (P-417), amb una versió nova de la matriu (060).
Patró de la 0055."""

from django.db import migrations, models
from django.db.models import Max

CODE = "core.gdpr.register_in_person"
CELLS = [("secretary", CODE, "all")]
NOTE = "RGPD: registrar la sol·licitud d'esborrat presencial d'un menor de 14 anys (T-M01-22c)."


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
    dependencies = [("core", "0055_edit_instalments_permission")]

    operations = [
        migrations.AlterField(
            model_name="erasurerequest",
            name="channel",
            field=models.CharField(
                choices=[("web", "Web"), ("in_person", "Presencial")],
                max_length=10,
                verbose_name="canal",
            ),
        ),
        migrations.RunPython(load, unload),
    ]
