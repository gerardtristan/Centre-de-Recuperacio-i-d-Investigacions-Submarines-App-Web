from django.apps import AppConfig


class InvoicingConfig(AppConfig):
    name = "apps.invoicing"
    verbose_name = "Facturació"

    def ready(self):
        from apps.core import business_settings, events

        from . import services

        # 049: la factura d'un cobrament neix de l'esdeveniment, no de qui cobra.
        events.subscribe(events.CHARGE_PAID, services.on_charge_paid)
        business_settings.register_check(
            services.ENABLED_KINDS,
            services.check_enabled_kinds,
            normalise=business_settings.canonical_list,
        )
