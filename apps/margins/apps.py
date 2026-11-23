from django.apps import AppConfig


class MarginsConfig(AppConfig):
    name = "apps.margins"
    verbose_name = "Marges"

    def ready(self):
        # T-M09-02: la 04 consulta els períodes tancats del 09 abans de crear cada moviment.
        from apps.treasury import services

        from . import periods

        services.register_movement_guard(periods.closed_until)

        # T-M02-51b (RN-M02-59): el cost previst de la primera llicència inclosa al curs.
        from apps.activities import extensions

        from . import included_licence

        extensions.first_licence_included.connect(
            included_licence.on_first_licence_included, dispatch_uid="margins.included_licence"
        )
