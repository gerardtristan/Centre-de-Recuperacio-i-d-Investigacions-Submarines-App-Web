# T-M02-20 (P-M02-G; S-M02-14): resultats ambientals d'una sortida (un per sortida).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("activities", "0016_instructor_requirements_mode"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EnvironmentalResult",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "waste_grams",
                    models.PositiveIntegerField(
                        blank=True, null=True, verbose_name="residus recollits (grams)"
                    ),
                ),
                ("species", models.TextField(blank=True, verbose_name="espècies observades")),
                ("observations", models.TextField(blank=True, verbose_name="observacions")),
                ("recorded_at", models.DateTimeField(verbose_name="registrat el")),
                (
                    "activity",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="environmental_result",
                        to="activities.activity",
                        verbose_name="sortida",
                    ),
                ),
                (
                    "recorded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="registrat per",
                    ),
                ),
            ],
            options={
                "verbose_name": "resultats ambientals",
                "verbose_name_plural": "resultats ambientals",
            },
        ),
    ]
