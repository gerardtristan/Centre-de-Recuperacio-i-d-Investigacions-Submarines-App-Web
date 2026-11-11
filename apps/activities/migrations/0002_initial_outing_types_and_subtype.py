"""Dades inicials del catàleg del M02 (T-M02-02; pla, M02-6).

- Tipus de sortida: «Immersió», «Medi ambient» (de medi ambient), «Sèniors» i «Jornada oberta»,
  amb el departament «General» de la 00 per defecte [A validar: junta, si són tipus propis]. El
  responsable els pot desactivar.
- Subtipus de medi ambient: «Neteja» (F §5). La resta de la llista és la S-M02-13.
- El catàleg de cursos i d'especialitats neix buit (S-M02-07): els cursos i els preus reals els
  ha de donar la junta. Cap projecte.

Cap dada personal. Desfer-la esborra aquestes files; només es pot si cap activitat les fa servir.
"""

from django.db import migrations

OUTING_TYPES = [
    ("Immersió", False),
    ("Medi ambient", True),
    ("Sèniors", False),
    ("Jornada oberta", False),
]
SUBTYPES = ["Neteja"]


def create(apps, schema_editor):
    general, _ = apps.get_model("core", "Department").objects.get_or_create(name="General")
    OutingType = apps.get_model("activities", "OutingType")
    for name, environmental in OUTING_TYPES:
        OutingType.objects.create(
            name=name, is_environmental=environmental, default_department=general
        )
    Subtype = apps.get_model("activities", "EnvironmentalSubtype")
    for name in SUBTYPES:
        Subtype.objects.create(name=name)


def remove(apps, schema_editor):
    apps.get_model("activities", "EnvironmentalSubtype").objects.filter(name__in=SUBTYPES).delete()
    apps.get_model("activities", "OutingType").objects.filter(
        name__in=[name for name, _ in OUTING_TYPES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("activities", "0001_initial"),
        ("core", "0006_charges_and_departments"),
    ]

    operations = [migrations.RunPython(create, remove)]
