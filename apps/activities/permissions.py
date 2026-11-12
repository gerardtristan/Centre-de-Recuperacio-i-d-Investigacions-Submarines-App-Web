"""Permisos del 02 (T-M02-33; matriu inicial de la 059, «02 Activitats»; CA-RP-13).

Un sol lloc per als codis del mòdul i per al que demana cada ruta, com
`apps/members/permissions.py`. Els permisos mateixos (abasts i configuració inicial) són al catàleg
comú (`apps/core/permission_catalog.py`); la matriu vigent és a la base de dades i l'edita
l'administrador.

- **Serveis.** Cada servei del 02 que canvia dades crida `require(by, CODI)` abans de fer res: un
  compte sense el permís amb edició rep «no trobat» (Http404), també si el servei es crida fora
  d'una vista. El compte personal i un actor que no és un compte no tenen mai permisos de rol
  (059, punt 4.2); el sistema (tasques de la cua) no passa per aquí.
- **Rutes.** `ROUTES` diu què demana cada ruta del mòdul, per mètode, com al 01. Cada ruta nova
  s'hi ha de declarar: la prova per cel·la (`tests/test_route_permissions.py`) falla si n'apareix
  una que no hi és, i compara la resposta real de cada ruta per a cada rol.
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


def _both(*needs):
    """GET i POST demanen el mateix (el permís es comprova abans que el mètode)."""
    return {"GET": needs, "POST": needs}


def _read_then_write(code):
    """Pantalles que es llegeixen amb el permís i hi desen amb edició."""
    return {"GET": ((code, READ),), "POST": ((code, WRITE),)}


# Ruta → el que demana (com al 01).
ROUTES: dict = {
    # --- Públiques (T-M02-08; AC1): activitats publicades, sense cap dada personal ---
    "activities:list": PUBLIC,
    "activities:detail": PUBLIC,
    # --- Catàlegs (T-M02-05; AC6) ---
    "administration:catalogue_courses": _both((AC6, READ)),
    "administration:catalogue_specialities": _both((AC6, READ)),
    "administration:catalogue_course_add": _both((AC6, WRITE)),
    "administration:catalogue_speciality_add": _both((AC6, WRITE)),
    "administration:catalogue_entry_edit": _both((AC6, WRITE)),
    "administration:catalogue_entry_prices": _both((AC6, WRITE)),
    "administration:catalogue_entry_active": _both((AC6, WRITE)),
    "administration:outing_types": _read_then_write(AC6),
    "administration:outing_type_active": _both((AC6, WRITE)),
    "administration:outing_subtype_active": _both((AC6, WRITE)),
    "administration:outing_type_mode": _both((AC6, WRITE)),  # T-M02-29
    "administration:certification_levels": _read_then_write(AC6),
    "administration:certification_level_active": _both((AC6, WRITE)),
    "administration:projects": _read_then_write(AC6),
    # --- Medi ambient (T-M02-20; AC14: la Junta el té només de consulta) ---
    "administration:environment": _both((AC14, READ)),
    "administration:project_detail": _both((AC14, READ)),
    "administration:activity_results": _read_then_write(AC14),
    # --- Activitats (T-M02-06; AC7) ---
    "administration:activities": _both((AC7, READ)),
    "administration:activity_detail": _both((AC7, READ)),
    "administration:activity_course_add": _both((AC7, WRITE)),
    "administration:activity_outing_add": _both((AC7, WRITE)),
    "administration:activity_edit": _both((AC7, WRITE)),
    "administration:activity_step": _both((AC7, WRITE)),
    "administration:activity_reopen": _both((AC7, WRITE)),
    "administration:activity_cancel": _both((AC7, WRITE)),
    "administration:activity_duplicate": _both((AC7, WRITE)),  # T-M02-07
    "administration:activity_programme": _both((AC7, WRITE)),
    "administration:session_add": _both((AC7, WRITE)),
    "administration:session_edit": _both((AC7, WRITE)),
    "administration:session_cancel": _both((AC7, WRITE)),
}


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
