from django.apps import AppConfig


class DashboardConfig(AppConfig):
    name = "apps.dashboard"
    verbose_name = "Dashboard"

    def ready(self):
        from apps.core import business_settings

        from . import indicators

        # P-488: un sol permís per als textos d'ajuda de tots els indicadors; la fila diu el nom.
        business_settings.register_family(indicators.HELP_TEXT, indicators.name_of)
