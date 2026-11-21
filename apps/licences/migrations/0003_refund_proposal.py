"""T-M06-12 (M06-6; RN-M06-09, CA-M06-13): propostes de devolució de les llicències cancel·lades
després de pagar-les."""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("licences", "0002_settings"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LicenceRefundProposal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("amount_cents", models.PositiveIntegerField(verbose_name="import (cèntims)")),
                ("reason", models.TextField(verbose_name="motiu")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("proposed", "Proposada"),
                            ("done", "Feta"),
                            ("rejected", "Rebutjada"),
                        ],
                        default="proposed",
                        max_length=8,
                        verbose_name="estat",
                    ),
                ),
                (
                    "refund_key",
                    models.UUIDField(
                        default=uuid.uuid4, unique=True, verbose_name="clau de la devolució"
                    ),
                ),
                ("decision_note", models.TextField(blank=True, verbose_name="nota de la decisió")),
                ("decided_at", models.DateTimeField(null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "decided_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "licence",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="refund_proposal",
                        to="licences.licence",
                        verbose_name="llicència",
                    ),
                ),
            ],
            options={
                "verbose_name": "proposta de devolució de llicència",
                "verbose_name_plural": "propostes de devolució de llicència",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("amount_cents__gt", 0)),
                        name="licences_refund_amount_positive",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("status__in", ["proposed", "done", "rejected"])),
                        name="licences_refund_status_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("status", "proposed"), ("decided_by__isnull", False), _connector="OR"
                        ),
                        name="licences_refund_decided_has_author",
                    ),
                ],
            },
        ),
    ]
