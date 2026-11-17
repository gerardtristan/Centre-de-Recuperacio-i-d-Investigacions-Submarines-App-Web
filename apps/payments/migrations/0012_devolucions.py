"""T-M05b-13: devolucions que fa el club (M05b-6; P-M05b-G), amb la clau que les fa idempotents
(P-118, P-119)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0038_payments_mandates_revoke_permission"),
        ("payments", "0011_fitxer_de_la_remesa"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RefundRequest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("key", models.UUIDField(unique=True, verbose_name="clau")),
                ("amount_cents", models.PositiveBigIntegerField(verbose_name="import (cèntims)")),
                ("reason", models.TextField(verbose_name="motiu")),
                (
                    "channel",
                    models.CharField(
                        choices=[("provider", "Proveïdor"), ("bank", "Banc")],
                        max_length=8,
                        verbose_name="canal",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pendent"), ("done", "Feta")],
                        default="pending",
                        max_length=7,
                        verbose_name="estat",
                    ),
                ),
                (
                    "provider_refund_id",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="devolució del proveïdor"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("done_at", models.DateTimeField(blank=True, null=True, verbose_name="feta el")),
                (
                    "payment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="core.payment",
                        verbose_name="pagament",
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "devolució",
                "verbose_name_plural": "devolucions",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("amount_cents__gt", 0)), name="refund_amount_positive"
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("reason__regex", "\\S")), name="refund_reason_required"
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("channel__in", ["provider", "bank"])),
                        name="refund_channel_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(("done_at__isnull", True), ("status", "pending")),
                            models.Q(("done_at__isnull", False), ("status", "done")),
                            _connector="OR",
                        ),
                        name="refund_done_at_iff_done",
                    ),
                ],
            },
        ),
    ]
