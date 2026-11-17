"""Arqueig de caixa (T-M04-09; CA-T08.1): només s'hi afegeixen files, també amb una consulta
SQL directa, com les desfetes de conciliació (0012). Desfer la migració treu la taula."""

import django.db.models.deletion
import django.db.models.expressions
from django.conf import settings
from django.db import migrations, models

APPEND_ONLY_SQL = """
CREATE FUNCTION treasury_cashcount_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Els arqueigs no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;
CREATE TRIGGER treasury_cashcount_no_update_or_delete
    BEFORE UPDATE OR DELETE ON treasury_cashcount
    FOR EACH ROW EXECUTE FUNCTION treasury_cashcount_immutable();
CREATE TRIGGER treasury_cashcount_no_truncate
    BEFORE TRUNCATE ON treasury_cashcount
    FOR EACH STATEMENT EXECUTE FUNCTION treasury_cashcount_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER treasury_cashcount_no_truncate ON treasury_cashcount;
DROP TRIGGER treasury_cashcount_no_update_or_delete ON treasury_cashcount;
DROP FUNCTION treasury_cashcount_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("treasury", "0013_provider_settlement"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CashCount",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("counted_on", models.DateField(verbose_name="data de l'arqueig")),
                (
                    "counted_cents",
                    models.PositiveBigIntegerField(verbose_name="import comptat (cèntims)"),
                ),
                ("computed_cents", models.BigIntegerField(verbose_name="saldo calculat (cèntims)")),
                ("difference_cents", models.BigIntegerField(verbose_name="diferència (cèntims)")),
                (
                    "recorded_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="data de registre"),
                ),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cash_counts",
                        to="treasury.treasuryaccount",
                        verbose_name="compte",
                    ),
                ),
                (
                    "adjustment",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cash_count",
                        to="treasury.movement",
                        verbose_name="ajust",
                    ),
                ),
                (
                    "recorded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="registrat per",
                    ),
                ),
            ],
            options={
                "verbose_name": "arqueig",
                "verbose_name_plural": "arqueigs",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            (
                                "difference_cents",
                                django.db.models.expressions.CombinedExpression(
                                    models.F("counted_cents"), "-", models.F("computed_cents")
                                ),
                            )
                        ),
                        name="cash_count_difference_is_counted_minus_computed",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("adjustment__isnull", True),
                            models.Q(("difference_cents", 0), _negated=True),
                            _connector="OR",
                        ),
                        name="cash_count_adjustment_only_with_difference",
                    ),
                ],
            },
        ),
        migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL),
    ]
