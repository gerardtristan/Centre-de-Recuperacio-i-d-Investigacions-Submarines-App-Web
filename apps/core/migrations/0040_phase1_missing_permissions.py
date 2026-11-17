"""Cel·les inicials dels permisos de la fase 1 que faltaven al catàleg (M04-4, M05b-4 i la
matriu inicial de la 059; T-M04-16): T2, T3 i T9 de la tresoreria i B4 a B7 dels cobraments,
amb una sola versió nova de la matriu (060). B3 és protegit i no té files. Mateix patró que la
0039."""

from django.db import migrations
from django.db.models import Max

CELLS = {
    "treasury.accounts.manage": ("treasurer", "administrator"),
    "treasury.cost_centres.manage": ("administrator",),
    "treasury.export": ("treasurer", "administrator"),
    "payments.returns": ("treasurer",),
    "payments.refund": ("treasurer",),
    "payments.view": ("treasurer", "administrator"),
    "payments.resend": ("treasurer", "administrator"),
}
NOTE = "Permisos de la fase 1 que faltaven: T2, T3, T9 i B4 a B7 (T-M04-16)."


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    diff = []
    for code, roles in CELLS.items():
        for role in roles:
            _cell, created = RolePermission.objects.get_or_create(
                role=Role.objects.get(code=role), permission_code=code, defaults={"scope": "all"}
            )
            if created:
                diff.append({"role": role, "permission": code, "before": None, "after": "all"})
    if diff:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    RolePermission = apps.get_model("core", "RolePermission")
    RolePermission.objects.filter(permission_code__in=CELLS).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0039_treasury_transfer_and_cash_count_permissions")]

    operations = [migrations.RunPython(load, unload)]
