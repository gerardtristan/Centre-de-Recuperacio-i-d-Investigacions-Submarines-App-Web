from django.db import migrations

# VC-29 (RN-M03-14): dies després de l'activitat a partir dels quals una peça lliurada i no retornada
# surt a l'avís diari, de 1 a 90 [A validar: junta, S-M03-06]. El permís d'editar-lo és de la
# pantalla d'ajustos del 03 (T-M03-22, torn del nucli).
KEY = "equipment.unreturned_after_days"


def load(apps, schema_editor):
    apps.get_model("core", "Setting").objects.get_or_create(
        key=KEY,
        defaults={"module": "equipment", "value_type": "integer", "initial_value": 7,
                  "min_value": 1, "max_value": 90},
    )  # fmt: skip


def unload(apps, schema_editor):
    """L'ajust es queda: un valor canviat té historial."""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0066_billing_settings_permissions"),
        ("equipment", "0010_rental_lists"),
    ]

    operations = [migrations.RunPython(load, unload)]
