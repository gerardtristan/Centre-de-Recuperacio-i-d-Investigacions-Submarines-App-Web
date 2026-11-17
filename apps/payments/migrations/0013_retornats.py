"""T-M05b-12: codi i data del retorn al rebut domiciliat (M05b-6) i el màxim d'intents per
domiciliació per càrrec (VC-16, RN-M05b-15: 2, d'1 a 3). Com a la 0010, el permís per editar-lo
arriba amb la pantalla de la VC-16; fins llavors només l'edita qui té tot l'apartat de pagaments."""

from django.db import migrations, models


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key="payments.max_direct_debit_attempts",
        defaults={"module": "payments", "value_type": "integer", "initial_value": 2,
                  "min_value": 1, "max_value": 3},
    )  # fmt: skip


def unload(apps, schema_editor):
    """L'ajust es queda, com els de la 0004 i la 0010: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0012_devolucions"),
    ]

    operations = [
        migrations.AddField(
            model_name="directdebititem",
            name="return_reason_code",
            field=models.CharField(blank=True, max_length=4, verbose_name="codi del retorn"),
        ),
        migrations.AddField(
            model_name="directdebititem",
            name="returned_on",
            field=models.DateField(blank=True, null=True, verbose_name="retornat el"),
        ),
        migrations.RunPython(load, unload),
    ]
