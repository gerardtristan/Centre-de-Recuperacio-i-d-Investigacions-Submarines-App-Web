"""T-M09A-06 i T-M09A-15 (RN-M09A-06 i 22): els avisos enviats (`GrantReminder`, només INSERT) i
els ajustos dels dies: `grants.deadline_reminder_days` (VC-36: 30, 14 i 7; d'1 a 90) i
`grants.requirement_reminder_days` (VC-37: 7 i 2; d'1 a 30). El permís per editar-los és AJ10
(apartat d'ajustos dels ajuts, T-M09-26)."""

import django.db.models.deletion
from django.db import migrations, models

SETTINGS = {
    "grants.deadline_reminder_days": ([30, 14, 7], 90),  # VC-36
    "grants.requirement_reminder_days": ([7, 2], 30),  # VC-37
}


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key, (initial, maximum) in SETTINGS.items():
        Setting.objects.get_or_create(
            key=key,
            defaults={"module": "grants", "value_type": "integer_list", "initial_value": initial,
                      "min_value": 1, "max_value": maximum},
        )  # fmt: skip


def unload(apps, schema_editor):
    """Els ajustos es queden: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("grants", "0006_amendment_term"),
    ]

    operations = [
        migrations.RunPython(load, unload),
        migrations.CreateModel(
            name="GrantReminder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("kind", models.CharField(max_length=20, verbose_name="tipus")),
                ("due_on", models.DateField(verbose_name="data de referència")),
                ("sent_at", models.DateTimeField(auto_now_add=True, verbose_name="enviat")),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reminders",
                        to="grants.grantapplication",
                        verbose_name="sol·licitud",
                    ),
                ),
                (
                    "requirement",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reminders",
                        to="grants.grantrequirement",
                        verbose_name="requeriment",
                    ),
                ),
            ],
            options={
                "verbose_name": "avís d'un ajut",
                "verbose_name_plural": "avisos dels ajuts",
                "ordering": ["pk"],
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(("requirement__isnull", False)),
                        fields=("application", "requirement", "kind"),
                        name="grant_reminder_requirement_once",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(("requirement__isnull", True)),
                        fields=("application", "kind", "due_on"),
                        name="grant_reminder_once_per_date",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(
                                ("kind__startswith", "requirement_"), ("requirement__isnull", False)
                            ),
                            models.Q(
                                models.Q(("kind__startswith", "requirement_"), _negated=True),
                                ("requirement__isnull", True),
                            ),
                            _connector="OR",
                        ),
                        name="grant_reminder_requirement_kind",
                    ),
                ],
            },
        ),
    ]
