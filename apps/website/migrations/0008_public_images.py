"""Pla d'acceleració F2-6 (D2) i decisió 105: les imatges públiques de la web, darrere d'un
interruptor apagat. El permís per editar-lo (`settings.edit.website.public_images_enabled`) és
del catàleg del nucli: fins llavors, ningú no el pot encendre des de l'app."""

from django.db import migrations

KEY = "website.public_images_enabled"


def load(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    Setting.objects.get_or_create(
        key=KEY, defaults={"module": "website", "value_type": "boolean", "initial_value": False}
    )


class Migration(migrations.Migration):
    dependencies = [("website", "0007_news"), ("core", "0013_business_settings")]

    operations = [migrations.RunPython(load, migrations.RunPython.noop)]
