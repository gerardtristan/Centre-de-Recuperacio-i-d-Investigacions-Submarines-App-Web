"""T-M05b-15b: si els avisos d'un resultat de la targeta guardada han sortit i, si un correu
falla, quants dies s'ha provat i quin va ser l'últim (un sol intent per dia, com a molt
`NOTICE_TRIES`). Les files d'abans (15a) ja es van avisar: s'hi afegeix `notified` a cert."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("payments", "0017_cobrament_targeta_guardada")]

    operations = [
        migrations.AddField(
            model_name="savedcardnotice",
            name="notified",
            field=models.BooleanField(default=True, verbose_name="avisat"),
        ),
        migrations.AlterField(
            model_name="savedcardnotice",
            name="notified",
            field=models.BooleanField(default=False, verbose_name="avisat"),
        ),
        migrations.AddField(
            model_name="savedcardnotice",
            name="tries",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="dies d'intents"),
        ),
        migrations.AddField(
            model_name="savedcardnotice",
            name="tried_on",
            field=models.DateField(null=True, verbose_name="últim intent"),
        ),
    ]
