"""Decisió del tresorer sobre un intent «a revisar» (T-M05b-16c; 097, P-82 opció C): el resultat
(«pagat» o «fallit») i més d'un tancament per intent, si torna «a revisar». La taula continua sent
només INSERT (0022): afegir la columna amb un valor per defecte no reescriu cap fila."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0023_permisos_095"),
    ]

    operations = [
        migrations.AddField(
            model_name="reviewclosure",
            name="outcome",
            field=models.CharField(
                choices=[("paid", "Pagat"), ("failed", "Fallit")],
                default="failed",
                max_length=12,
                verbose_name="decisió",
            ),
        ),
        migrations.AlterField(
            model_name="reviewclosure",
            name="attempt",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="review_closures",
                to="payments.paymentattempt",
                verbose_name="intent",
            ),
        ),
    ]
