"""Centres de cost inicials (CA-T14.1): «General / Quotes de socis», «General / Llicències»
(provisional, VT-04) i «General / Ajustos de caixa» (VT-06). Reversible."""

from django.db import migrations

GENERAL = "General"
INITIAL = ["Quotes de socis", "Llicències", "Ajustos de caixa"]


def create_initial_cost_centres(apps, schema_editor):
    department = apps.get_model("core", "Department").objects.get(name=GENERAL)
    cost_centre = apps.get_model("treasury", "CostCentre")
    for name in INITIAL:
        cost_centre.objects.get_or_create(department=department, name=name)


def delete_initial_cost_centres(apps, schema_editor):
    apps.get_model("treasury", "CostCentre").objects.filter(
        department__name=GENERAL, name__in=INITIAL
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("treasury", "0003_cost_centre")]

    operations = [migrations.RunPython(create_initial_cost_centres, delete_initial_cost_centres)]
