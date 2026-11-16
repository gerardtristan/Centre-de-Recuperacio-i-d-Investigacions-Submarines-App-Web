"""VC-17 (decisió 093; T-M05b-28): les hores que la xarxa de seguretat torna a provar una ordre
que no pot tancar abans de deixar-la «a revisar» (L-M05b-01), que substitueixen la constant del
codi. Valor inicial 24, el que feia servir la constant; rang 24 a 168 (P-102). No afecta diners
ni té data d'entrada en vigor. El permís és a `core/0032`."""

from django.db import migrations

KEY = "payments.safety_net_give_up_hours"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={"module": "payments", "value_type": "integer", "initial_value": 24,
                  "min_value": 24, "max_value": 168},
    )  # fmt: skip


def unload(apps, schema_editor):
    """L'ajust es queda, com a la 0004: un valor canviat té historial, que no s'esborra mai, i
    tornar a aplicar la migració reaprofita la mateixa fila."""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0032_settings_safety_net_give_up_permission"),
        ("payments", "0004_vc17_settings"),
    ]

    operations = [migrations.RunPython(load, unload)]
