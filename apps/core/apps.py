from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"
    verbose_name = "Base comuna"

    def ready(self):
        from . import checks  # noqa: F401 (registra les comprovacions d'arrencada)
