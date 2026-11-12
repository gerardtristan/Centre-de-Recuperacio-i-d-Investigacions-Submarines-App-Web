"""Categoria de l'anul·lació d'un càrrec (T-M01-40; RN-M01-72): «exempció» o cap. Només un càrrec
anul·lat en pot tenir."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0026_person_reference_label"),
    ]

    operations = [
        migrations.AddField(
            model_name="charge",
            name="cancel_category",
            field=models.CharField(
                blank=True,
                choices=[("exemption", "Exempció")],
                max_length=12,
                verbose_name="categoria de l'anul·lació",
            ),
        ),
        migrations.AddConstraint(
            model_name="charge",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("cancel_category", ""),
                    models.Q(("cancel_category", "exemption"), ("status", "cancelled")),
                    _connector="OR",
                ),
                name="charge_cancel_category_valid",
            ),
        ),
    ]
