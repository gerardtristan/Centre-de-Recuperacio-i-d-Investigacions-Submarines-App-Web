"""T-M01-31 (052, 054; RN-M01-35 a 40): la còpia de lectura de la llicència del 06 a
`LicenceRecord` (`licence_ref`, `cancelled_on`, `source_version` i l'origen `licences`)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0065_equipment_settings_permissions"),
        ("members", "0025_renewal_notice_months"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="licencerecord",
            name="licencerecord_source_valid",
        ),
        migrations.AddField(
            model_name="licencerecord",
            name="cancelled_on",
            field=models.DateField(blank=True, null=True, verbose_name="cancel·lada el"),
        ),
        migrations.AddField(
            model_name="licencerecord",
            name="licence_ref",
            field=models.PositiveBigIntegerField(
                blank=True, null=True, unique=True, verbose_name="llicència del 06"
            ),
        ),
        migrations.AddField(
            model_name="licencerecord",
            name="source_version",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="versió del 06"),
        ),
        migrations.AlterField(
            model_name="licencerecord",
            name="source",
            field=models.CharField(
                choices=[
                    ("manual", "Manual"),
                    ("cluber", "Cluber"),
                    ("licences", "Llicències (06)"),
                ],
                max_length=10,
                verbose_name="origen",
            ),
        ),
        migrations.AddConstraint(
            model_name="licencerecord",
            constraint=models.CheckConstraint(
                condition=models.Q(("source__in", ["manual", "cluber", "licences"])),
                name="licencerecord_source_valid",
            ),
        ),
    ]
