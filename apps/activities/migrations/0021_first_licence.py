"""«Inclou la primera llicència» a les versions de preu del catàleg i a l'activitat, i els ajustos
VC-60 i VC-61 (T-M02-50; addenda de la 104; RN-M02-55, 57 i 59). Tots dos ajustos comencen buits:
la categoria, fins que el tresorer en triï una; el departament, el dels cursos (P-427)."""

from django.db import migrations, models

SETTINGS = {
    "activities.included_licence_expense_category": {
        "value_type": "text", "initial_value": "", "max_length": 80,
    },
    "activities.homologation_department": {
        "value_type": "text", "initial_value": "", "max_length": 80,
    },
}  # fmt: skip


def seed(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key, fields in SETTINGS.items():
        Setting.objects.get_or_create(key=key, defaults={"module": "activities", **fields})


def unseed(apps, schema_editor):
    """Els ajustos es queden (en guarden l'historial), com a la 0013."""


class Migration(migrations.Migration):
    dependencies = [
        ("activities", "0020_filing_course_outcome"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
        migrations.AddField(
            model_name="activity",
            name="includes_first_licence",
            field=models.BooleanField(default=False, verbose_name="inclou la primera llicència"),
        ),
        migrations.AddField(
            model_name="trainingcatalogueprice",
            name="includes_first_licence",
            field=models.BooleanField(default=False, verbose_name="inclou la primera llicència"),
        ),
    ]
