"""T-M05b-10: empremta i versió de l'últim fitxer pain.008 de la remesa (el fitxer no es desa)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0010_remeses"),
    ]

    operations = [
        migrations.AddField(
            model_name="directdebitremittance",
            name="file_format",
            field=models.CharField(blank=True, max_length=20, verbose_name="format del fitxer"),
        ),
        migrations.AddField(
            model_name="directdebitremittance",
            name="file_hash",
            field=models.CharField(blank=True, max_length=64, verbose_name="empremta del fitxer"),
        ),
    ]
