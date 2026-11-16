"""Desfeta d'una conciliació (T-M04-12; 045): només s'hi afegeixen files, també amb una consulta
SQL directa, com les conciliacions (0010). Desfer la migració treu la taula."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

APPEND_ONLY_SQL = """
CREATE FUNCTION treasury_reconciliationundo_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Les desfetes de conciliació no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;
CREATE TRIGGER treasury_reconciliationundo_no_update_or_delete
    BEFORE UPDATE OR DELETE ON treasury_reconciliationundo
    FOR EACH ROW EXECUTE FUNCTION treasury_reconciliationundo_immutable();
CREATE TRIGGER treasury_reconciliationundo_no_truncate
    BEFORE TRUNCATE ON treasury_reconciliationundo
    FOR EACH STATEMENT EXECUTE FUNCTION treasury_reconciliationundo_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER treasury_reconciliationundo_no_truncate ON treasury_reconciliationundo;
DROP TRIGGER treasury_reconciliationundo_no_update_or_delete ON treasury_reconciliationundo;
DROP FUNCTION treasury_reconciliationundo_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("treasury", "0011_statement_line_exclusion"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ReconciliationUndo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("reason", models.TextField(verbose_name="motiu")),
                (
                    "undone_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="data de la desfeta"),
                ),
                (
                    "reconciliation",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="undo",
                        to="treasury.reconciliation",
                        verbose_name="conciliació",
                    ),
                ),
                (
                    "undone_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="desfeta per",
                    ),
                ),
            ],
            options={
                "verbose_name": "desfeta de conciliació",
                "verbose_name_plural": "desfetes de conciliació",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("reason__regex", "\\S")),
                        name="reconciliation_undo_reason_required",
                    )
                ],
            },
        ),
        migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL),
    ]
