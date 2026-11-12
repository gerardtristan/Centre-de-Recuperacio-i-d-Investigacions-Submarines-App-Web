from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    name = "apps.payments"
    verbose_name = "Pagaments"

    def ready(self):
        from . import checks  # noqa: F401 (registra les comprovacions d'arrencada)
