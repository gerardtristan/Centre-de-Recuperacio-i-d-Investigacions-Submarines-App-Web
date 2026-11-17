"""T-M05a-26 (RN-M05a-23; addenda de la 060 al 05a): la targeta guardada admet l'estat «denegada»
(definitiva, RN-M05b-28)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0043_settings_vc11_permission"),
        ("payments", "0020_avis_caducitat_targeta"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="savedcard",
            name="saved_card_status_valid",
        ),
        migrations.AlterField(
            model_name="savedcard",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "activa"),
                    ("removed", "esborrada"),
                    ("expired", "caducada"),
                    ("declined", "denegada"),
                ],
                default="active",
                max_length=10,
                verbose_name="estat",
            ),
        ),
        migrations.AddConstraint(
            model_name="savedcard",
            constraint=models.CheckConstraint(
                condition=models.Q(("status__in", ["active", "removed", "expired", "declined"])),
                name="saved_card_status_valid",
            ),
        ),
    ]
