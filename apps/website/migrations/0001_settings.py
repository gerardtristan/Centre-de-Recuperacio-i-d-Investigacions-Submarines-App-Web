"""T-M07-03 (M07-6, «Valors configurables»): els ajustos del 07. El butlletí i el contacte
comencen apagats (D2: no s'encenen a producció sense P-42 i P-486). Les dades de contacte del
club comencen buides (S-M07-03, [A validar: secretaria]); el límit de 500 caràcters és nostre.
Els permisos per editar-los (`settings.section.website` i `settings.edit.website.*`, WP1 o
l'administrador) són del catàleg del nucli (T-M07-02): fins llavors, l'apartat «website» no surt
a cap pantalla (`_section_or_404`)."""

from django.db import migrations

SETTINGS = {
    "website.home_activities_count": {
        "value_type": "integer",
        "initial_value": 6,
        "min_value": 1,
        "max_value": 12,
    },
    "website.news_on_home": {
        "value_type": "integer",
        "initial_value": 3,
        "min_value": 0,
        "max_value": 10,
    },
    "website.newsletter_enabled": {"value_type": "boolean", "initial_value": False},
    "website.newsletter_confirm_hours": {
        "value_type": "integer",
        "initial_value": 48,
        "min_value": 1,
        "max_value": 168,
    },
    "website.contact_enabled": {"value_type": "boolean", "initial_value": False},
    "website.contact_retention_months": {
        "value_type": "integer",
        "initial_value": 6,
        "min_value": 1,
        "max_value": 24,
    },
    "website.club_contact": {"value_type": "text", "initial_value": "", "max_length": 500},
}


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key, fields in SETTINGS.items():
        Setting.objects.get_or_create(key=key, defaults={"module": "website", **fields})


def unload(apps, schema_editor):
    """Els ajustos es queden: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("core", "0013_business_settings")]

    operations = [migrations.RunPython(load, unload)]
