"""Nucli del 06 Llicències: el tipus de lot «licences» per al pas únic dels registres del 01
(P-M06-H, T-M06-14) i les cel·les inicials dels ajustos del mòdul (M06-6, «Valors
configurables»; LC9), amb una sola versió nova de la matriu (060). Patró de la 0060."""

from django.db import migrations, models
from django.db.models import Max

CELLS = {
    "settings.section.licences": {"secretary": "read", "administrator": "read"},
    "settings.edit.licences.non_members_enabled": {"administrator": "all"},
    "settings.edit.licences.day_enabled": {"administrator": "all"},
    "settings.edit.licences.reminder_days": {"secretary": "all"},
    "settings.edit.licences.to_renew_days": {"secretary": "all"},
    "settings.edit.licences.next_year_opens_on": {"secretary": "all"},
}
NOTE = "Ajustos de llicències: apartat, LC9 i els valors de la secretaria (T-M06-20)."


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


KINDS = [("cluber", "Cluber"), ("bank_statement", "Extracte bancari"),
         ("licences", "Llicències del 01")]  # fmt: skip


class Migration(migrations.Migration):
    dependencies = [("core", "0062_margins_and_grants_permissions")]

    operations = [
        migrations.RemoveConstraint(model_name="importbatch", name="importbatch_kind_valid"),
        migrations.AlterField(
            model_name="importbatch",
            name="kind",
            field=models.CharField(choices=KINDS, max_length=20, verbose_name="tipus"),
        ),
        migrations.AddConstraint(
            model_name="importbatch",
            constraint=models.CheckConstraint(
                condition=models.Q(kind__in=["cluber", "bank_statement", "licences"]),
                name="importbatch_kind_valid",
            ),
        ),
        migrations.RunPython(load, unload),
    ]
