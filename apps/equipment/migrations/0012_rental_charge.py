"""T-M03-11: el càrrec del lloguer al participant (RN-M03-11 [A validar: junta i tresorer, S-M03-03])
i el seu interruptor, `equipment.rental_charges_enabled`, apagat (D2: diners que veurà un soci).
No s'encén a producció sense la resposta; el permís d'editar-lo és del torn del nucli."""

import django.db.models.deletion
from django.db import migrations, models

KEY = "equipment.rental_charges_enabled"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={"module": "equipment", "value_type": "boolean", "initial_value": False},
    )


def unload(apps, schema_editor):
    """L'ajust es queda: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0071_equipment_settings_more_permissions"),
        ("equipment", "0011_unreturned_setting"),
    ]

    operations = [
        migrations.AddField(
            model_name="equipmentassignment",
            name="charge",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="core.charge",
                verbose_name="càrrec del lloguer",
            ),
        ),
        migrations.RunPython(load, unload),
    ]
