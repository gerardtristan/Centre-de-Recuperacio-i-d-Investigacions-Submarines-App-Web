from django.apps import AppConfig


class MarginsConfig(AppConfig):
    name = "apps.margins"
    verbose_name = "Marges"

    def ready(self):
        # T-M09-02: la 04 consulta els períodes tancats del 09 abans de crear cada moviment.
        from apps.treasury import services

        from . import periods

        services.register_movement_guard(periods.closed_until)
