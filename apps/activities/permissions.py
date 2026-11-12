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
- **Per objecte** (T-M02-04; RN-43 de la 00, RN-RP-04; CA-M02-16). L'abast «les seves sessions»
  (AC8, AC9, AC10a, AC10b, AC12, AC20 i C3) el comprova `teaches`, registrada al motor comú: una
  sessió és «seva» si la persona del compte hi fa classe, i una activitat, si fa classe en alguna
  de les seves sessions no cancel·lades. Val per a qualsevol rol que tingui el permís amb aquest
  abast, no només per al d'instructor. `require(by, CODI, objecte)` respon «no trobat» fora de
  l'abast i en deixa l'intent al registre; `sessions_for` dona les sessions que es poden llistar.
  **`require` amb objecte s'ha de cridar abans d'obrir la transacció del servei:** si no, el
  «no trobat» desfaria també l'entrada del registre.
- **No declarats:** AC1 a AC4 (públic o propi, sense permís de rol) i CF1 i CF2 (mòdul 11).
"""

from django.http import Http404

from apps.core import audit
from apps.core.permission_catalog import SCOPE_OWN_SESSIONS
from apps.core.permissions import has_perm, register_scope_check, scope_for

from .models import Activity, Session

OUT_OF_SCOPE = "activities.out_of_scope"  # CA-M02-16: intent sobre un objecte que no és seu

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


def teaches(account, obj) -> bool:
    """«Les seves sessions»: la persona del compte fa classe a la sessió, o en alguna sessió no
    cancel·lada de l'activitat. Qualsevol altre objecte queda fora de l'abast."""
    person_id = getattr(account, "person_id", None)
    if person_id is None:
        return False
    if isinstance(obj, Session):
        return obj.instructors.filter(pk=person_id).exists()
    if isinstance(obj, Activity):
        return Session.objects.filter(activity=obj, cancelled=False, instructors=person_id).exists()
    return False


register_scope_check(SCOPE_OWN_SESSIONS, teaches)


def can(by, code, obj=None, *, write=True, permissions=None) -> bool:
    """Per mostrar o no una acció. El control és el del servei o la vista (`require`)."""
    from apps.accounts.models import Account

    return isinstance(by, Account) and has_perm(by, code, obj, write=write, permissions=permissions)


def require(by, code, obj=None, *, write=True, request=None) -> None:
    """Sense el permís, «no trobat», sense revelar res (RN-RP-01). Amb `obj`, també ha de caure
    dins l'abast: si el compte té el permís però l'objecte no és seu, l'intent queda al registre
    (CA-M02-16)."""
    if not can(by, code, write=write):
        raise Http404
    if obj is not None and not can(by, code, obj, write=write):
        audit.record(
            OUT_OF_SCOPE, actor=by, target=obj, details={"permission": code}, request=request
        )
        raise Http404


def sessions_for(by, code, *, write=True):
    """Les sessions sobre les quals el compte pot fer `code`: totes, només les seves o cap."""
    if not can(by, code, write=write):
        return Session.objects.none()
    if scope_for(by, code) == SCOPE_OWN_SESSIONS:
        return Session.objects.filter(instructors=by.person_id)
    return Session.objects.all()
