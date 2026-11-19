"""T-M01-49 (097, P-61): els terminis de la quota de ple dret, apagats. Una quota pot ser un dels
tres terminis (`instalment`, de 1 a 3; 0 en la resta) i els quatre ajustos de la família
`members.instalments`: activat (no), import total (9600 cèntims, 3 × 32 €), recàrrec (0) i dies
per proposar l'impagat (30). L'import i el recàrrec, provisionals fins que la junta respongui. El
permís, `core/0052`."""

from django.db import migrations, models

SETTINGS = [
    # clau, tipus, valor inicial, mínim, màxim, afecta diners (i llavors té data d'entrada en vigor)
    ("members.instalments.enabled", "boolean", False, None, None, False),
    ("members.instalments.total_cents", "cents", 9600, 3, None, True),
    ("members.instalments.surcharge_cents", "cents", 0, 0, None, True),
    ("members.instalments.unpaid_candidate_days", "integer", 30, 1, 365, False),
]


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key, kind, initial, low, high, money in SETTINGS:
        Setting.objects.get_or_create(
            key=key,
            defaults={"module": "members", "value_type": kind, "initial_value": initial,
                      "min_value": low, "max_value": high, "affects_money": money,
                      "effective_dated": money},
        )  # fmt: skip


def unload(apps, schema_editor):
    """Els ajustos es queden, com els de `members/0022`: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0052_instalments_permission"),
        ("members", "0023_membership_type_attributes"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="annualfee",
            name="annualfee_kind_valid",
        ),
        migrations.RemoveConstraint(
            model_name="annualfee",
            name="annualfee_unique_period_kind_sequence",
        ),
        migrations.AddField(
            model_name="annualfee",
            name="instalment",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="termini"),
        ),
        migrations.AlterField(
            model_name="annualfee",
            name="kind",
            field=models.CharField(
                choices=[
                    ("annual", "Quota anual"),
                    ("type_change_supplement", "Suplement de canvi de tipus"),
                    ("instalment", "Termini de la quota"),
                ],
                max_length=25,
                verbose_name="tipus de quota",
            ),
        ),
        migrations.AddConstraint(
            model_name="annualfee",
            constraint=models.UniqueConstraint(
                fields=("member", "period", "kind", "instalment", "sequence"),
                name="annualfee_unique_period_kind_instalment_sequence",
            ),
        ),
        migrations.AddConstraint(
            model_name="annualfee",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("kind__in", ["annual", "type_change_supplement", "instalment"])
                ),
                name="annualfee_kind_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="annualfee",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("instalment__gte", 1), ("instalment__lte", 3), ("kind", "instalment")
                    ),
                    models.Q(models.Q(("kind", "instalment"), _negated=True), ("instalment", 0)),
                    _connector="OR",
                ),
                name="annualfee_instalment_valid",
            ),
        ),
        migrations.RunPython(load, unload),
    ]
