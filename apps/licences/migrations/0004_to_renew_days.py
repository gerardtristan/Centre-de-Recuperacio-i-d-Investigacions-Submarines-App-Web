"""T-M06-09 (VC-41): `licences.to_renew_days`, els dies abans del venciment en què una llicència
surt «per renovar» (M06-5): 60, d'1 a 120. El permís per editar-lo arriba amb la T-M06-20."""

from django.db import migrations

KEY = "licences.to_renew_days"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={"module": "licences", "value_type": "integer", "initial_value": 60,
                  "min_value": 1, "max_value": 120},
    )  # fmt: skip


def unload(apps, schema_editor):
    """L'ajust es queda: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("licences", "0003_refund_proposal")]

    operations = [migrations.RunPython(load, unload)]
