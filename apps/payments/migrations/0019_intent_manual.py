"""P-12: l'intent «manual», que obre el sistema per emetre el rebut d'un pagament registrat a
mà (`transfers.on_payment_saved`). Cap usuari no el tria (`attempts.SCREEN_METHODS`)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0018_avis_targeta_notificat"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="paymentattempt",
            name="payment_attempt_method_valid",
        ),
        migrations.AlterField(
            model_name="paymentattempt",
            name="method",
            field=models.CharField(
                choices=[
                    ("card", "Targeta"),
                    ("bizum", "Bizum"),
                    ("transfer", "Transferència"),
                    ("direct_debit", "Domiciliació"),
                    ("saved_card", "Targeta guardada"),
                    ("manual", "Manual"),
                ],
                max_length=12,
                verbose_name="mètode",
            ),
        ),
        migrations.AddConstraint(
            model_name="paymentattempt",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    (
                        "method__in",
                        ["card", "bizum", "transfer", "direct_debit", "saved_card", "manual"],
                    )
                ),
                name="payment_attempt_method_valid",
            ),
        ),
    ]
