"""T-M08-03 (RN-M08-02; P-487, decisió 105): la mida mínima d'un grup al dashboard, 3 d'inici,
de 2 a 10. El permís per editar-lo (d'inici, l'administrador) és del catàleg del nucli, amb els
de l'apartat «dashboard» (vegeu la 0001)."""

from django.db import migrations

KEY = "dashboard.min_group_size"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={
            "module": "dashboard",
            "value_type": "integer",
            "initial_value": 3,
            "min_value": 2,
            "max_value": 10,
        },
    )


def unload(apps, schema_editor):
    """L'ajust es queda: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("dashboard", "0001_help_texts")]

    operations = [migrations.RunPython(load, unload)]
