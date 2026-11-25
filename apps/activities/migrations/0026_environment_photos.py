"""T-M02-20 (CA-M02-22; P-41, oberta): `EnvironmentalPhoto` i l'interruptor
`activities.environment_photos_enabled`, apagat (D2: imatges de persones). No s'encén a producció
sense la resposta de la P-41."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

KEY = "activities.environment_photos_enabled"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={"module": "activities", "value_type": "boolean", "initial_value": False},
    )


def unload(apps, schema_editor):
    """L'ajust es queda: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("activities", "0025_card_photos"),
        ("core", "0083_environment_photo_kind"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EnvironmentalPhoto",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "content_type",
                    models.CharField(max_length=100, verbose_name="tipus de contingut"),
                ),
                ("author", models.CharField(max_length=120, verbose_name="autor")),
                (
                    "usage_permission",
                    models.BooleanField(default=False, verbose_name="permís d'ús de l'autor"),
                ),
                (
                    "shows_people",
                    models.BooleanField(default=False, verbose_name="s'hi veuen persones"),
                ),
                (
                    "people_consent",
                    models.BooleanField(default=False, verbose_name="consentiment de les persones"),
                ),
                ("publishable", models.BooleanField(default=False, verbose_name="publicable")),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Activa"), ("retired", "Retirada")],
                        default="active",
                        max_length=10,
                        verbose_name="estat",
                    ),
                ),
                (
                    "retired_reason",
                    models.CharField(
                        blank=True, max_length=300, verbose_name="motiu de la retirada"
                    ),
                ),
                ("uploaded_at", models.DateTimeField(auto_now_add=True, verbose_name="pujada")),
                (
                    "file",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="core.privatefile",
                        verbose_name="fitxer",
                    ),
                ),
                (
                    "result",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="photos",
                        to="activities.environmentalresult",
                        verbose_name="resultats",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="pujada per",
                    ),
                ),
            ],
            options={
                "verbose_name": "foto d'una sortida de medi ambient",
                "verbose_name_plural": "fotos de les sortides de medi ambient",
                "ordering": ["uploaded_at", "pk"],
            },
        ),
        migrations.RunPython(load, unload),
    ]
