"""T-M09-16c (RN-M09-15 i 28): la durada dels períodes nous, `margin.period_length` (VC-32):
mensual d'inici [A validar: tresorer, S-M09-05], o trimestral. El permís per editar-la és de la
T-M09-26 (nucli)."""

from django.db import migrations

KEY = "margin.period_length"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={"module": "margin", "value_type": "choice", "initial_value": "monthly",
                  "choices": ["monthly", "quarterly"]},
    )  # fmt: skip


def unload(apps, schema_editor):
    """L'ajust es queda: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("margins", "0005_low_margin_alert")]

    operations = [migrations.RunPython(load, unload)]
