"""Passar llista i incidències (T-M02-16, part de servei; P-M02-E; RN-M02-17; CA-M02-16 i
CA-M02-17; AC9; C3).

- **Qui.** Qui té AC9. Amb l'abast «les seves sessions» (l'instructor), només les sessions on fa
  classe: fora, «no trobat» i l'intent queda al registre (CA-M02-16). Una sortida no té sessions:
  la llista del dia es comprova sobre l'activitat.
- **Què es veu** (C3; M02-4, «Per objecte»): dels inscrits **confirmats**, nom, titulacions i si
  la llicència és vigent el dia (sí o no; «en tràmit» és no). Qui té AC9 sobre totes les
  activitats veu, a més, els pendents de pagament, a part, perquè ho resolgui (P-M02-E pas 4);
  l'instructor no. Cap correu, telèfon, document ni pagament.
- **Marcar** (`mark`): present o absent, per sessió (curs) o pel dia (sortida). És **idempotent**:
  tornar a enviar la mateixa marca no crea res ni escriu al registre (CA-M02-17: el mòbil la
  reenvia sola quan torna la cobertura). Corregir-la sí que queda al registre, amb el valor
  anterior.
- **Incidències** (`add_incident`): només operatives. Només s'hi afegeixen. **Mai dades de salut**
  (RN-M02-17): ho diu el text d'ajuda (`INCIDENT_HELP`); un accident segueix el protocol del club
  fora de la plataforma.

**Concrecions d'implementació** (dins de les regles; al diari de la T-M02-16)

- Només es passa llista d'una activitat publicada que no s'ha cancel·lat (ni tancat), i no abans
  del dia de la sessió (o del primer dia de la sortida).
- Només es marca qui té la inscripció confirmada.
- L'assistència d'una sortida de més d'un dia és una sola marca (M02-6: «el dia de la sortida»).

**Fora d'aquesta peça:** la pantalla del mòbil amb el reintent (vistes i plantilles, amb la ruta
`/gestio/activitats/{id}/llista`), les classes de reforç (T-M02-18) i l'avaluació (T-M02-17).
"""

from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.core import audit
from apps.core.permission_catalog import SCOPE_OWN_SESSIONS
from apps.core.permissions import scope_for
from apps.licences import services as licences

from . import certifications, permissions
from .models import Activity, Attendance, Enrolment, Incident

S = Enrolment.Status
A = Activity.Status
MARKED = "activities.attendance.marked"
INCIDENT_ADDED = "activities.incident.added"
ROLL_STATUSES = (A.OPEN, A.REGISTRATION_CLOSED, A.IN_PROGRESS, A.DONE)
MAX_INCIDENT = Incident._meta.get_field("description").max_length
INCIDENT_HELP = gettext_lazy(
    "Només dades operatives. Sense dades de salut: un accident segueix el protocol del club."
)


@dataclass(frozen=True)
class RollRow:
    enrolment_id: int
    name: str
    certifications: tuple[str, ...]
    licence_valid: bool
    present: bool | None  # None = encara no s'ha marcat


@dataclass(frozen=True)
class Roll:
    activity: Activity
    session: object
    can_record: bool
    rows: tuple[RollRow, ...] = field(default=())
    unpaid: tuple[RollRow, ...] = field(default=())  # buit per a l'abast «les seves sessions»

    @property
    def present(self) -> int:
        return sum(1 for row in self.rows if row.present)

    @property
    def unmarked(self) -> int:
        return sum(1 for row in self.rows if row.present is None)


def _target(activity, session):
    """L'objecte sobre el qual es comprova l'abast: la sessió, si n'hi ha; si no, l'activitat."""
    return session if session is not None else activity


def _check_session(activity, session) -> None:
    if activity.kind == Activity.Kind.COURSE:
        if session is None or session.activity_id != activity.pk:
            raise Http404
        if session.cancelled:
            raise ValidationError(_("Aquesta sessió està cancel·lada: no se'n passa llista."))
    elif session is not None:
        raise Http404


def day_of(activity, session):
    """El dia de la llista: el de la sessió o el primer de la sortida."""
    return timezone.localdate(session.starts_at) if session is not None else activity.starts_on


def can_record_now(activity, session, today=None) -> bool:
    today = today or timezone.localdate()
    return activity.status in ROLL_STATUSES and day_of(activity, session) <= today


def _licence_valid(person, day) -> bool:
    info = licences.current(person, day)
    return info is not None and info.status == licences.CurrentStatus.ACTIVE


