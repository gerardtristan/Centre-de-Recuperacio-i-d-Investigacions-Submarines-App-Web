"""T-M06-15 (RN-M06-17; 054): el comptador `version` de cada llicència i la marca de
`licence.expired` ja emès."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("licences", "0005_reminders"),
    ]

    operations = [
        migrations.AddField(
            model_name="licence",
            name="expired_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="caducitat notificada el"
            ),
        ),
        migrations.AddField(
            model_name="licence",
            name="version",
            field=models.PositiveIntegerField(default=1, verbose_name="versió"),
        ),
    ]
