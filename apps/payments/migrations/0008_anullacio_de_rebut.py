"""Anul·lació de rebut (045; T-M05b-29): només s'hi afegeixen files, també amb una consulta SQL
directa, com les anul·lacions de pagament de la 00. Desfer la migració treu la taula."""

import django.db.models.deletion
from django.db import migrations, models

APPEND_ONLY_SQL = """
CREATE FUNCTION payments_receiptcancellation_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Les anul·lacions de rebut no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;
CREATE TRIGGER payments_receiptcancellation_no_update_or_delete
    BEFORE UPDATE OR DELETE ON payments_receiptcancellation
    FOR EACH ROW EXECUTE FUNCTION payments_receiptcancellation_immutable();
CREATE TRIGGER payments_receiptcancellation_no_truncate
    BEFORE TRUNCATE ON payments_receiptcancellation
    FOR EACH STATEMENT EXECUTE FUNCTION payments_receiptcancellation_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER payments_receiptcancellation_no_truncate ON payments_receiptcancellation;
DROP TRIGGER payments_receiptcancellation_no_update_or_delete ON payments_receiptcancellation;
DROP FUNCTION payments_receiptcancellation_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0007_preferencia_targeta_campanya"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReceiptCancellation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("note", models.TextField(verbose_name="nota")),
                (
                    "cancelled_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="data de l'anul·lació"),
                ),
                (
                    "receipt",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cancellation",
                        to="payments.receipt",
                        verbose_name="rebut",
                    ),
                ),
            ],
            options={
                "verbose_name": "anul·lació de rebut",
                "verbose_name_plural": "anul·lacions de rebut",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("note__regex", "\\S")),
                        name="receipt_cancellation_note_required",
                    )
                ],
            },
        ),
        migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL),
    ]
