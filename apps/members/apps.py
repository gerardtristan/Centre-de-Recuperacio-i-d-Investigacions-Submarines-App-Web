from django.apps import AppConfig


class MembersConfig(AppConfig):
    name = "apps.members"
    verbose_name = "Socis i carnet"

    def ready(self):
        from . import checks  # noqa: F401 (registra les comprovacions d'arrencada)
