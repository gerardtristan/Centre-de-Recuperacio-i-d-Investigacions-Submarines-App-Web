"""T-M06-04 (M06-6, valors configurables): els ajustos que llegeix la sol·licitud.
`licences.non_members_enabled` (VC-39) i `licences.day_enabled` (VC-40) desactivats;
`licences.next_year_opens_on` (VC-42) l'1/12, de l'1/10 al 31/12. La llicència d'un dia
s'activa amb la T-M06-21 (058). Els permisos per editar-los arriben amb la T-M06-20: fins
llavors, l'apartat «licences» no surt a cap pantalla (`_section_or_404`)."""

from django.db import migrations

SETTINGS = {
    "licences.non_members_enabled": {"value_type": "boolean", "initial_value": False},
    "licences.day_enabled": {"value_type": "boolean", "initial_value": False},
    "licences.next_year_opens_on": {
        "value_type": "day_month",
        "initial_value": "12-01",
        "min_value": 1001,
        "max_value": 1231,
    },  # fmt: skip
}


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key, fields in SETTINGS.items():
        Setting.objects.get_or_create(key=key, defaults={"module": "licences", **fields})


def unload(apps, schema_editor):
    """Els ajustos es queden: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("core", "0060_licences_permissions"), ("licences", "0001_initial")]

    operations = [migrations.RunPython(load, unload)]
