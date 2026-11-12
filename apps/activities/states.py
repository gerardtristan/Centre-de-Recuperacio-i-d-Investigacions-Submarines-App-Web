"""Estats i transicions d'una activitat (T-M02-03; RN-M02-02 i RN-M02-20; estats de M02-5).

Un sol lloc canvia `Activity.status`. Cada canvi es fa amb la fila bloquejada i deixa una entrada
al registre d'activitat amb l'estat anterior, el nou, qui l'ha fet i el motiu.

**Taula (RN-M02-02)**

- `draft → open → registration_closed → in_progress → done → closed`.
- Sortides: `open → done` i `registration_closed → done`; no fan servir `in_progress`.
- Qualsevol estat abans de `done` → `cancelled`, amb motiu.
- Cap pas enrere, tret de `registration_closed → open` (reobrir inscripcions abans de l'inici).
- `done → closed` és a la taula, però aquí no hi ha cap funció que el faci: només el fa el 09
  (`margins.close_activity`) amb les comprovacions de tancament de la T-M02-22.

**Qui fa cada pas**

- El responsable (permís AC7 amb edició; sense, «no trobat»): `publish`, `close_registration`,
  `reopen_registration`, `mark_done` i `cancel`.
- El sistema (`advance_by_clock`, sense compte; al registre surt com a «sistema»): tanca les
  inscripcions quan arriba la data límit i posa un curs «en curs» quan comença la primera sessió.

**Concrecions d'implementació** (dins de les regles; al diari de la T-M02-03)

- Publicar és només `draft → open` i demana que la data límit d'inscripció encara no hagi passat.
  `registration_closed → open` és reobrir, amb les seves condicions.
- Reobrir demana una data límit futura que no passi del dia d'inici (és el que vol dir «abans de
  l'inici»); es pot donar en reobrir.
- RN-M02-20, «la data de l'última sessió»: el dia de l'última sessió no cancel·lada del curs; si
  no en té cap, o és una sortida, el dia de final de l'activitat (`ends_on`).
- Un curs sense cap sessió passa a «en curs» el dia d'inici.
- `mark_done` aplica abans els passos del sistema que ja toquen, perquè el responsable no depengui
  de si la cua ha passat.

**Senyal:** `mark_done` envia `extensions.activity_done` dins la mateixa transacció (T-M02-09).

**Omplir les places no tanca les inscripcions** (decisió 088): l'activitat continua `open` i qui
arriba després va a la llista d'espera. El sistema només tanca per la data límit.

**Fora d'aquesta peça:** l'efecte de cancel·lar sobre inscripcions i càrrecs (T-M02-15), els
avisos als inscrits (T-M02-21) i els esdeveniments `activity.cancelled` (T-M02-35).
"""

import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit

from . import extensions, permissions
from .models import Activity

S = Activity.Status
K = Activity.Kind

STATUS_CHANGED = "activities.activity.status_changed"
CLOCK_ORIGIN = "activities.clock"

_BEFORE_DONE = (S.DRAFT, S.OPEN, S.REGISTRATION_CLOSED, S.IN_PROGRESS)
EDITABLE_STATUSES = _BEFORE_DONE  # una activitat es pot editar fins que es fa o es cancel·la
_TRANSITIONS = {
    K.COURSE: {
        S.DRAFT: {S.OPEN, S.CANCELLED},
        S.OPEN: {S.REGISTRATION_CLOSED, S.CANCELLED},
        S.REGISTRATION_CLOSED: {S.OPEN, S.IN_PROGRESS, S.CANCELLED},
        S.IN_PROGRESS: {S.DONE, S.CANCELLED},
        S.DONE: {S.CLOSED},
    },
    K.OUTING: {
        S.DRAFT: {S.OPEN, S.CANCELLED},
        S.OPEN: {S.REGISTRATION_CLOSED, S.DONE, S.CANCELLED},
        S.REGISTRATION_CLOSED: {S.OPEN, S.DONE, S.CANCELLED},
        S.DONE: {S.CLOSED},
    },
}


class InvalidTransition(ValidationError):
    """El pas d'estat no és a la taula de RN-M02-02 (M02-8)."""


