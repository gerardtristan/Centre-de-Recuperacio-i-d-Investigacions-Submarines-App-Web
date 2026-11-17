"""T-M05b-15b: si els avisos d'un resultat de la targeta guardada han sortit; si un correu
falla, queda fals i la tasca diària ho torna a provar."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("payments", "0017_cobrament_targeta_guardada")]

    operations = [
        migrations.AddField(
            model_name="savedcardnotice",
            name="notified",
            field=models.BooleanField(default=False, verbose_name="avisat"),
        ),
    ]
