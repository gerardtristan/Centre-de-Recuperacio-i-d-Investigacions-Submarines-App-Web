"""T-M01-52 (091, RN-M01-107): les regles dels tipus de soci llegeixen atributs del tipus i no
el codi. El tipus de ple dret actual en té els valors d'avui (ple dret i 14 anys, RN-M01-64);
el simpatitzant es queda amb els valors per defecte (no és de ple dret, cap edat mínima)."""

from django.db import migrations, models


def load(apps, schema_editor):
    apps.get_model("members", "MembershipType").objects.filter(code="full").update(
        full_rights=True, min_age=14
    )


class Migration(migrations.Migration):
    dependencies = [("members", "0022_ajustos_01")]

    operations = [
        migrations.AddField(
            model_name="membershiptype",
            name="full_rights",
            field=models.BooleanField(default=False, verbose_name="de ple dret"),
        ),
        migrations.AddField(
            model_name="membershiptype",
            name="min_age",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="edat mínima"),
        ),
        migrations.RunPython(load, migrations.RunPython.noop),
    ]
