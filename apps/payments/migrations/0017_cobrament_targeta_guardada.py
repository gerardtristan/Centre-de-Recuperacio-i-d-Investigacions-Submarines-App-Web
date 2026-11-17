"""T-M05b-15: la targeta guardada amb què s'obre cada intent i la marca d'una quota que una targeta
no ha pogut cobrar (una sola vegada per càrrec i targeta)."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0043_settings_vc11_permission"),
        ("payments", "0016_targeta_guardada"),
    ]

    operations = [
        migrations.CreateModel(
            name="SavedCardAttempt",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "attempt",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="payments.paymentattempt",
                    ),
                ),
                (
                    "card",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="payments.savedcard",
                    ),
                ),
            ],
            options={
                "verbose_name": "targeta d'un intent",
                "verbose_name_plural": "targetes dels intents",
            },
        ),
        migrations.CreateModel(
            name="SavedCardNotice",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("reason", models.TextField(verbose_name="motiu")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "card",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="payments.savedcard",
                    ),
                ),
                (
                    "charge",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="core.charge",
                    ),
                ),
            ],
            options={
                "verbose_name": "avís de quota no cobrada amb la targeta",
                "verbose_name_plural": "avisos de quotes no cobrades amb la targeta",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("charge", "card"), name="saved_card_notice_once"
                    )
                ],
            },
        ),
    ]
