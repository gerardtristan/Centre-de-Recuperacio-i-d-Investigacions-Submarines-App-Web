from django.apps import AppConfig


class WebsiteConfig(AppConfig):
    name = "apps.website"
    verbose_name = "Web pública i ajuda"

    def ready(self):
        from apps.core import events
        from apps.core import privacy as core_privacy

        from . import clients, privacy

        # T-M07-36 (decisió 108, C.3): l'excepció de client escolta els pagaments (apagada, res).
        events.subscribe(events.CHARGE_PAID, clients.on_charge_paid)

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
