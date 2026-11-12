from django.apps import AppConfig


class MembersConfig(AppConfig):
    name = "apps.members"
    verbose_name = "Socis i carnet"

    def ready(self):
        # RGPD (T-M01-22): el M01 registra a la 00 la seva part de l'exportació i de
        # l'anonimització (contracte M01-8). La 00 no importa cap mòdul.
        from apps.core import privacy as core_privacy

        from . import (
            checks,  # noqa: F401 (registra les comprovacions d'arrencada)
            privacy,
        )

        core_privacy.register(
            "socis",
            core_privacy.Module(
                export=privacy.export_personal_data,
                anonymise=privacy.anonymise,
                audit_targets=privacy.audit_targets,
                describe=privacy.describe,
            ),
        )
