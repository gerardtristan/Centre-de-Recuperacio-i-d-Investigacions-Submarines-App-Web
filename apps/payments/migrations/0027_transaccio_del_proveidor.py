"""T-M05b-31: la referència de la transacció del proveïdor a la notificació i a l'intent, perquè
la conciliació de la liquidació trobi el pagament encara que el proveïdor no hi posi la nostra
ordre."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("payments", "0026_interruptors_proveidor")]

    operations = [
        migrations.AddField(
            model_name="providerevent",
            name="transaction_id",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="transacció del proveïdor"
            ),
        ),
        migrations.AddField(
            model_name="paymentattempt",
            name="provider_transaction_id",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="transacció del proveïdor"
            ),
        ),
    ]
