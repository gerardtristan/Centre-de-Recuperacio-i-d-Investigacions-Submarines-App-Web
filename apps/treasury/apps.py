from django.apps import AppConfig


class TreasuryConfig(AppConfig):
    name = "apps.treasury"
    verbose_name = "Tresoreria"

    def ready(self):
        from apps.core.imports import bank_statement

        from . import reconciliation

        bank_statement.changed.connect(
            reconciliation.on_statement_changed, dispatch_uid="treasury.reconciliation"
        )
        bank_statement.reconciled_lines.connect(
            reconciliation.has_live_reconciliations, dispatch_uid="treasury.reconciled_lines"
        )
