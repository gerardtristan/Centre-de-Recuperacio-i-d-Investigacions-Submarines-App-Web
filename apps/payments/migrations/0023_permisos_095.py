"""Cel·les de la 095 (060; RN-RP-08), amb una versió nova de la matriu:

- P-190: T8 (excloure una línia) i T10 (la llista «a revisar») tenen codi propi. Fins ara feien
  servir T4 i T1: T8 el rep qui té T4 i T10 qui té T1, amb el mateix abast. Cap rol no guanya ni
  perd accés; de bon principi, T8 el Tresorer i T10 el Tresorer i l'Administrador.
- P-193: la Secretaria té «Cons.» a A4 (només «té mètode: sí/no»).

Són aquí i no al `core` perquè A4 és del 05a i les tres cel·les van juntes (com la 0021)."""

from django.db import migrations
from django.db.models import Max

T1, T4, T8, T10 = "treasury.view", "treasury.reconcile", "treasury.exclude", "treasury.review"
A4 = "payments.mandates.view"
NEW = (T8, T10)
NOTE = (
    "T8 i T10 amb codi propi, amb les cel·les de T4 i T1 (P-190); la Secretaria, «Cons.» a A4 "
    "(P-193). Decisió 095."
)


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    cells = [
        (cell.role, new, cell.scope)
        for old, new in ((T4, T8), (T1, T10))
        for cell in RolePermission.objects.filter(permission_code=old).select_related("role")
    ]
    cells.append((Role.objects.get(code="secretary"), A4, "read"))
    diff = []
    for role, code, scope in cells:
        _cell, created = RolePermission.objects.get_or_create(
            role=role, permission_code=code, defaults={"scope": scope}
        )
        if created:
            diff.append({"role": role.code, "permission": code, "before": None, "after": scope})
    if diff:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    RolePermission = apps.get_model("core", "RolePermission")
    RolePermission.objects.filter(permission_code__in=NEW).delete()
    RolePermission.objects.filter(permission_code=A4, role__code="secretary").delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0048_settings_members_types_permissions"),
        ("payments", "0022_tancament_a_revisar"),
        ("treasury", "0007_t1_view_permission"),  # les cel·les de T1
    ]

    operations = [migrations.RunPython(load, unload)]
