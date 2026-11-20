"""T-M02-03c (M02-6, «Valors configurables»): els ajustos que llegeixen els serveis en crear una
activitat. `activities.default_payment_window_hours` (VC-21): 72 hores, de 24 a 240;
`activities.default_requirements_mode` (VC-24): «avís» (`warn`) o «bloqueig» (`block`). Els
permisos per editar-los arriben amb la pantalla d'ajustos del 02 (T-M02-28): fins llavors,
l'apartat «activities» no surt a cap pantalla."""

from django.db import migrations

SETTINGS = {
    "activities.default_payment_window_hours": {
        "value_type": "integer",
        "initial_value": 72,
        "min_value": 24,
        "max_value": 240,
    },
    "activities.default_requirements_mode": {
        "value_type": "choice",
        "initial_value": "warn",
        "choices": ["warn", "block"],
    },
}


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key, fields in SETTINGS.items():
        Setting.objects.get_or_create(key=key, defaults={"module": "activities", **fields})


def unload(apps, schema_editor):
    """Els ajustos es queden: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0013_business_settings"),
        ("activities", "0003_activity_session_programmeblock"),
    ]

    operations = [migrations.RunPython(load, unload)]
