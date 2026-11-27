"""T-M07-23 (decisió 106, RN-M07-09): el text de l'avís del bloc de YouTube és un ajust, perquè
el valida la junta (P-574). Fins llavors, `website.youtube_enabled` continua apagat. El permís per
editar-lo (`settings.edit.website.youtube_notice`) és del catàleg del nucli."""

from django.db import migrations

SETTINGS = {
    "website.youtube_notice": {
        "value_type": "text",
        "initial_value": "En prémer, es carrega YouTube (Google)",
        "max_length": 200,
    },
}


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key, fields in SETTINGS.items():
        Setting.objects.get_or_create(key=key, defaults={"module": "website", **fields})


def unload(apps, schema_editor):
    """Els ajustos es queden: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("website", "0016_scheduled_actions")]

    operations = [migrations.RunPython(load, unload)]
