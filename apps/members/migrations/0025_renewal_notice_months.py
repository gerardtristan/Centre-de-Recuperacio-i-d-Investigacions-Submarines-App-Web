"""T-M01-43e (P-399): els mesos de l'avís de renovació passen de l'entorn
(`MEMBER_RENEWAL_NOTICE_MONTHS`) a l'ajust `members.renewal_notice_months`: enter, 1 mes, d'1 a 6.
El permís, `core/0057`."""

from django.db import migrations

KEY = "members.renewal_notice_months"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={"module": "members", "value_type": "integer", "initial_value": 1,
                  "min_value": 1, "max_value": 6, "affects_money": False,
                  "effective_dated": False},
    )  # fmt: skip


def unload(apps, schema_editor):
    """L'ajust es queda, com els de `members/0022`: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0057_renewal_notice_months_permission"),
        ("members", "0024_instalments"),
    ]

    operations = [migrations.RunPython(load, unload)]
