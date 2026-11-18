from django.apps import AppConfig
from django.db.models.signals import post_migrate, post_save


class PaymentsConfig(AppConfig):
    name = "apps.payments"
    verbose_name = "Pagaments"

    def ready(self):
        from . import checks  # registra les comprovacions d'arrencada

        checks.refuse_fake_integrations()

        # Esborrat RGPD i exportació (L-M05a-06): el nucli crida els mòduls registrats.
        from apps.core import privacy as core_privacy

        from . import privacy

        core_privacy.register(
            "pagaments",
            core_privacy.Module(
                export=privacy.export,
                anonymise=privacy.anonymise,
                audit_targets=privacy.audit_targets,
                describe=privacy.describe,
            ),
        )

        from apps.core import business_settings

        from . import returns

        # P-291: les dues llistes de codis de retorn no poden compartir cap codi.
        for key in (returns.RETRY_CODES, returns.BLOCK_CODES):
            business_settings.register_check(key, returns.check_codes(key))

        from .setup import ensure_transit_account

        post_migrate.connect(ensure_transit_account, sender=self)

        from apps.core import charges
        from apps.core.models import Payment, PaymentCancellation

        from . import attempts
        from .transfers import on_cancellation_saved, on_payment_saved

        # P-12: cap pagament a mà amb un intent que potser ja ha cobrat el càrrec.
        charges.register_manual_payment_guard(attempts.ensure_manual_payment_allowed)

        # T-M05b-06: una transferència conciliada a la 04 dona l'intent per pagat i el rebut.
        post_save.connect(on_payment_saved, sender=Payment, dispatch_uid="payments.transfer_paid")
        # T-M05b-29: la 045 la torna a pendent; l'intent es cancel·la i el rebut s'anul·la.
        post_save.connect(
            on_cancellation_saved,
            sender=PaymentCancellation,
            dispatch_uid="payments.transfer_reverted",
        )
