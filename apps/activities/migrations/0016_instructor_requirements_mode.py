"""T-M02-30 (RN-M02-26; VC-46): `activities.instructor_requirements_mode`, què passa en assignar
com a instructor algú que no és soci actiu o no té la llicència tècnica vigent: «bloqueig»
(`block`, valor inicial [A validar: junta]) o «avís» (`warn`). El permís per editar-lo és del
nucli (catàleg i matriu): mentre no hi sigui, el valor és l'inicial."""

from django.db import migrations

KEY = "activities.instructor_requirements_mode"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={
            "module": "activities",
            "value_type": "choice",
            "initial_value": "block",
            "choices": ["block", "warn"],
        },
    )


def unload(apps, schema_editor):
    """L'ajust es queda: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [("activities", "0015_course_outcome")]

    operations = [migrations.RunPython(load, unload)]
