"""T-M01-52 (091, RN-M01-107): un sol permís per al preu de tots els tipus de soci, també els
creats des de l'app, en lloc d'un per codi (AJ01-1 i AJ01-2 de la `core/0046`), i el permís de
la pantalla de tipus. El permís nou només el rep qui tenia el preu de tots dos tipus, amb l'abast
més estret dels dos: cap rol no guanya accés a preus que abans no podia canviar. Qui només en
tenia un el perd, i la versió de la matriu ho diu. Patró de la 0046 (060)."""

from django.db import migrations
from django.db.models import Max

OLD = (
    "settings.edit.members.annual_fee_cents.full",
    "settings.edit.members.annual_fee_cents.supporter",
)
PRICE = "settings.edit.members.annual_fee_cents"
TYPES = "settings.edit.members.membership_types"
NOTE = (
    "Socis: un sol permís per al preu de tots els tipus, només per a qui tenia el preu de tots "
    "dos tipus (qui només en tenia un el perd), i la pantalla de tipus (T-M01-52)."
)


def load(apps, schema_editor):
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    diff = []
    old = list(RolePermission.objects.filter(permission_code__in=OLD).select_related("role"))
    scopes = {}
    for cell in old:
        diff.append({"role": cell.role.code, "permission": cell.permission_code,
                     "before": cell.scope, "after": None})  # fmt: skip
        scopes.setdefault(cell.role.code, []).append(cell.scope)
    RolePermission.objects.filter(pk__in=[c.pk for c in old]).delete()
    # Tots dos preus, amb l'abast més estret («all» < «read» en ordre alfabètic: es tria a mà).
    cells = [
        (role, PRICE, "read" if "read" in found else "all")
        for role, found in scopes.items()
        if len(found) == len(OLD)
    ]
    cells += [("treasurer", TYPES, "all"), ("administrator", TYPES, "all")]
    for role, code, scope in cells:
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
    for cell in RolePermission.objects.filter(permission_code=PRICE):
        for code in OLD:
            RolePermission.objects.get_or_create(
                role=cell.role, permission_code=code, defaults={"scope": cell.scope}
            )
    RolePermission.objects.filter(permission_code__in=(PRICE, TYPES)).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0046_settings_members_permissions")]

    operations = [migrations.RunPython(load, unload)]