def roll(activity, session=None, *, viewer, today=None, request=None) -> Roll:
    """La llista per passar: «no trobat» sense AC9 o fora de l'abast (i queda al registre)."""
    target = _target(activity, session)
    permissions.require(viewer, permissions.ATTENDANCE, target, write=False, request=request)
    _check_session(activity, session)
    limited = scope_for(viewer, permissions.ATTENDANCE) == SCOPE_OWN_SESSIONS
    marks = dict(
        Attendance.objects.filter(enrolment__activity=activity, session=session).values_list(
            "enrolment_id", "present"
        )
    )
    statuses = (S.CONFIRMED,) if limited else (S.CONFIRMED, S.PENDING_PAYMENT)
    enrolled = (
        Enrolment.objects.filter(activity=activity, status__in=statuses)
        .select_related("person")
        .order_by("person__last_name", "person__first_name", "id")
    )
    day = day_of(activity, session)
    rows, unpaid = [], []
    for row in enrolled:
        person = row.person
        item = RollRow(
            enrolment_id=row.pk,
            name=f"{person.first_name} {person.last_name}".strip(),
            certifications=tuple(str(c) for c in certifications.of(person)),
            licence_valid=_licence_valid(person, day),
            present=marks.get(row.pk),
        )
        (rows if row.status == S.CONFIRMED else unpaid).append(item)
    return Roll(
        activity=activity,
        session=session,
        can_record=can_record_now(activity, session, today)
        and permissions.can(viewer, permissions.ATTENDANCE, target),
        rows=tuple(rows),
        unpaid=tuple(unpaid),
    )


def mark(enrolment, session=None, *, present, by, today=None, request=None) -> Attendance:
    """Marca una persona present o absent. Idempotent: la mateixa marca dues vegades no canvia
    res. L'abast es comprova abans d'obrir la transacció, perquè l'intent quedi al registre."""
    activity = enrolment.activity
    permissions.require(by, permissions.ATTENDANCE, _target(activity, session), request=request)
    _check_session(activity, session)
    if not isinstance(present, bool):
        raise ValidationError(_("Cal dir si hi és o no hi és."))
    if not can_record_now(activity, session, today):
        raise ValidationError(_("Encara no es pot passar llista d'aquesta activitat."))
    with transaction.atomic():
        row = Enrolment.objects.select_for_update().get(pk=enrolment.pk)
        if row.status != S.CONFIRMED:
            raise ValidationError(_("Només es passa llista de qui té la inscripció confirmada."))
        current = Attendance.objects.filter(enrolment=row, session=session).first()
        if current is not None and current.present == present:
            return current
        old = current.present if current is not None else None
        current = current or Attendance(enrolment=row, session=session)
        current.present = present
        current.recorded_by = by
        current.recorded_at = timezone.now()
        current.save()
        audit.record(
            MARKED,
            actor=by,
            target=current,
            field="present",
            old=old,
            new=present,
            details={"enrolment": row.pk, "session": session.pk if session else None},
            request=request,
        )
        return current


def incidents(activity, session=None, *, viewer, request=None):
    """Les incidències d'una activitat (o d'una sessió), de la més nova a la més antiga."""
    permissions.require(
        viewer, permissions.ATTENDANCE, _target(activity, session), write=False, request=request
    )
    rows = Incident.objects.filter(activity=activity).select_related("session")
    return rows.filter(session=session) if session is not None else rows


def add_incident(activity, *, by, kind, description, session=None, request=None) -> Incident:
    """Afegeix una incidència operativa. Sense dades de salut (RN-M02-17)."""
    permissions.require(by, permissions.ATTENDANCE, _target(activity, session), request=request)
    if session is not None and session.activity_id != activity.pk:
        raise Http404
    if activity.status not in ROLL_STATUSES:
        raise ValidationError(_("No es poden registrar incidències d'aquesta activitat."))
    if kind not in Incident.Kind.values:
        raise ValidationError(_("Classe d'incidència desconeguda."))
    description = (description or "").strip()
    if not description:
        raise ValidationError(_("Cal descriure la incidència."))
    if len(description) > MAX_INCIDENT:
        raise ValidationError(
            _("La descripció no pot passar de %(max)s caràcters.") % {"max": MAX_INCIDENT}
        )
    with transaction.atomic():
        incident = Incident.objects.create(
            activity=activity,
            session=session,
            kind=kind,
            description=description,
            recorded_by=by,
            recorded_at=timezone.now(),
        )
        # Sense la descripció: el registre no ha de repetir text lliure.
        audit.record(
            INCIDENT_ADDED,
            actor=by,
            target=incident,
            details={"activity": activity.pk, "kind": kind},
            request=request,
        )
    return incident
