"""Permisos del 07 i del 08 a la matriu inicial (T-M07-02, M07-4; M08-4 i M08-6, T-M08-02 i 03):
WP1 a WP8, DB1 i DB2, i els apartats d'ajustos «website» i «dashboard» amb els seus valors.
Una versió nova de la matriu (060). La còpia fixa de les cel·les és la del catàleg d'aquest
moment: una migració no importa el catàleg."""

from django.db import migrations
from django.db.models import Max

ADMIN, PRES, SECR, BOARD = "administrator", "president", "secretary", "board"
RCS, RM, TRES, DH = "courses_manager", "equipment_manager", "treasurer", "history_department"
WP1 = {ADMIN: "all", PRES: "all"}

CELLS = {
    "website.pages": WP1,
    "website.news": WP1,
    "website.media": WP1,
    "website.help": {**WP1, BOARD: "all"},
    "website.contact": {SECR: "all", ADMIN: "all"},
    "website.newsletter": WP1,
    "website.subscribers": {ADMIN: "all"},
    "website.contact_reasons": {ADMIN: "all"},
    "settings.section.website": {ADMIN: "read", PRES: "read"},
    "settings.edit.website.home_activities_count": WP1,
    "settings.edit.website.news_on_home": WP1,
    "settings.edit.website.club_contact": WP1,
    "settings.edit.website.newsletter_enabled": {ADMIN: "all"},
    "settings.edit.website.newsletter_confirm_hours": {ADMIN: "all"},
    "settings.edit.website.contact_enabled": {ADMIN: "all"},
    "settings.edit.website.contact_retention_months": {ADMIN: "all"},
    "dashboard.view": dict.fromkeys((SECR, RCS, RM, TRES, DH, ADMIN, PRES), "all"),
    "dashboard.actions": dict.fromkeys((RCS, TRES, ADMIN, PRES), "all"),
    "settings.section.dashboard": {ADMIN: "all"},
    "settings.edit.dashboard.help_text": {ADMIN: "all"},
    "settings.edit.dashboard.min_group_size": {ADMIN: "all"},
}
NOTE = "Web pública (WP1 a WP8, M07-4) i dashboard (DB1, DB2, M08-4), amb els seus ajustos."


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
    dependencies = [("core", "0077_encrypted_file_kinds")]

    operations = [migrations.RunPython(load, unload)]
