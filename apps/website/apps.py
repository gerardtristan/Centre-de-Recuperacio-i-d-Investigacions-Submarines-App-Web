from django.apps import AppConfig


class WebsiteConfig(AppConfig):
    name = "apps.website"
    verbose_name = "Web pública i ajuda"

    def ready(self):
        from apps.core import privacy as core_privacy

        from . import privacy

        # T-M07-15 (CA-M07-21): l'exportació i l'esborrat RGPD dels missatges i del butlletí.
        core_privacy.register(
            "web",
            core_privacy.Module(
                export=privacy.export,
                anonymise=privacy.anonymise,
                audit_targets=privacy.audit_targets,
                describe=privacy.describe,
                addresses=True,  # el correu de contacte, que la 00 ja ha buidat en cridar-lo
            ),
        )
