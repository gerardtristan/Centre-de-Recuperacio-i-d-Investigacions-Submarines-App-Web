"""T-M09-13 (RN-M09-14, CA-M09-12): l'avís de marge baix (`LowMarginAlert`, només INSERT) i el
llindar `margin.low_margin_threshold_cents` (VC-31): 0 €, qualsevol import, també negatiu. El
permís per editar-lo és de la T-M09-26 (nucli)."""

import django.db.models.deletion
from django.db import migrations, models

KEY = "margin.low_margin_threshold_cents"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY, defaults={"module": "margin", "value_type": "cents", "initial_value": 0}
    )


def unload(apps, schema_editor):
    """L'ajust es queda: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0071_equipment_settings_more_permissions"),
        ("margins", "0004_period_event"),
    ]

    operations = [
        migrations.CreateModel(
            name="LowMarginAlert",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("margin_cents", models.BigIntegerField(verbose_name="marge previst (cèntims)")),
                ("threshold_cents", models.BigIntegerField(verbose_name="llindar (cèntims)")),
                ("sent_at", models.DateTimeField(auto_now_add=True, verbose_name="enviat")),
                (
                    "activity",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="activities.activity",
                        verbose_name="activitat",
                    ),
                ),
            ],
            options={
                "verbose_name": "avís de marge baix",
                "verbose_name_plural": "avisos de marge baix",
                "ordering": ["pk"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("margin_cents__lt", models.F("threshold_cents"))),
                        name="margins_low_margin_alert_below_threshold",
                    )
                ],
            },
        ),
        migrations.RunPython(load, unload),
    ]
