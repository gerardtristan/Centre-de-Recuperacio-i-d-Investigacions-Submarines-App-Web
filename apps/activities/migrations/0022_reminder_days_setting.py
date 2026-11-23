"""T-M02-21 (RN-M02-19; VC-23): `activities.reminder_days_before`, els dies abans de cada sessió o
sortida que surt el recordatori als inscrits confirmats: 2, de 0 (el mateix dia) a 14
[A validar: secretaria, S-M02-15]. El permís d'editar-lo és de la secretaria (`core/0075`)."""

from django.db import migrations

KEY = "activities.reminder_days_before"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={
            "module": "activities",
            "value_type": "integer",
            "initial_value": 2,
            "min_value": 0,
            "max_value": 14,
        },
    )


def unload(apps, schema_editor):
    """L'ajust es queda: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("activities", "0021_first_licence"),
        ("core", "0075_activities_reminder_days_permission"),
    ]

    operations = [migrations.RunPython(load, unload)]
