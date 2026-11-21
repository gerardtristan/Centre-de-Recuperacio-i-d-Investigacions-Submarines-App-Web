from django.apps import AppConfig


class LicencesConfig(AppConfig):
    name = "apps.licences"
    verbose_name = "Llicències"

    def ready(self):
        from apps.core import events

        from . import services

        events.subscribe(events.CHARGE_PAID, services.on_charge_paid)

        # RN-M06-17 (054): la font de lectura per a la comprovació diària del 01.
        from apps.members.licence_copy import register_licence_source

        from . import events as licence_events

        register_licence_source(licence_events.read_source)
