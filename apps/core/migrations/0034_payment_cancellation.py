"""Anul·lació de pagament (045; T-M04-12c): només s'hi afegeixen files, també amb una consulta
SQL directa, com les conciliacions de la 04. Desfer la migració treu la taula."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

APPEND_ONLY_SQL = """
CREATE FUNCTION core_paymentcancellation_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Les anul·lacions de pagament no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;
CREATE TRIGGER core_paymentcancellation_no_update_or_delete
    BEFORE UPDATE OR DELETE ON core_paymentcancellation
    FOR EACH ROW EXECUTE FUNCTION core_paymentcancellation_immutable();
CREATE TRIGGER core_paymentcancellation_no_truncate
    BEFORE TRUNCATE ON core_paymentcancellation
    FOR EACH STATEMENT EXECUTE FUNCTION core_paymentcancellation_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER core_paymentcancellation_no_truncate ON core_paymentcancellation;
DROP TRIGGER core_paymentcancellation_no_update_or_delete ON core_paymentcancellation;
DROP FUNCTION core_paymentcancellation_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0033_treasury_reconcile_permission"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PaymentCancellation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("reason", models.TextField(verbose_name="motiu")),
                (
                    "cancelled_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="data de l'anul·lació"),
                ),
                (
                    "cancelled_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="anul·lat per",
                    ),
                ),
                (
                    "payment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cancellation",
                        to="core.payment",
                        verbose_name="pagament",
                    ),
                ),
            ],
            options={
                "verbose_name": "anul·lació de pagament",
                "verbose_name_plural": "anul·lacions de pagament",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("reason__regex", "\\S")),
                        name="payment_cancellation_reason_required",
                    )
                ],
            },
        ),
        migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL),
    ]
