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

        # Esborrat RGPD (T-M04-14c): el nucli crida els mòduls registrats.
        from apps.core import privacy as core_privacy

        from . import privacy

        core_privacy.register(
            "tresoreria",
            core_privacy.Module(
                export=privacy.export,
                anonymise=privacy.anonymise,
                audit_targets=privacy.audit_targets,
            ),
        )
