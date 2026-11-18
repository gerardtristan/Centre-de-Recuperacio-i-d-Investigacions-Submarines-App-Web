"""T-M00-08b: la nota de cada versió d'un text legal (M12) i els ajustos buits (el text per
defecte del codi) de la resta de correus editables. Patró de la 0047."""

from django.db import migrations, models

KEYS = [
    "texts.avis-renovacio",
    "texts.avis-renovacio-pas-acceptat",
    "texts.avis-renovacio-pas-pendent",
    "texts.rebut-sollicitud-alta",
    "texts.alta-rebutjada",
]


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key in KEYS:
        Setting.objects.get_or_create(
            key=key,
            defaults={
                "module": "texts",
                "value_type": "text",
                "initial_value": "",
                "max_length": 5000,
            },
        )


def unload(apps, schema_editor):
    # Només els ajustos que encara no tenen cap versió: l'historial d'un text editat no s'esborra
    # mai, i tornar a aplicar la migració el reaprofita (`get_or_create`).
    apps.get_model("core", "Setting").objects.filter(key__in=KEYS, versions__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0048_settings_members_types_permissions")]

    operations = [
        migrations.AddField(
            model_name="legaltext",
            name="note",
            field=models.TextField(blank=True, default="", verbose_name="nota"),
        ),
        migrations.RunPython(load, unload),
    ]
