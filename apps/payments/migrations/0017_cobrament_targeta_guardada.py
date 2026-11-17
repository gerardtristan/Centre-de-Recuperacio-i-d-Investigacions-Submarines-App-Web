"""T-M05b-15: la targeta guardada amb què s'obre cada intent i la marca d'un avís ja donat
(una quota que una targeta no pot cobrar, per un motiu)."""

from django.db import migrations, models
from django.db.models.deletion import PROTECT

ID = ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"))  # fmt: skip


def fk(to, one=False):
    return (models.OneToOneField if one else models.ForeignKey)(on_delete=PROTECT, related_name="+", to=to)  # fmt: skip


def load(apps, schema_editor):  # P-302: la finestra de cobrament, 7 dies [A validar: tresorer]
    apps.get_model("core", "Setting").objects.get_or_create(key="payments.saved_card_charge_window_days", defaults={"module": "payments", "value_type": "integer", "initial_value": 7, "min_value": 0, "max_value": 60})  # fmt: skip


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0043_settings_vc11_permission"),
        ("payments", "0016_targeta_guardada"),
    ]

    operations = [
        migrations.CreateModel(
            name="SavedCardAttempt",
            fields=[
                ID,
                ("attempt", fk("payments.paymentattempt", one=True)),
                ("card", fk("payments.savedcard")),
                ("reached_provider", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "targeta d'un intent",
                "verbose_name_plural": "targetes dels intents",
            },
        ),
        migrations.CreateModel(
            name="SavedCardNotice",
            fields=[
                ID,
                ("case", models.CharField(max_length=30, verbose_name="motiu")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("card", fk("payments.savedcard")),
                ("charge", fk("core.charge")),
            ],
            options={
                "verbose_name": "avís de quota no cobrada amb la targeta",
                "verbose_name_plural": "avisos de quotes no cobrades amb la targeta",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("charge", "card", "case"), name="saved_card_notice_once"
                    )
                ],
            },
        ),
        migrations.RunPython(load, migrations.RunPython.noop),  # l'ajust es queda
    ]
