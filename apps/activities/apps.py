from django.apps import AppConfig


class ActivitiesConfig(AppConfig):
    name = "apps.activities"
    verbose_name = "Activitats (cursos i sortides)"

    def ready(self):
        # RGPD (M02-8): el nucli crida els mòduls registrats; no importa mai el 02.
        from apps.core import privacy as core_privacy

        from . import privacy

        core_privacy.register(
            "activitats",
            core_privacy.Module(
                export=privacy.export,
                anonymise=privacy.anonymise,
                audit_targets=privacy.audit_targets,
                describe=privacy.describe,
            ),
        )
