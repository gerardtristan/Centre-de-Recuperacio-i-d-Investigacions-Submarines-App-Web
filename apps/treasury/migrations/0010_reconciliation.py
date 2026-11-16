"""Conciliació confirmada (T-M04-12; M04-6): només s'hi afegeixen files, també amb una consulta
SQL directa (CK C8), com els moviments (0006). Els càrrecs casats (taula intermèdia) tampoc no
es canvien ni s'esborren: desfer una conciliació serà una fila nova (045).
Desfer la migració treu la taula."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

APPEND_ONLY_SQL = """
CREATE FUNCTION treasury_reconciliation_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Les conciliacions no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;
""" + "".join(
    f"""
CREATE TRIGGER {table}_no_update_or_delete
    BEFORE UPDATE OR DELETE ON {table}
    FOR EACH ROW EXECUTE FUNCTION treasury_reconciliation_immutable();
CREATE TRIGGER {table}_no_truncate
    BEFORE TRUNCATE ON {table}
    FOR EACH STATEMENT EXECUTE FUNCTION treasury_reconciliation_immutable();
"""
    for table in ("treasury_reconciliation", "treasury_reconciliation_matched_charges")
)

REVERSE_SQL = """
DROP TRIGGER treasury_reconciliation_matched_charges_no_truncate
    ON treasury_reconciliation_matched_charges;
DROP TRIGGER treasury_reconciliation_matched_charges_no_update_or_delete
    ON treasury_reconciliation_matched_charges;
DROP TRIGGER treasury_reconciliation_no_truncate ON treasury_reconciliation;
DROP TRIGGER treasury_reconciliation_no_update_or_delete ON treasury_reconciliation;
DROP FUNCTION treasury_reconciliation_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0032_settings_safety_net_give_up_permission"),
        ("treasury", "0009_statement_line_state"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Reconciliation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "confirmed_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="data de la confirmació"),
                ),
                (
                    "confirmed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="confirmada per",
                    ),
                ),
                (
                    "matched_charges",
                    models.ManyToManyField(
                        related_name="+", to="core.charge", verbose_name="càrrecs casats"
                    ),
                ),
                (
                    "statement_line",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reconciliations",
                        to="core.importline",
                        verbose_name="línia",
                    ),
                ),
            ],
            options={
                "verbose_name": "conciliació",
                "verbose_name_plural": "conciliacions",
            },
        ),
        migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL),
    ]
