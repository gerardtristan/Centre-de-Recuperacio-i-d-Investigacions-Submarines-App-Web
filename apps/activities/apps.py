from django.apps import AppConfig


class ActivitiesConfig(AppConfig):
    name = "apps.activities"
    verbose_name = "Activitats (cursos i sortides)"

    def ready(self):
        # RGPD (M02-8): el nucli crida els mòduls registrats; no importa mai el 02.
        from apps.core import events
        from apps.core import privacy as core_privacy

        from . import charges, privacy

        # 049 (T-M02-10): una inscripció es confirma quan el seu càrrec es paga.
        events.subscribe(events.CHARGE_PAID, charges.on_charge_paid)

        # Abast per objecte (T-M02-04a): «les seves sessions» i «les seves activitats».
        from apps.core.permission_catalog import SCOPE_OWN_ACTIVITIES, SCOPE_OWN_SESSIONS
        from apps.core.permissions import register_scope_check

        from . import permissions

        register_scope_check(SCOPE_OWN_SESSIONS, permissions.teaches)
        register_scope_check(SCOPE_OWN_ACTIVITIES, permissions.responsible_for)

        # VC-55 (addenda de la 104): la destinació de les homologacions, una agència activa.
        from apps.core import business_settings

        from . import catalogue

        business_settings.register_check(catalogue.TARGET_AGENCY_KEY, catalogue.check_target_agency)
        business_settings.register_check(
            catalogue.LICENCE_CATEGORY_KEY, catalogue.check_licence_category
        )
        business_settings.register_check(
            catalogue.HOMOLOGATION_DEPARTMENT_KEY, catalogue.check_homologation_department
        )
        from . import filings  # P-530: el tipus de la primera llicència inclosa

        business_settings.register_check(
            filings.FIRST_LICENCE_TYPE_KEY, filings.check_first_licence_type
        )

        # T-M02-04b (L-M02-05; decisió 101): qui perd el rol d'instructor surt de les sessions
        # futures, dins la mateixa transacció i a nom de qui ha retirat el rol.
        from django.db.models.signals import post_save

        from apps.core.models import AccountRole

        post_save.connect(_on_role_saved, sender=AccountRole, dispatch_uid="activities.role_saved")

        core_privacy.register(
            "activitats",
            core_privacy.Module(
                export=privacy.export,
                anonymise=privacy.anonymise,
                audit_targets=privacy.audit_targets,
                describe=privacy.describe,
            ),
        )


def _on_role_saved(sender, instance, **kwargs):
    from apps.core.models import Role

    from . import sessions

    if instance.removed_at is None or instance.role.code != Role.Code.INSTRUCTOR:
        return
    sessions.release_former_instructors(actor=instance.removed_by)
