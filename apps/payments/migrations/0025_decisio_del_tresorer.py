"""Decisió del tresorer sobre un intent «a revisar» (T-M05b-16c; 097, P-82 opció C): el resultat
(«pagat» o «fallit»), el motiu de l'intent en tancar-lo i més d'un tancament per intent, si torna
«a revisar»; i el codi del motiu «a revisar» de l'intent (`review_code`), que les guardes fan servir
en lloc del text (061). Un intent que ja hi era queda amb el codi «altre».

Els tancaments que ja hi hagi (T-M05b-16b) no van triar res: queden «sense decisió» i amb el
motiu que té ara el seu intent, que encara és «a revisar» (no s'ha pogut tornar a canviar). La
taula és només INSERT (0022): les columnes s'afegeixen amb un valor per defecte, que no reescriu
cap fila, i la còpia del motiu desactiva el disparador només durant l'UPDATE. Sense valor per
defecte al model: cada tancament nou diu la decisió."""

import django.db.models.deletion
from django.db import migrations, models

COPY_REASON_SQL = """
ALTER TABLE payments_reviewclosure DISABLE TRIGGER payments_reviewclosure_no_update_or_delete;
UPDATE payments_reviewclosure AS closure
    SET review_reason = attempt.review_reason
    FROM payments_paymentattempt AS attempt
    WHERE attempt.id = closure.attempt_id;
ALTER TABLE payments_reviewclosure ENABLE TRIGGER payments_reviewclosure_no_update_or_delete;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0024_paisos_iban"),
    ]

    operations = [
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
        migrations.AddField(
            model_name="reviewclosure",
            name="outcome",
            field=models.CharField(
                choices=[("paid", "Pagat"), ("failed", "Fallit"), ("undecided", "Sense decisió")],
                default="undecided",
                max_length=12,
                verbose_name="decisió",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="reviewclosure",
            name="review_reason",
            field=models.TextField(blank=True, default="", verbose_name="motiu de la revisió"),
            preserve_default=False,
        ),
        migrations.RunSQL(COPY_REASON_SQL, migrations.RunSQL.noop),
        migrations.AddField(
            model_name="paymentattempt",
            name="review_code",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "altre"),
                    ("amount", "l'import o la moneda no quadren"),
                    ("duplicate", "pagament duplicat"),
                    ("cancelled", "càrrec anul·lat"),
                    ("in_flight", "un altre intent en curs"),
                    ("returned", "càrrec retornat"),
                    ("confirmed", "el proveïdor n'ha confirmat el cobrament"),
                ],
                default="",
                max_length=12,
                verbose_name="codi de la revisió",
            ),
            preserve_default=False,
        ),
    ]
