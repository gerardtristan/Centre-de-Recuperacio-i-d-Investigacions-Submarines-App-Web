"""Llengua preferida de la persona i llengua dels textos legals (T-M01-09b, decisió 061).

Les files que ja hi ha queden en català. Una traducció serà una fila més de la mateixa versió.
"""

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_charges_and_departments"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="legaltext",
            name="legaltext_unique_version",
        ),
        migrations.AddField(
            model_name="legaltext",
            name="language",
            field=models.CharField(default="ca", max_length=7, verbose_name="llengua"),
        ),
        migrations.AddField(
            model_name="person",
            name="preferred_language",
            field=models.CharField(default="ca", max_length=7, verbose_name="llengua preferida"),
        ),
        migrations.AddConstraint(
            model_name="legaltext",
            constraint=models.UniqueConstraint(
                fields=("kind", "version", "language"), name="legaltext_unique_version_language"
            ),
        ),
    ]
