"""T-M05a-23 (RN-M05a-20; CA-M05a-20): quants dies abans que caduqui la targeta guardada surt
l'avís al soci, com a ajust (VC-48). Valor inicial 30 dies (addenda de la 060 al 05a) [A validar:
tresorer]; de 1 a 90. El permís per editar-lo encara no és al catàleg (cal una migració de
`core`)."""

from django.db import migrations

KEY = "payments.card_expiry_notice_days"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={"module": "payments", "value_type": "integer", "initial_value": 30,
                  "min_value": 1, "max_value": 90},
    )  # fmt: skip


def unload(apps, schema_editor):
    """L'ajust es queda, com els altres dels pagaments: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("payments", "0019_reintents_targeta_guardada")]

    operations = [migrations.RunPython(load, unload)]
