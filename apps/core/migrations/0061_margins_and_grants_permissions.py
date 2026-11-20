"""Cel·les inicials dels permisos del 09 (M09-4, M09-ajuts-4 i la matriu inicial de la 059;
T-M09-30): MG1 a MG9, MG11, MG13, MG14 i AJ1 a AJ11, AJ13, amb una sola versió nova de la matriu
(060). Mateix patró que la 0060. MG12, C5 i AJ12 són protegits: no tenen cap fila."""

from django.db import migrations
from django.db.models import Max

BOTH = {"treasurer": "all", "administrator": "all"}
GRANTS = {"treasurer": "all", "board": "all", "administrator": "all"}
OWN_GRANTS = {"treasurer": "all", "board": "own_applications", "administrator": "all"}
CELLS = {
    "expenses.record": {
        "courses_manager": "own_activities",
        "treasurer": "all",
        "administrator": "all",
        "president": "all",
    },
    "expenses.pay": BOTH,
    "expenses.allocate": BOTH,
    "expenses.other_income": BOTH,
    "expenses.planned_costs": {
        "courses_manager": "own_activities",
        "treasurer": "all",
        "administrator": "all",
    },
    "expenses.margin.view": {
        "courses_manager": "own_activities",
        "treasurer": "all",
        "administrator": "all",
        "president": "all",
        "board": "read",
    },
    "expenses.margin.close_activity": BOTH,
    "expenses.reports": {"treasurer": "all", "administrator": "all", "board": "read"},
    "expenses.invoices.issue": BOTH,
    "expenses.periods.close": BOTH,
    "expenses.volunteering": BOTH,
    "expenses.catalogues": BOTH,
    "grants.view": GRANTS,
    "grants.calls.manage": GRANTS,
    "grants.eligibility": GRANTS,
    "grants.applications.prepare": OWN_GRANTS,
    "grants.applications.resolve": OWN_GRANTS,
    "grants.applications.amendments": OWN_GRANTS,
    "grants.income": BOTH,
    "grants.justification": {"treasurer": "all", "board": "read", "administrator": "all"},
    "grants.applications.close": BOTH,
    "grants.applications.undo": {"administrator": "all"},
    "grants.alert_days": BOTH,
    "grants.audit.view": {"treasurer": "read", "administrator": "all"},
}
NOTE = "Permisos del 09 i de l'apartat d'ajuts: MG1 a MG14 i AJ1 a AJ13 (T-M09-30)."


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
    dependencies = [("core", "0060_licences_permissions")]

    operations = [migrations.RunPython(load, unload)]
