"""T-M02-28b (VC-25; RN-M02-24): l'enllaç per defecte a la previsió marítima,
`activities.marine_forecast_url` (URL https). Inicial: el web públic del Meteocat; l'adreça exacta
de la pàgina de previsió marítima la posa l'administrador des dels ajustos (P-505). El permís per
editar-lo és del nucli."""

from django.db import migrations

KEY = "activities.marine_forecast_url"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={"module": "activities", "value_type": "url",
                  "initial_value": "https://www.meteo.cat/", "max_length": 300},
    )  # fmt: skip


def unload(apps, schema_editor):
    """L'ajust es queda: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("activities", "0021_first_licence")]

    operations = [migrations.RunPython(load, unload)]
