"""T-M05a-22: dies dels recordatoris de la campanya de mandats com a ajust (VC-11, RN-M05a-14:
7 i 14 dies des de la invitació, cadascun de 1 a 60). El permís per editar-lo és a `core/0043`."""

from django.db import migrations


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key="payments.mandate_campaign_reminder_days",
        defaults={"module": "payments", "value_type": "integer_list", "initial_value": [7, 14],
                  "min_value": 1, "max_value": 60},
    )  # fmt: skip


def unload(apps, schema_editor):
    """L'ajust es queda, com els de la 0004, la 0010 i la 0013: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("payments", "0013_retornats")]

    operations = [migrations.RunPython(load, unload)]