def allowed_targets(activity) -> frozenset:
    """Estats als quals pot passar l'activitat des del seu estat, segons si és curs o sortida."""
    return frozenset(_TRANSITIONS[activity.kind].get(activity.status, ()))


def is_editable(activity) -> bool:
    """Una activitat es pot editar fins que es marca com a feta o es cancel·la."""
    return activity.status in _BEFORE_DONE


def _lock(activity) -> Activity:
    return Activity.objects.select_for_update().get(pk=activity.pk)


def _apply(locked, target, *, actor, now, reason="", request=None) -> None:
    if target not in allowed_targets(locked):
        raise InvalidTransition(
            _("Una activitat «%(old)s» no pot passar a «%(new)s».")
            % {"old": locked.get_status_display(), "new": S(target).label}
        )
    old = locked.status
    locked.status = target
    fields = ["status", "updated_at"]
    if target == S.OPEN and locked.published_at is None:
        locked.published_at = now
        fields.append("published_at")
    if target == S.DONE:
        locked.done_at = now
        fields.append("done_at")
    if target == S.CANCELLED:
        locked.cancellation_reason = reason
        fields.append("cancellation_reason")
    locked.save(update_fields=fields)
    audit.record(
        STATUS_CHANGED,
        actor=actor,
        target=locked,
        field="status",
        old=old,
        new=target,
        reason=reason,
        request=request,
    )


def _refresh(activity, locked) -> Activity:
    for name in ("status", "published_at", "done_at", "cancellation_reason", "updated_at"):
        setattr(activity, name, getattr(locked, name))
    return activity


def _start_of(day: datetime.date) -> datetime.datetime:
    return timezone.make_aware(datetime.datetime.combine(day, datetime.time.min))


def _live_sessions(activity):
    return activity.sessions.filter(cancelled=False)


def _course_started(activity, now) -> bool:
    first = _live_sessions(activity).order_by("starts_at").values_list("starts_at", flat=True)
    start = first.first() or _start_of(activity.starts_on)
    return start <= now


def last_day(activity) -> datetime.date:
    """El dia a partir del qual es pot marcar com a feta (RN-M02-20)."""
    if activity.kind == K.COURSE:
        last = _live_sessions(activity).order_by("-starts_at").values_list("starts_at", flat=True)
        moment = last.first()
        if moment is not None:
            return timezone.localdate(moment)
    return activity.ends_on


def _due_by_clock(activity, now):
    """El pas que el sistema ja hauria d'haver fet, o `None`."""
    if activity.status == S.OPEN and activity.registration_closes_at <= now:
        return S.REGISTRATION_CLOSED
    if (
        activity.kind == K.COURSE
        and activity.status == S.REGISTRATION_CLOSED
        and _course_started(activity, now)
    ):
        return S.IN_PROGRESS
    return None


def _catch_up(locked, now) -> list[str]:
    done = []
    while (target := _due_by_clock(locked, now)) is not None:
        _apply(locked, target, actor=audit.system(CLOCK_ORIGIN), now=now)
        done.append(target)
    return done


# --- Passos del responsable (AC7) -----------------------------------------------------------------


@transaction.atomic
def publish(activity, *, by, now=None, request=None) -> Activity:
    """`draft → open`: surt al llistat públic (T-M02-08) i s'hi pot inscriure gent (T-M02-11)."""
    permissions.require(by, permissions.MANAGE)
    now = now or timezone.now()
    locked = _lock(activity)
    if locked.status != S.DRAFT:
        # `registration_closed → open` també és a la taula, però és reobrir, amb les seves
        # condicions (`reopen_registration`): publicar no les pot saltar.
        raise InvalidTransition(_("Només es publica una activitat en esborrany."))
    if locked.registration_closes_at <= now:
        raise ValidationError(
            _("La data límit d'inscripció ja ha passat: canvia-la abans de publicar.")
        )
    _apply(locked, S.OPEN, actor=by, now=now, request=request)
    return _refresh(activity, locked)


