"""Liquidacions del proveïdor (T-M04-13): `ProviderSettlement`, `SettlementItem` (només s'hi
afegeixen files, també amb SQL directe, com les desfetes de la 0012) i `Movement.settlement`.
Desfer la migració treu les taules i el camp."""

import django.db.models.deletion
import django.db.models.expressions
from django.db import migrations, models

APPEND_ONLY_SQL = """
CREATE FUNCTION treasury_settlementitem_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Les partides de liquidació no es poden modificar ni esborrar (%).', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$;
CREATE TRIGGER treasury_settlementitem_no_update_or_delete
    BEFORE UPDATE OR DELETE ON treasury_settlementitem
    FOR EACH ROW EXECUTE FUNCTION treasury_settlementitem_immutable();
CREATE TRIGGER treasury_settlementitem_no_truncate
    BEFORE TRUNCATE ON treasury_settlementitem
    FOR EACH STATEMENT EXECUTE FUNCTION treasury_settlementitem_immutable();
"""

REVERSE_SQL = """
DROP TRIGGER treasury_settlementitem_no_truncate ON treasury_settlementitem;
DROP TRIGGER treasury_settlementitem_no_update_or_delete ON treasury_settlementitem;
DROP FUNCTION treasury_settlementitem_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0036_treasury_reverse_permission"),
        ("treasury", "0012_reconciliation_undo"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProviderSettlement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("provider_code", models.CharField(max_length=30, verbose_name="proveïdor")),
                (
                    "external_id",
                    models.CharField(max_length=100, verbose_name="identificador del proveïdor"),
                ),
                ("settled_on", models.DateField(verbose_name="data de l'abonament")),
                ("gross_cents", models.PositiveBigIntegerField(verbose_name="brut (cèntims)")),
                ("fees_cents", models.PositiveBigIntegerField(verbose_name="comissions (cèntims)")),
                ("net_cents", models.PositiveBigIntegerField(verbose_name="net (cèntims)")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("received", "Rebuda"),
                            ("reconciled", "Conciliada"),
                            ("to_review", "A revisar"),
                        ],
                        max_length=10,
                        verbose_name="estat",
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("notification", "Notificació"),
                            ("file", "Fitxer"),
                            ("manual", "Manual"),
                            ("remittance", "Remesa"),
                        ],
                        max_length=12,
                        verbose_name="origen",
                    ),
                ),
                (
                    "review_notes",
                    models.JSONField(blank=True, default=list, verbose_name="problemes"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "liquidació",
                "verbose_name_plural": "liquidacions",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("provider_code", "external_id"),
                        name="settlement_unique_per_provider",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            (
                                "net_cents",
                                django.db.models.expressions.CombinedExpression(
                                    models.F("gross_cents"), "-", models.F("fees_cents")
                                ),
                            )
                        ),
                        name="settlement_net_is_gross_minus_fees",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("gross_cents__gt", 0), ("net_cents__gt", 0)),
                        name="settlement_amounts_positive",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("status__in", ["received", "reconciled", "to_review"])),
                        name="settlement_status_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("source__in", ["notification", "file", "manual", "remittance"])
                        ),
                        name="settlement_source_valid",
                    ),
                ],
            },
        ),
        migrations.AddField(
            model_name="movement",
            name="settlement",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="movements",
                to="treasury.providersettlement",
                verbose_name="liquidació",
            ),
        ),
        migrations.CreateModel(
            name="SettlementItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("amount_cents", models.PositiveBigIntegerField(verbose_name="import (cèntims)")),
                (
                    "fee_cents",
                    models.PositiveBigIntegerField(
                        blank=True, null=True, verbose_name="comissió (cèntims)"
                    ),
                ),
                (
                    "payment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="core.payment",
                        verbose_name="pagament",
                    ),
                ),
                (
                    "settlement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="items",
                        to="treasury.providersettlement",
                        verbose_name="liquidació",
                    ),
                ),
            ],
            options={
                "verbose_name": "partida de liquidació",
                "verbose_name_plural": "partides de liquidació",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("amount_cents__gt", 0)),
                        name="settlement_item_amount_positive",
                    )
                ],
            },
        ),
        migrations.RunSQL(APPEND_ONLY_SQL, REVERSE_SQL),
    ]
