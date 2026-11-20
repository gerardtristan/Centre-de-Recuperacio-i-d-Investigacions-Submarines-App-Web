from django.apps import AppConfig


class LicencesConfig(AppConfig):
    name = "apps.licences"
    verbose_name = "Llicències"

    def ready(self):
        from apps.core import events

        from . import services

        events.subscribe(events.CHARGE_PAID, services.on_charge_paid)
