"""T-M02-13 (RN-M02-09; VC-22): `activities.offer_accept_hours`, les hores per acceptar una plaça
oferta de la llista d'espera: 48, de 12 a 168. La pantalla d'ajustos del 02 és de la T-M02-28."""

from django.db import migrations

KEY = "activities.offer_accept_hours"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={
            "module": "activities",
            "value_type": "integer",
            "initial_value": 48,
            "min_value": 12,
            "max_value": 168,
        },
    )


def unload(apps, schema_editor):
    """L'ajust es queda: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("activities", "0008_enrolment")]

    operations = [migrations.RunPython(load, unload)]
