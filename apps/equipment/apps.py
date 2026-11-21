from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EquipmentConfig(AppConfig):
    name = "apps.equipment"
    verbose_name = "Material"

    def ready(self):
        from apps.activities import extensions

        from . import places

        # RN-M03-23: el centre habitual, al formulari del lloc del 02.
        extensions.register_place_section(
            extensions.PlaceSection(
                key="equipment.usual_centre",
                label=_("Centre habitual"),
                fields=places.section_fields,
                save=places.section_save,
            )
        )
