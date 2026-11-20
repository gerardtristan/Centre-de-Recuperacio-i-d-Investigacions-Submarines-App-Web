"""T-M06-11 (M06-6; RN-M06-12): els avisos de venciment al titular i el resum diari de la
secretaria (només INSERT), i l'ajust `licences.reminder_days` (VC-41: 60, 30 i 7; d'1 a 120)."""

import django.db.models.deletion
from django.db import migrations, models

KEY = "licences.reminder_days"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={"module": "licences", "value_type": "integer_list", "initial_value": [60, 30, 7],
                  "min_value": 1, "max_value": 120},
    )  # fmt: skip


def unload(apps, schema_editor):
    """L'ajust es queda: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("licences", "0004_to_renew_days"),
    ]

    operations = [
        migrations.CreateModel(
            name="LicenceReminderDigest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("day", models.DateField(verbose_name="dia")),
                ("days_before", models.PositiveSmallIntegerField(verbose_name="dies abans")),
                ("count", models.PositiveIntegerField(verbose_name="llicències")),
                ("sent_to", models.PositiveIntegerField(verbose_name="destinataris")),
                ("sent_at", models.DateTimeField(auto_now_add=True, verbose_name="enviat el")),
            ],
            options={
                "verbose_name": "resum d'avisos",
                "verbose_name_plural": "resums d'avisos",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("day", "days_before"), name="licences_digest_once"
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="LicenceReminder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("days_before", models.PositiveSmallIntegerField(verbose_name="dies abans")),
                ("sent_at", models.DateTimeField(auto_now_add=True, verbose_name="enviat el")),
                (
                    "licence",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reminders",
                        to="licences.licence",
                    ),
                ),
            ],
            options={
                "verbose_name": "avís de venciment",
                "verbose_name_plural": "avisos de venciment",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("licence", "days_before"), name="licences_reminder_once"
                    )
                ],
            },
        ),
        migrations.RunPython(load, unload),
    ]
