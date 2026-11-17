"""T-M05b-15: la targeta guardada amb què s'obre cada intent i la marca d'un avís ja donat
(una quota que una targeta no pot cobrar, per un motiu)."""

from django.db import migrations, models
from django.db.models.deletion import PROTECT

ID = ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"))  # fmt: skip


def fk(to, one=False):
    return (models.OneToOneField if one else models.ForeignKey)(on_delete=PROTECT, related_name="+", to=to)  # fmt: skip


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
    ]
