from django.apps import AppConfig


class MembersConfig(AppConfig):
    name = "apps.members"
    verbose_name = "Socis i carnet"

    def ready(self):
        # RGPD (T-M01-22): el M01 registra a la 00 la seva part de l'exportació i de
        # l'anonimització (contracte M01-8). La 00 no importa cap mòdul.
        from apps.core import business_settings
        from apps.core import privacy as core_privacy

        from . import (
            checks,  # noqa: F401 (registra les comprovacions d'arrencada)
            privacy,
        )
        from . import settings as member_settings

        # T-M01-52: un sol permís per al preu de tots els tipus; la fila diu el nom del tipus.
        business_settings.register_family("members.annual_fee_cents", _type_name)
        # P-360: els recordatoris (VC-02) no poden començar abans de l'avís de renovació.
        business_settings.register_check(
            member_settings.FEE_REMINDER_OFFSETS, member_settings.check_reminders
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


def _type_name(code):
    from .models import MembershipType

    return MembershipType.objects.filter(code=code).values_list("name", flat=True).first() or code
