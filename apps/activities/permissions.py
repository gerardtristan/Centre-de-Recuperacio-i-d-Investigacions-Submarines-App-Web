"""Permisos del 02 (T-M02-33 i T-M02-38; matriu inicial de la 059, «02 Activitats», i addenda de
llocs). Els permisos mateixos (abasts i configuració inicial) són al catàleg comú
(`apps/core/permission_catalog.py`); la matriu vigent és a la base de dades i l'edita
l'administrador.

Cada servei del 02 que canvia dades crida `require(by, CODI)` abans de fer res: sense el permís
amb edició, «no trobat» (Http404), també fora d'una vista. El compte personal i un actor que no és
un compte no tenen mai permisos de rol (059, punt 4.2). AC1 a AC4 són públics o propis, sense
permís de rol.

**Per objecte** (T-M02-04a; RN-43 de la 00, RN-RP-04; CA-M02-16). `ActivitiesConfig.ready` registra
al motor comú les comprovacions de dos abasts, que valen per a qualsevol rol i qualsevol mòdul que
els faci servir (el 06 per a LC10, el 09 per a MG1, MG5 i MG6):

- **«les seves sessions»** (`teaches`): la persona del compte fa classe a la sessió, o en alguna
  sessió no cancel·lada de l'activitat;
- **«les seves activitats»** (`responsible_for`): la persona del compte és la responsable de
  l'activitat (o de l'activitat de la sessió).

Un objecte d'un altre mòdul hi entra pel seu camp `activity` (o `session`). `require(by, CODI,
objecte)` respon «no trobat» fora de l'abast i en deixa l'intent al registre; s'ha de cridar abans
d'obrir la transacció del servei, perquè el «no trobat» no desfaci l'entrada.
"""

from django.http import Http404

from apps.core import audit
from apps.core.permission_catalog import SCOPE_OWN_SESSIONS
from apps.core.permissions import has_perm, scope_for

from .models import Activity, Session

OUT_OF_SCOPE = "activities.out_of_scope"  # CA-M02-16: intent sobre un objecte que no és seu

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
AC24 = CARD_PHOTOS_VIEW = "activities.card_photos.view"  # addenda de la 104
AC25 = CARD_PHOTOS_MANAGE = "activities.card_photos.manage"
AC26 = FILINGS = "activities.filings.manage"
AC27 = FIRST_LICENCE_VIEW = "activities.first_licence.view"  # addenda de la 104
AC28 = FIRST_LICENCE_MANAGE = "activities.first_licence.manage"
C3 = STUDENT_FIELDS = "activities.field.student_for_instructor"
C7 = MATERIAL_COST_FIELD = "activities.field.material_cost"


def _unwrap(obj):
    """Una sessió, una activitat o un objecte d'un altre mòdul que en porti una."""
    if isinstance(obj, Session | Activity):
        return obj
    return getattr(obj, "session", None) or getattr(obj, "activity", None)


def teaches(account, obj) -> bool:
    """«Les seves sessions»."""
    person_id, obj = getattr(account, "person_id", None), _unwrap(obj)
    if person_id is None:
        return False
    if isinstance(obj, Session):
        return obj.instructors.filter(pk=person_id).exists()
    if isinstance(obj, Activity):
        return Session.objects.filter(activity=obj, cancelled=False, instructors=person_id).exists()
    return False


def responsible_for(account, obj) -> bool:
    """«Les seves activitats»."""
    person_id, obj = getattr(account, "person_id", None), _unwrap(obj)
    if isinstance(obj, Session):
        obj = obj.activity
    return person_id is not None and isinstance(obj, Activity) and obj.responsible_id == person_id


def can(by, code, obj=None, *, write=True) -> bool:
    """Per mostrar o no una acció. El control és el del servei (`require`)."""
    from apps.accounts.models import Account

    return isinstance(by, Account) and has_perm(by, code, obj, write=write)


def require(by, code, obj=None, *, write=True, request=None) -> None:
    """Sense el permís, «no trobat», sense revelar res (RN-RP-01). Amb `obj`, també ha de caure
    dins l'abast; si no, l'intent queda al registre (CA-M02-16)."""
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
