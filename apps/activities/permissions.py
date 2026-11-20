"""Permisos del 02 (T-M02-33 i T-M02-38; matriu inicial de la 059, «02 Activitats», i addenda de
llocs). Els permisos mateixos (abasts i configuració inicial) són al catàleg comú
(`apps/core/permission_catalog.py`); la matriu vigent és a la base de dades i l'edita
l'administrador.

Cada servei del 02 que canvia dades crida `require(by, CODI)` abans de fer res: sense el permís
amb edició, «no trobat» (Http404), també fora d'una vista. El compte personal i un actor que no és
un compte no tenen mai permisos de rol (059, punt 4.2). L'abast per objecte («les seves sessions»)
és de la T-M02-04. AC1 a AC4 són públics o propis, sense permís de rol.
"""

from django.http import Http404

from apps.core.permissions import has_perm

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
AC21 = PLACES_VIEW = "activities.places.view"
AC22 = PLACES_MANAGE = "activities.places.manage"
AC23 = MATERIAL_COST = "activities.material_cost.edit"
C3 = STUDENT_FIELDS = "activities.field.student_for_instructor"
C7 = MATERIAL_COST_FIELD = "activities.field.material_cost"


def can(by, code, *, write=True) -> bool:
    """Per mostrar o no una acció. El control és el del servei (`require`)."""
    from apps.accounts.models import Account

    return isinstance(by, Account) and has_perm(by, code, write=write)


def require(by, code, *, write=True) -> None:
    """Sense el permís, «no trobat», sense revelar res (RN-RP-01)."""
    if not can(by, code, write=write):
        raise Http404
