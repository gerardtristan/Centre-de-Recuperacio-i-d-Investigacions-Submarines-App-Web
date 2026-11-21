"""Addenda de la 104 (T-M02-48, part del nucli): AC24 (fotos de titulacions: veure; secretaria, i
«Cons.» la junta), AC25 (fotos i homologacions: veure i editar; secretaria) i AC26 (tramitacions
a la federació; secretaria, administrador i President, com LC5), amb una versió nova de la matriu
(060). Patró de la 0065."""

from django.db import migrations
from django.db.models import Max

CELLS = {
    "settings.section.activities": {"secretary": "read", "president": "read"},
    "settings.edit.activities.homologation_target_agency": {
        "courses_manager": "all",
        "treasurer": "all",
        "administrator": "all",
        "president": "all",
    },
    "settings.edit.activities.card_photos_enabled": {"administrator": "all"},
    "settings.edit.activities.card_photo_retention_months": {"secretary": "all"},
    "settings.edit.activities.homologation_fee_cents": {"treasurer": "all"},
    "settings.edit.activities.course_filing_fee_cents": {"treasurer": "all"},
    "settings.edit.activities.filing_fees_enabled": {"treasurer": "all"},
    "activities.card_photos.view": {"secretary": "all", "board": "read"},
    "activities.card_photos.manage": {"secretary": "all"},
    "activities.filings.manage": {"secretary": "all", "administrator": "all", "president": "all"},
}
NOTE = "Addenda de la 104: AC24, AC25 i AC26 i els ajustos VC-55 a VC-59 (T-M02-48)."  # fmt: skip


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
    RolePermission.objects.filter(permission_code__in=CELLS).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0067_activities_settings_permissions")]

    operations = [migrations.RunPython(load, unload)]
