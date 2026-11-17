"""T-M05b-09: remeses i rebuts domiciliats (M05b-6), i els dies de l'avís previ (VC-16,
S-M05b-06: 14, de 14 a 30). El permís per editar-los arriba amb la pantalla de la VC-16; fins
llavors només els edita qui té tot l'apartat de pagaments."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key="payments.prenotification_days",
        defaults={"module": "payments", "value_type": "integer", "initial_value": 14,
                  "min_value": 14, "max_value": 30},
    )  # fmt: skip


def unload(apps, schema_editor):
    """L'ajust es queda, com els de la 0004: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0037_payments_campaign_send_permission"),
        ("payments", "0009_bloqueig_de_mandats"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DirectDebitRemittance",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("period", models.CharField(max_length=20, verbose_name="període")),
                ("collection_date", models.DateField(verbose_name="data de cobrament")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Esborrany"),
                            ("notified", "Avisada"),
                            ("sent_to_bank", "Enviada al banc"),
                            ("settled", "Liquidada"),
                            ("cancelled", "Anul·lada"),
                        ],
                        default="draft",
                        max_length=12,
                        verbose_name="estat",
                    ),
                ),
                ("item_count", models.PositiveIntegerField(verbose_name="rebuts")),
                (
                    "total_cents",
                    models.PositiveBigIntegerField(verbose_name="import total (cèntims)"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "remesa",
                "verbose_name_plural": "remeses",
            },
        ),
        migrations.CreateModel(
            name="DirectDebitItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("amount_cents", models.PositiveBigIntegerField(verbose_name="import (cèntims)")),
                (
                    "end_to_end_id",
                    models.CharField(
                        max_length=35, unique=True, verbose_name="identificador d'extrem a extrem"
                    ),
                ),
                (
                    "attempt_number",
                    models.PositiveSmallIntegerField(default=1, verbose_name="intent"),
                ),
                (
                    "prenotified_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="avís previ enviat"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("included", "Inclòs"),
                            ("excluded", "Exclòs"),
                            ("collected", "Cobrat"),
                            ("returned", "Retornat"),
                        ],
                        default="included",
                        max_length=10,
                        verbose_name="estat",
                    ),
                ),
                (
                    "attempt",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="direct_debit_item",
                        to="payments.paymentattempt",
                    ),
                ),
                (
                    "mandate",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="payments.sepamandate",
                    ),
                ),
                (
                    "remittance",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="items",
                        to="payments.directdebitremittance",
                    ),
                ),
            ],
            options={
                "verbose_name": "rebut domiciliat",
                "verbose_name_plural": "rebuts domiciliats",
            },
        ),
        migrations.AddConstraint(
            model_name="directdebitremittance",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("status__in", ["draft", "notified", "sent_to_bank", "settled", "cancelled"])
                ),
                name="dd_remittance_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="directdebititem",
            constraint=models.CheckConstraint(
                condition=models.Q(("amount_cents__gt", 0)), name="dd_item_amount_positive"
            ),
        ),
        migrations.AddConstraint(
            model_name="directdebititem",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("status__in", ["included", "excluded", "collected", "returned"])
                ),
                name="dd_item_status_valid",
            ),
        ),
        migrations.RunPython(load, unload),
    ]
