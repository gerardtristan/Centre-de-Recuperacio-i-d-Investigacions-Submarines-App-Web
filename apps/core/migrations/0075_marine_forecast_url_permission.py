"""Permís per editar l'enllaç per defecte a la previsió marítima (VC-25, T-M02-28b, part del
nucli; RN-M02-24): l'administrador, dins de l'apartat «Activitats» dels ajustos, que ja hi té
«Cons.». Una versió nova de la matriu (060). El número el fixa el PILOT al torn del nucli."""

from django.db import migrations
from django.db.models import Max

CODE = "settings.edit.activities.marine_forecast_url"
NOTE = "Ajustos d'activitats: l'administrador edita l'enllaç a la previsió marítima (T-M02-28b)."


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    _cell, created = RolePermission.objects.get_or_create(
        role=Role.objects.get(code="administrator"), permission_code=CODE,
        defaults={"scope": "all"},
    )  # fmt: skip
    if created:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        diff = [{"role": "administrator", "permission": CODE, "before": None, "after": "all"}]
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    apps.get_model("core", "RolePermission").objects.filter(permission_code=CODE).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0074_licences_first_licence_type_permission")]

    operations = [migrations.RunPython(load, unload)]
