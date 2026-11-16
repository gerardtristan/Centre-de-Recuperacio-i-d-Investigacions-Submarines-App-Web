"""Cel·les inicials d'A4, «Veure mètodes i mandats de tots els socis (IBAN emmascarat)» (M05a-4;
T-M05a-14): Tresorer i Administrador, amb una versió nova de la matriu (060). La Secretaria,
«Consulta» [A validar] al M05a-4, comença sense (P-193). Mateix patró que la 0033."""

from django.db import migrations
from django.db.models import Max

CODE = "payments.mandates.view"
NOTE = "A4, veure mètodes i mandats de tots els socis amb l'IBAN emmascarat (T-M05a-14)."
ROLES = ("treasurer", "administrator")


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    diff = []
    for role in ROLES:
        _cell, created = RolePermission.objects.get_or_create(
            role=Role.objects.get(code=role), permission_code=CODE, defaults={"scope": "all"}
        )
        if created:
            diff.append({"role": role, "permission": CODE, "before": None, "after": "all"})
    if diff:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    apps.get_model("core", "RolePermission").objects.filter(permission_code=CODE).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0034_payment_cancellation")]

    operations = [migrations.RunPython(load, unload)]
