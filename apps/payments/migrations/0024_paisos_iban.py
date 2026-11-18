"""P-123 (095, provisional fins que el banc ho confirmi): els països de l'IBAN admesos al mandat
són un ajust de pagaments, que de bon principi és tota la zona SEPA [A verificar: banc]. L'edita
el Tresorer [P-386], amb una versió nova de la matriu (060). Patró de la 0021.

La zona SEPA, pels codis de país de l'IBAN: els 27 de la UE; Islàndia, Liechtenstein i Noruega;
Suïssa, el Regne Unit, Mònaco, San Marino, el Vaticà, Andorra i Gibraltar; i Albània, Moldàvia,
Montenegro i Macedònia del Nord, que s'hi han afegit els darrers anys. Els territoris que fan
servir l'IBAN d'un altre país (per exemple, Åland amb FI) ja hi entren."""

from django.db import migrations
from django.db.models import Max

KEY = "payments.mandate_countries"
CODE = f"settings.edit.{KEY}"
SEPA = (
    "AD, AL, AT, BE, BG, CH, CY, CZ, DE, DK, EE, ES, FI, FR, GB, GI, GR, HR, HU, IE, IS, IT, LI, "
    "LT, LU, LV, MC, MD, ME, MK, MT, NL, NO, PL, PT, RO, SE, SI, SK, SM, VA"
)
NOTE = "Ajustos de pagaments: el Tresorer edita els països de l'IBAN admesos al mandat (P-123)."


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    Role = apps.get_model("core", "Role")
    RolePermission = apps.get_model("core", "RolePermission")
    PermissionMatrixVersion = apps.get_model("core", "PermissionMatrixVersion")
    Setting.objects.get_or_create(
        key=KEY,
        defaults={"module": "payments", "value_type": "text", "initial_value": SEPA,
                  "max_length": 400},
    )  # fmt: skip
    _cell, created = RolePermission.objects.get_or_create(
        role=Role.objects.get(code="treasurer"), permission_code=CODE, defaults={"scope": "all"}
    )
    if created:
        last = PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0
        diff = [{"role": "treasurer", "permission": CODE, "before": None, "after": "all"}]
        PermissionMatrixVersion.objects.create(number=last + 1, note=NOTE, diff=diff)


def unload(apps, schema_editor):
    """La cel·la i la versió de la matriu se'n van; l'ajust es queda, com a la 0021."""
    apps.get_model("core", "RolePermission").objects.filter(permission_code=CODE).delete()
    apps.get_model("core", "PermissionMatrixVersion").objects.filter(note=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0048_settings_members_types_permissions"),
        ("payments", "0023_permisos_095"),
    ]

    operations = [migrations.RunPython(load, unload)]
