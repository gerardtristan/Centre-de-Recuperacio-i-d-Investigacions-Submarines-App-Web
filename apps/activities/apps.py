from django.apps import AppConfig


class ActivitiesConfig(AppConfig):
    name = "apps.activities"
    verbose_name = "Activitats (cursos i sortides)"

    def ready(self):
        from django.db.models.signals import post_save

        from apps.core import privacy as core_privacy
        from apps.core.models import AccountRole

        # Registra «les seves sessions» al motor de permisos (T-M02-04).
        from . import (
            permissions,  # noqa: F401
            privacy,
        )

        # RGPD (M02-8): el 02 registra a la 00 la seva part de l'exportació i de
        # l'anonimització. La 00 no importa cap mòdul.
        core_privacy.register(
            "activitats",
            core_privacy.Module(
                export=privacy.export_personal_data,
                anonymise=privacy.anonymise,
                audit_targets=privacy.audit_targets,
                describe=privacy.describe,
            ),
        )

        post_save.connect(
            _on_role_saved, sender=AccountRole, dispatch_uid="activities.role_removed"
        )


def _on_role_saved(sender, instance, **kwargs):
    """L-M02-05 (decisió 086): en retirar el rol d'instructor, la persona surt de les sessions
    futures on feia classe, dins la mateixa transacció i a nom de qui ha retirat el rol."""
    from apps.core.models import Role

    from . import sessions

    if instance.removed_at is None or instance.role.code != Role.Code.INSTRUCTOR:
        return
    sessions.release_former_instructors(actor=instance.removed_by)
