from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EquipmentConfig(AppConfig):
    name = "apps.equipment"
    verbose_name = "Material"

    def ready(self):
        from django.db.models.signals import post_save

        from apps.activities import extensions

        from . import closing, costs, detail, needs, places, typical

        # RN-M02-43 i RN-M03-25: el 02 copia aquest cost a l'activitat que es crea.
        extensions.register_material_cost_calculator(costs.standard_material_cost)

        # RN-M03-23: el centre habitual, al formulari del lloc del 02.
        extensions.register_place_section(
            extensions.PlaceSection(
                key="equipment.usual_centre",
                label=_("Centre habitual"),
                fields=places.section_fields,
                save=places.section_save,
            )
        )
        # P-M03-C: què porta i què necessita, al formulari d'inscripció.
        extensions.register_enrolment_section(
            extensions.EnrolmentSection(
                key=needs.SECTION_KEY,
                label=_("Material"),
                fields=needs.section_fields,
                save=needs.section_save,
            )
        )
        # RN-M03-17: el material típic es copia en crear l'activitat i en duplicar-la.
        post_save.connect(
            typical.on_activity_saved,
            sender="activities.Activity",
            dispatch_uid="equipment.typical.created",
        )
        extensions.activity_duplicated.connect(
            typical.on_activity_duplicated, dispatch_uid="equipment.typical.duplicated"
        )
        # C10, MT2 i MT7: el material assignat, a «Les meves activitats» i a la fitxa.
        extensions.register_detail_section(detail.SECTION)
        # RN-M03-13: «material pendent» impedeix tancar l'activitat.
        extensions.register_closing_check(closing.pending_reasons)
        # RN-M03-20 i L-M03-05: una inscripció que ja no és viva o una activitat cancel·lada
        # alliberen les peces previstes.
        post_save.connect(
            closing.on_enrolment_saved,
            sender="activities.Enrolment",
            dispatch_uid="equipment.closing.enrolment",
        )
        post_save.connect(
            closing.on_activity_saved,
            sender="activities.Activity",
            dispatch_uid="equipment.closing.activity",
        )
