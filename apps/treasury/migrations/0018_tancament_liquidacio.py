"""Tancament d'una liquidació «a revisar» (T-M04-14c; P-390): només s'hi afegeixen files, també
amb una consulta SQL directa, com els tancaments del 05b (payments/0022)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

APPEND_ONLY_SQL = """
CREATE FUNCTION treasury_settlementreviewclosure_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Els tancaments de liquidacions no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;
CREATE TRIGGER treasury_settlementreviewclosure_no_update_or_delete
    BEFORE UPDATE OR DELETE ON treasury_settlementreviewclosure
    FOR EACH ROW EXECUTE FUNCTION treasury_settlementreviewclosure_immutable();
CREATE TRIGGER treasury_settlementreviewclosure_no_truncate
    BEFORE TRUNCATE ON treasury_settlementreviewclosure
    FOR EACH STATEMENT EXECUTE FUNCTION treasury_settlementreviewclosure_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER treasury_settlementreviewclosure_no_truncate ON treasury_settlementreviewclosure;
DROP TRIGGER treasury_settlementreviewclosure_no_update_or_delete
    ON treasury_settlementreviewclosure;
DROP FUNCTION treasury_settlementreviewclosure_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("treasury", "0017_liquidacio_a_la_conciliacio"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SettlementReviewClosure",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("closed_at", models.DateTimeField(auto_now_add=True, verbose_name="tancada el")),
                (
                    "closed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="tancada per",
                    ),
                ),
                (
                    "settlement",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="review_closure",
                        to="treasury.providersettlement",
                        verbose_name="liquidació",
                    ),
                ),
            ],
            options={
                "verbose_name": "tancament d'una liquidació a revisar",
                "verbose_name_plural": "tancaments de liquidacions a revisar",
            },
        ),
        migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL),
    ]
