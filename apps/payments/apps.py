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

        from .setup import ensure_transit_account

        post_migrate.connect(ensure_transit_account, sender=self)

        from apps.core.models import Payment, PaymentCancellation

        from .transfers import on_cancellation_saved, on_payment_saved

        # T-M05b-06: una transferència conciliada a la 04 dona l'intent per pagat i el rebut.
        post_save.connect(on_payment_saved, sender=Payment, dispatch_uid="payments.transfer_paid")
        # T-M05b-29: la 045 la torna a pendent; l'intent es cancel·la i el rebut s'anul·la.
        post_save.connect(
            on_cancellation_saved,
            sender=PaymentCancellation,
            dispatch_uid="payments.transfer_reverted",
        )
