from django.apps import AppConfig
from django.db.models.signals import post_migrate


class PaymentsConfig(AppConfig):
    name = "apps.payments"
    verbose_name = "Pagaments"

    def ready(self):
        from . import checks  # registra les comprovacions d'arrencada

        checks.refuse_fake_integrations()

        from .setup import ensure_transit_account

        post_migrate.connect(ensure_transit_account, sender=self)
