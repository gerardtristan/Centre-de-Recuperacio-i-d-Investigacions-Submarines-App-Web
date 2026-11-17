"""T-M04-20 (addendes de la 050 i la 053): tipus `expense` i `other_income` i la data de valor
original dels moviments d'origen extern que entren al període obert (RN-T31). Afegir una
columna buida no modifica cap fila: els activadors de només INSERT (0006) no hi intervenen."""

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0041_events"),
        ("treasury", "0014_cash_count"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="movement",
            name="movement_kind_valid",
        ),
        migrations.AddField(
            model_name="movement",
            name="original_value_date",
            field=models.DateField(blank=True, null=True, verbose_name="data de valor original"),
        ),
        migrations.AlterField(
            model_name="movement",
            name="kind",
            field=models.CharField(
                choices=[
                    ("income", "Ingrés de cobrament"),
                    ("fee", "Comissió"),
                    ("refund", "Devolució"),
                    ("return", "Retorn"),
                    ("transfer", "Traspàs"),
                    ("cash_adjustment", "Ajust d'arqueig"),
                    ("reversal", "Contramoviment"),
                    ("expense", "Despesa"),
                    ("other_income", "Altres ingressos"),
                ],
                max_length=15,
                verbose_name="tipus",
            ),
        ),
        migrations.AddConstraint(
            model_name="movement",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    (
                        "kind__in",
                        [
                            "income",
                            "fee",
                            "refund",
                            "return",
                            "transfer",
                            "cash_adjustment",
                            "reversal",
                            "expense",
                            "other_income",
                        ],
                    )
                ),
                name="movement_kind_valid",
            ),
        ),
    ]
