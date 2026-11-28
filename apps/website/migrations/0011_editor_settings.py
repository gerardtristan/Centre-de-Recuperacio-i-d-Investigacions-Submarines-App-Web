"""T-M07-04 (decisió 106, addenda M07): els ajustos nous de l'editor. YouTube i el flux de
revisió comencen apagats (D2: YouTube no s'encén a producció sense P-574; el flux de revisió és
de la T-M07-26). El desat automàtic és de la T-M07-06b i la mida de les pujades, de la T-M07-07."""

from django.db import migrations

SETTINGS = {
    "website.youtube_enabled": {"value_type": "boolean", "initial_value": False},
    "website.review_flow_enabled": {"value_type": "boolean", "initial_value": False},
    "website.autosave_seconds": {
        "value_type": "integer",
        "initial_value": 20,
        "min_value": 5,
        "max_value": 120,
    },
    "website.upload_max_mb": {
        "value_type": "integer",
        "initial_value": 10,
        "min_value": 1,
        "max_value": 25,
    },
}


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key, fields in SETTINGS.items():
        Setting.objects.get_or_create(key=key, defaults={"module": "website", **fields})


def unload(apps, schema_editor):
    """Els ajustos es queden: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("website", "0010_tutorials")]

    operations = [migrations.RunPython(load, unload)]
