"""VC-17 (addenda de la 055 del 05b; T-M05b-22): els dos valors de la pantalla d'ajustos de
pagaments, que substitueixen les constants del codi, i els minuts que un Bizum conserva des que
comença (RN-M05b-24). Els permisos són a `core/0031`. Cap dels dos afecta diners ni té data
d'entrada en vigor."""

from django.db import migrations, models

SETTINGS = [
    ("payments.bizum_ui_timeout_minutes", 15, 5, 30),
    ("payments.safety_net_age_minutes", 60, 30, 240),
]


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key, initial, low, high in SETTINGS:
        Setting.objects.get_or_create(
            key=key,
            defaults={"module": "payments", "value_type": "integer", "initial_value": initial,
                      "min_value": low, "max_value": high},
        )  # fmt: skip


def unload(apps, schema_editor):
    # Un valor ja canviat té historial, que no s'esborra mai: llavors l'ajust es queda i, si es
    # torna a aplicar la migració, es reaprofita.
    apps.get_model("core", "Setting").objects.filter(
        key__in=[key for key, *_ in SETTINGS], versions__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0031_settings_payments_permissions"),
        ("payments", "0003_receipt"),
    ]

    operations = [
        migrations.AddField(
            model_name="paymentattempt",
            name="ui_timeout_minutes",
            field=models.PositiveSmallIntegerField(
                blank=True, null=True, verbose_name="minuts d'espera a la pantalla"
            ),
        ),
        migrations.RunPython(load, unload),
    ]
