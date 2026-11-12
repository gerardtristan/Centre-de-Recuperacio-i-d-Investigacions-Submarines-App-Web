"""Càrrec, pagament i departament, estructura bàsica (T-M01-09; spec 00, HU-15 i HU-16).

Crea el departament «General» (CA-16.1, amb la precisió del 02/11/2026: els centres de cost
com «Quotes de socis» els afegeix la T-M04-02).
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_general(apps, schema_editor):
    apps.get_model("core", "Department").objects.get_or_create(name="General")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_legal_texts_and_consents"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Department",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=80, unique=True, verbose_name="nom")),
                ("active", models.BooleanField(default=True, verbose_name="actiu")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "departament",
                "verbose_name_plural": "departaments",
            },
        ),
        migrations.CreateModel(
            name="Charge",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("fee", "Quota"),
                            ("enrolment", "Inscripció"),
                            ("licence", "Llicència"),
                        ],
                        max_length=10,
                        verbose_name="tipus",
                    ),
                ),
                ("concept", models.CharField(max_length=140, verbose_name="concepte")),
                ("amount_cents", models.PositiveBigIntegerField(verbose_name="import (cèntims)")),
                (
                    "currency",
                    models.CharField(
                        default="EUR", editable=False, max_length=3, verbose_name="moneda"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendent"),
                            ("paid", "Pagat"),
                            ("returned", "Retornat"),
                            ("cancelled", "Anul·lat"),
                        ],
                        default="pending",
                        max_length=10,
                        verbose_name="estat",
                    ),
                ),
                ("cancel_reason", models.TextField(blank=True, verbose_name="motiu d'anul·lació")),
                ("origin", models.CharField(max_length=30, verbose_name="mòdul d'origen")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="charges",
                        to="core.person",
                        verbose_name="persona deutora",
                    ),
                ),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="charges",
                        to="core.department",
                        verbose_name="departament",
                    ),
                ),
            ],
            options={
                "verbose_name": "càrrec",
                "verbose_name_plural": "càrrecs",
            },
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "method",
                    models.CharField(
                        choices=[
                            ("direct_debit", "Domiciliació"),
                            ("card", "Targeta"),
                            ("bizum", "Bizum"),
                            ("transfer", "Transferència"),
                            ("manual", "Manual"),
                        ],
                        max_length=12,
                        verbose_name="mètode",
                    ),
                ),
                ("amount_cents", models.PositiveBigIntegerField(verbose_name="import (cèntims)")),
                (
                    "provider_status",
                    models.CharField(blank=True, max_length=40, verbose_name="estat al proveïdor"),
                ),
                ("needs_review", models.BooleanField(default=False, verbose_name="a revisar")),
                (
                    "provider_reference",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="referència del proveïdor"
                    ),
                ),
                (
                    "transfer_reference",
                    models.CharField(
                        blank=True, max_length=60, verbose_name="referència de transferència"
                    ),
                ),
                (
                    "paid_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="data del pagament"),
                ),
                ("reason", models.TextField(blank=True, verbose_name="motiu")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "charge",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="payments",
                        to="core.charge",
                        verbose_name="càrrec",
                    ),
                ),
                (
                    "recorded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="registrat per",
                    ),
                ),
            ],
            options={
                "verbose_name": "pagament",
                "verbose_name_plural": "pagaments",
            },
        ),
        migrations.AddIndex(
            model_name="charge",
            index=models.Index(fields=["person", "status"], name="charge_person_status_idx"),
        ),
        migrations.AddConstraint(
            model_name="charge",
            constraint=models.CheckConstraint(
                condition=models.Q(("amount_cents__gt", 0)), name="charge_amount_positive"
            ),
        ),
        migrations.AddConstraint(
            model_name="charge",
            constraint=models.CheckConstraint(
                condition=models.Q(("currency", "EUR")), name="charge_currency_eur"
            ),
        ),
        migrations.AddConstraint(
            model_name="charge",
            constraint=models.CheckConstraint(
                condition=models.Q(("kind__in", ["fee", "enrolment", "licence"])),
                name="charge_kind_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="charge",
            constraint=models.CheckConstraint(
                condition=models.Q(("status__in", ["pending", "paid", "returned", "cancelled"])),
                name="charge_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="charge",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("status", "cancelled"), _negated=True),
                    models.Q(("cancel_reason", ""), _negated=True),
                    _connector="OR",
                ),
                name="charge_cancel_has_reason",
            ),
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(
                condition=models.Q(("amount_cents__gt", 0)), name="payment_amount_positive"
            ),
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("method__in", ["direct_debit", "card", "bizum", "transfer", "manual"])
                ),
                name="payment_method_valid",
            ),
        ),
        migrations.RunPython(create_general, migrations.RunPython.noop),
    ]
