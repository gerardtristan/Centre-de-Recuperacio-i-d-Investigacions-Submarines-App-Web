"""T-M00-08e (097; planning.md#M00-textos-editables): els textos d'ajuda de les pantalles, un
ajust de text buit (el text per defecte del codi) per plafó «Ajuda», a l'àrea de socis. No toca
cap permís: l'àrea ja té l'administrador i la Secretaria amb «Sí» (`core/0050`). Patró de la
0049."""

from django.db import migrations

KEYS = [
    "texts-members.ajuda-perfil-nom",
    "texts-members.ajuda-perfil-llicencia",
    "texts-members.ajuda-edicio-soci",
]


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    for key in KEYS:
        Setting.objects.get_or_create(
            key=key,
            defaults={
                "module": "texts-members",
                "value_type": "text",
                "initial_value": "",
                "max_length": 1000,
            },
        )


def unload(apps, schema_editor):
    # Només els que no tenen cap versió: l'historial d'un text editat no s'esborra mai.
    apps.get_model("core", "Setting").objects.filter(key__in=KEYS, versions__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0050_text_areas")]

    operations = [migrations.RunPython(load, unload)]
