"""AC29 «Titulacions: carregar a mà i verificar» (P-459, decisió 105; RN-M02-32; T-M02-52): la
Secretaria, el responsable de cursos i sortides i l'Administrador; la Junta, només consulta. Una
versió nova de la matriu (060)."""

from django.db import migrations
from django.db.models import Max

CODE = "activities.certifications.manage"
CELLS = {
    CODE: {
        "secretary": "all",
        "courses_manager": "all",
        "administrator": "all",
        "board": "read",
    }
}
NOTE = "Titulacions: carregar a mà i verificar (AC29, P-459; T-M02-52)."


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    diff = []
    for code, cells in CELLS.items():
        for role, scope in cells.items():
            _cell, created = RolePermission.objects.get_or_create(
                role=Role.objects.get(code=role), permission_code=code, defaults={"scope": scope}
            )
            if created:
                diff.append({"role": role, "permission": code, "before": None, "after": scope})
    if diff:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    RolePermission = apps.get_model("core", "RolePermission")
    for code, cells in CELLS.items():
        RolePermission.objects.filter(permission_code=code, role__code__in=cells).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0078_website_and_dashboard_permissions")]

    operations = [migrations.RunPython(load, unload)]
