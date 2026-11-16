from django.apps import AppConfig


class TreasuryConfig(AppConfig):
    name = "apps.treasury"
    verbose_name = "Tresoreria"

    def ready(self):
        from apps.core.imports import bank_statement

        from . import reconciliation

        bank_statement.confirmed.connect(
            reconciliation.on_statement_confirmed, dispatch_uid="treasury.reconciliation"
        )
