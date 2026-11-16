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
    # RN-M05b-24: els Bizum que ja eren en curs conserven els 15 minuts que tenien.
    apps.get_model("payments", "PaymentAttempt").objects.filter(
        method="bizum", ui_timeout_minutes__isnull=True
    ).update(ui_timeout_minutes=15)
    Setting = apps.get_model("core", "Setting")
    for key, initial, low, high in SETTINGS:
        Setting.objects.get_or_create(
            key=key,
            defaults={"module": "payments", "value_type": "integer", "initial_value": initial,
                      "min_value": low, "max_value": high},
        )  # fmt: skip


def unload(apps, schema_editor):
    """Els ajustos es queden: un valor canviat té historial, que no s'esborra mai, i tornar a
    aplicar la migració els reaprofita (mateixa fila). Sense cap codi que els llegeixi, no fan
    res. El camp de l'intent sí que se'n va."""


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
