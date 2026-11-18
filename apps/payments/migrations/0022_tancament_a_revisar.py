"""Tancament d'un intent «a revisar» (T-M05b-16b; P-82): només s'hi afegeixen files, també amb una
consulta SQL directa, com les anul·lacions de rebut (0008). Desfer la migració treu la taula."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

APPEND_ONLY_SQL = """
CREATE FUNCTION payments_reviewclosure_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Els tancaments d''«a revisar» no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;
CREATE TRIGGER payments_reviewclosure_no_update_or_delete
    BEFORE UPDATE OR DELETE ON payments_reviewclosure
    FOR EACH ROW EXECUTE FUNCTION payments_reviewclosure_immutable();
CREATE TRIGGER payments_reviewclosure_no_truncate
    BEFORE TRUNCATE ON payments_reviewclosure
    FOR EACH STATEMENT EXECUTE FUNCTION payments_reviewclosure_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER payments_reviewclosure_no_truncate ON payments_reviewclosure;
DROP TRIGGER payments_reviewclosure_no_update_or_delete ON payments_reviewclosure;
DROP FUNCTION payments_reviewclosure_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0021_codis_de_retorn"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ReviewClosure",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("note", models.TextField(verbose_name="nota")),
                ("closed_at", models.DateTimeField(auto_now_add=True, verbose_name="tancat el")),
                (
                    "attempt",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="review_closure",
                        to="payments.paymentattempt",
                        verbose_name="intent",
                    ),
                ),
                (
                    "closed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="tancat per",
                    ),
                ),
            ],
            options={
                "verbose_name": "tancament d'un intent a revisar",
                "verbose_name_plural": "tancaments d'intents a revisar",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("note__regex", "\\S")),
                        name="review_closure_note_required",
                    )
                ],
            },
        ),
        migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL),
    ]
