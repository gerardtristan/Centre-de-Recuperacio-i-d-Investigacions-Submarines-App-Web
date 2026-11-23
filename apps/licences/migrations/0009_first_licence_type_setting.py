"""Ajust del tipus de la primera llicència d'un alumne nou (P-530; RN-M06-28; T-M02-51a). Buit per
defecte: fins que la secretaria i el tresorer el triïn, el 02 no crea cap llicència inclosa (és
diners i ho veu l'alumne: l'opció conservadora, D2). Només la clau; la comprovació (un tipus
actiu) la registra el 02, que és qui el fa servir."""

from django.db import migrations

KEY = "licences.first_licence_type"


def seed(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={
            "module": "licences",
            "value_type": "text",
            "initial_value": "",
            "max_length": 80,
        },
    )


def unseed(apps, schema_editor):
    """L'ajust es queda (en guarda l'historial)."""


class Migration(migrations.Migration):
    dependencies = [("licences", "0008_first_licence")]

    operations = [migrations.RunPython(seed, unseed)]