@transaction.atomic
def close_registration(activity, *, by, now=None, request=None) -> Activity:
    """`open → registration_closed` a mà, abans de la data límit."""
    permissions.require(by, permissions.MANAGE)
    locked = _lock(activity)
    _apply(locked, S.REGISTRATION_CLOSED, actor=by, now=now or timezone.now(), request=request)
    return _refresh(activity, locked)


@transaction.atomic
def reopen_registration(activity, *, by, closes_at=None, now=None, request=None) -> Activity:
    """`registration_closed → open`, l'únic pas enrere. Cal una data límit futura que no passi
    del dia d'inici; si la que hi ha ja ha passat, se n'ha de donar una de nova."""
    permissions.require(by, permissions.MANAGE)
    now = now or timezone.now()
    locked = _lock(activity)
    if locked.status != S.REGISTRATION_CLOSED:
        raise InvalidTransition(_("Només es reobren les inscripcions d'una activitat tancada."))
    deadline = closes_at or locked.registration_closes_at
    if deadline <= now:
        raise ValidationError(_("Per reobrir les inscripcions cal una data límit futura."))
    if timezone.localdate(deadline) > locked.starts_on:
        raise ValidationError(_("La data límit d'inscripció no pot passar del dia d'inici."))
    if deadline != locked.registration_closes_at:
        audit.record_changes(
            "activities.activity.updated",
            actor=by,
            target=locked,
            changes={"registration_closes_at": (locked.registration_closes_at, deadline)},
            request=request,
        )
        locked.registration_closes_at = deadline
        locked.save(update_fields=["registration_closes_at", "updated_at"])
        activity.registration_closes_at = deadline
    _apply(locked, S.OPEN, actor=by, now=now, request=request)
    return _refresh(activity, locked)


@transaction.atomic
def mark_done(activity, *, by, now=None, request=None) -> Activity:
    """Marca l'activitat com a feta. Mai abans del dia de l'última sessió (curs) o de la sortida
    (RN-M02-20)."""
    permissions.require(by, permissions.MANAGE)
    now = now or timezone.now()
    locked = _lock(activity)
    _catch_up(locked, now)
    if S.DONE not in allowed_targets(locked):
        raise InvalidTransition(
            _("Una activitat «%(old)s» no es pot marcar com a feta.")
            % {"old": locked.get_status_display()}
        )
    if timezone.localdate(now) < last_day(locked):
        raise ValidationError(
            _("No es pot marcar com a feta abans del dia de l'última sessió o de la sortida.")
        )
    _apply(locked, S.DONE, actor=by, now=now, request=request)
    _refresh(activity, locked)
    # Dins la mateixa transacció: si un mòdul subscrit falla, l'activitat no queda feta a mitges.
    extensions.activity_done.send(sender=Activity, activity=activity, by=by)
    return activity


@transaction.atomic
def cancel(activity, *, by, reason, now=None, request=None) -> Activity:
    """Cancel·la una activitat que encara no s'ha fet, amb motiu obligatori. L'efecte sobre les
    inscripcions i els càrrecs és de la T-M02-15."""
    permissions.require(by, permissions.MANAGE)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal escriure el motiu de la cancel·lació."))
    locked = _lock(activity)
    _apply(locked, S.CANCELLED, actor=by, now=now or timezone.now(), reason=reason, request=request)
    return _refresh(activity, locked)


# --- Passos del sistema ---------------------------------------------------------------------------


def advance_by_clock(now=None) -> list[tuple[int, str]]:
    """Fa els passos que depenen del rellotge: tancar inscripcions a la data límit i posar «en
    curs» els cursos que han començat. Es pot cridar tantes vegades com calgui: només actua sobre
    el que toca. Torna (activitat, estat nou) de cada pas fet."""
    now = now or timezone.now()
    done = []
    candidates = Activity.objects.filter(
        Q(status=S.OPEN, registration_closes_at__lte=now)
        | Q(status=S.REGISTRATION_CLOSED, kind=K.COURSE)
    ).values_list("pk", flat=True)
    for pk in list(candidates):
        with transaction.atomic():
            locked = Activity.objects.select_for_update().get(pk=pk)
            done.extend((pk, target) for target in _catch_up(locked, now))
    return done
