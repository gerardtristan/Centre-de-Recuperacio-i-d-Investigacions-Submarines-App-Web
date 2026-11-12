"""Permisos del 02 (T-M02-33; matriu inicial de la 059, «02 Activitats»; CA-RP-13).

Un sol lloc per als codis del mòdul i per al que demana cada ruta, com
`apps/members/permissions.py`. Els permisos mateixos (abasts i configuració inicial) són al catàleg
comú (`apps/core/permission_catalog.py`); la matriu vigent és a la base de dades i l'edita
l'administrador.

- **Serveis.** Cada servei del 02 que canvia dades crida `require(by, CODI)` abans de fer res: un
  compte sense el permís amb edició rep «no trobat» (Http404), també si el servei es crida fora
  d'una vista. El compte personal i un actor que no és un compte no tenen mai permisos de rol
  (059, punt 4.2); el sistema (tasques de la cua) no passa per aquí.
- **Rutes.** `ROUTES` és buit perquè el 02 encara no té cap vista (T-M02-05 i T-M02-06). Cada ruta
  nova s'hi ha de declarar; la prova per cel·la falla si n'apareix una que no hi és.
- **Per objecte.** L'abast «les seves sessions» (AC8, AC9, AC10a, AC10b, AC12, AC20 i C3) el
  comprova `permissions.register_scope_check`, que és de la T-M02-04. Mentre no hi sigui, el motor
  no deixa passar cap objecte amb aquest abast.
- **No declarats:** AC1 a AC4 (públic o propi, sense permís de rol) i CF1 i CF2 (mòdul 11).
"""

from django.http import Http404

from apps.core.permissions import has_perm

PUBLIC = "public"
OWN = "own"
READ, WRITE = False, True

AC5 = ENROL_IN_PERSON = "activities.enrol_in_person"
AC6 = CATALOGUE = "activities.catalogue.manage"
AC7 = MANAGE = "activities.manage"
AC8 = PARTICIPANTS = "activities.participants.view"
AC9 = ATTENDANCE = "activities.attendance.record"
AC10A = ASSESSMENT = "activities.assessment.record"
AC10B = REINFORCEMENT_PROPOSE = "activities.reinforcement.propose"
AC11 = REINFORCEMENT_DECIDE = "activities.reinforcement.decide"
AC12 = OUTCOME = "activities.outcome.record"
AC13 = CERTIFICATE = "activities.certificate.issue"
AC14 = ENVIRONMENT = "activities.environment.manage"
AC15 = MESSAGE = "activities.message.send"
AC16 = WAITLIST = "activities.waitlist.manage"
AC17 = REFUND_PROPOSE = "activities.refund.propose"
AC18 = REFUND_EXECUTE = "activities.refund.execute"
AC19 = INCOME = "activities.income.view"
AC20 = REPORTS = "activities.reports.view"
C3 = STUDENT_FIELDS = "activities.field.student_for_instructor"

# Ruta → el que demana (com al 01). Encara no hi ha cap vista.
ROUTES: dict = {}


def can(by, code, *, write=True, permissions=None) -> bool:
    """Per mostrar o no una acció. El control és el del servei (`require`)."""
    from apps.accounts.models import Account

    return isinstance(by, Account) and has_perm(by, code, write=write, permissions=permissions)


def require(by, code, *, write=True) -> None:
    """Sense el permís, «no trobat», sense revelar res (RN-RP-01)."""
    if not can(by, code, write=write):
        raise Http404
