"""T-M05b-22c (VC-16; RN-M05b-09): els dies que s'espera una transferència abans de tancar
l'intent i enviar el recordatori (`payments.transfer_reminder_days`): 30, de 7 a 60. El permís,
`core/0059`."""

from django.db import migrations

KEY = "payments.transfer_reminder_days"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={"module": "payments", "value_type": "integer", "initial_value": 30,
                  "min_value": 7, "max_value": 60},
    )  # fmt: skip


def unload(apps, schema_editor):
    """L'ajust es queda: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0059_transfer_reminder_permission"),
        ("payments", "0028_treasurer_decision_origin"),
    ]

    operations = [migrations.RunPython(load, unload)]
