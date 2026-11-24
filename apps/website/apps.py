from django.apps import AppConfig


class WebsiteConfig(AppConfig):
    name = "apps.website"
    verbose_name = "Web pública i ajuda"

    def ready(self):
        from django.db.models.signals import pre_save

        from apps.core import privacy as core_privacy
        from apps.core.models import Person

        from . import privacy

        # T-M07-15 (CA-M07-21): l'exportació i l'esborrat RGPD dels missatges i del butlletí.
        pre_save.connect(privacy.remember_email, sender=Person, dispatch_uid="website.email")
        core_privacy.register(
            "web",
            core_privacy.Module(
                export=privacy.export,
                anonymise=privacy.anonymise,
                audit_targets=privacy.audit_targets,
                describe=privacy.describe,
            ),
        )
