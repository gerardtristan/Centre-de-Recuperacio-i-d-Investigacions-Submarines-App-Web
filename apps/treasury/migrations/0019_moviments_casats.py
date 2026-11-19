"""Moviments casats d'una conciliació (T-M04-12f; CA-T07.2): la taula intermèdia només admet
INSERT, també amb una consulta SQL directa, com la dels càrrecs (0010, que en reutilitza la
funció). Desfer la migració es rebutja si la taula té alguna fila: no s'esborra cap conciliació."""

from django.db import migrations, models

APPEND_ONLY_SQL = """
CREATE TRIGGER treasury_reconciliation_matched_movements_no_update_or_delete
    BEFORE UPDATE OR DELETE ON treasury_reconciliation_matched_movements
    FOR EACH ROW EXECUTE FUNCTION treasury_reconciliation_immutable();
CREATE TRIGGER treasury_reconciliation_matched_movements_no_truncate
    BEFORE TRUNCATE ON treasury_reconciliation_matched_movements
    FOR EACH STATEMENT EXECUTE FUNCTION treasury_reconciliation_immutable();
"""

REVERSE_SQL = """
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM treasury_reconciliation_matched_movements) THEN
        RAISE EXCEPTION 'Hi ha conciliacions amb moviments casats: no es desfà la migració.';
    END IF;
END;
$$;
DROP TRIGGER treasury_reconciliation_matched_movements_no_truncate
    ON treasury_reconciliation_matched_movements;
DROP TRIGGER treasury_reconciliation_matched_movements_no_update_or_delete
    ON treasury_reconciliation_matched_movements;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("treasury", "0018_tancament_liquidacio"),
    ]

    operations = [
        migrations.AddField(
            model_name="reconciliation",
            name="matched_movements",
            field=models.ManyToManyField(
                related_name="+", to="treasury.movement", verbose_name="moviments casats"
            ),
        ),
        migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL),
    ]
