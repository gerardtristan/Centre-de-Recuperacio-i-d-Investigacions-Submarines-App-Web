"""Sessions d'un curs i programa del dia d'una sortida (T-M02-03d; P-M02-B, pas 2; M02-6; addenda
de llocs, RN-M02-38 i CA-M02-47).

- **Sessions** (`add_session`, `update_session`, `cancel_session`, `set_instructors`): teoria,
  piscina o mar, amb data, hora, un lloc actiu (obligatori, CA-M02-47) i instructors. Una sessió
  no s'esborra: es cancel·la amb motiu. Se'n poden afegir mentre l'activitat no s'hagi fet ni
  cancel·lat.
- **Instructors:** persones amb el rol d'instructor actiu en un compte d'administrador actiu
  (M02-6). Les condicions de RN-M02-26 (soci actiu i llicència tècnica vigent) són de la T-M02-30,
  que depèn del 06.
- **Programa del dia** (`set_programme`): la llista de blocs sencera, en ordre. Qui se n'encarrega
  és una funció («cap d'immersió»), mai un nom ni dades de contacte. El lloc del bloc és opcional:
  buit vol dir el de l'activitat.
- Un lloc desactivat no es tria per a res nou (RN-M02-38); el que ja el té el conserva.
- **Permís:** AC7 amb edició; sense, «no trobat».

El pla no limita les sessions als cursos ni el programa a les sortides (CA-M02-04 parla d'una
activitat amb sessions i blocs), i aquí tampoc es limita.

**Fora d'aquesta peça:** les sessions de reforç (`reinforcement_for`, T-M02-18), l'avís als inscrits
quan canvia una sessió o el programa (RN-M02-18, T-M02-21), treure de les sessions futures qui perd
el rol d'instructor (decisió 101, T-M02-04) i les pantalles (T-M02-06).
"""

import datetime
import re

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit, business_settings
from apps.core.models import AccountRole, Person, Role
from apps.licences import services as licences
from apps.licences.models import LicenceType
from apps.members import services as members

from . import permissions, states
from .models import Activity, Place, ProgrammeBlock, Session

SESSION_ADDED = "activities.session.added"
SESSION_UPDATED = "activities.session.updated"
SESSION_CANCELLED = "activities.session.cancelled"
INSTRUCTORS_CHANGED = "activities.session.instructors_changed"
PROGRAMME_CHANGED = "activities.programme.changed"

SESSION_FIELDS = ("kind", "starts_at", "ends_at", "place", "is_practice")
BLOCK_FIELDS = ("starts_at", "ends_at", "label", "place", "responsible_label")
# Un correu o un telèfon no són una funció: el camp no ha de portar dades de contacte (M02-6).
_CONTACT = re.compile(r"@|\d[\d .-]{5,}\d")


def _editable(activity) -> Activity:
    locked = Activity.objects.select_for_update().get(pk=activity.pk)
    if not states.is_editable(locked):
        raise ValidationError(
            _("Una activitat «%(status)s» ja no es pot editar.")
            % {"status": locked.get_status_display()}
        )
    return locked


def _moment(value) -> datetime.datetime:
    if not isinstance(value, datetime.datetime) or timezone.is_naive(value):
        raise ValidationError(_("Escriu el dia i l'hora d'inici i de final de la sessió."))
    return value


def _place(place, *, current=None) -> None:
    """Un lloc actiu; el que ja hi era, encara que s'hagi desactivat, es pot conservar."""
    if not isinstance(place, Place):
        raise ValidationError(_("Cal triar un lloc de la llista."))
    if not place.active and place != current:
        raise ValidationError(_("Aquest lloc està desactivat."))


def _clean_session(data: dict) -> dict:
    out = dict(data)
    if "kind" in out and out["kind"] not in Session.Kind.values:
        raise ValidationError(_("La sessió ha de ser de teoria, de piscina o de mar."))
    for name in ("starts_at", "ends_at"):
        if name in out:
            _moment(out[name])
    if "is_practice" in out:
        out["is_practice"] = bool(out["is_practice"])
    return out


def instructor_people():
    """Persones que poden fer classe: rol d'instructor actiu en un compte d'administrador actiu."""
    from apps.accounts.models import Account

    return Person.objects.filter(
        pk__in=AccountRole.objects.filter(
            role__code=Role.Code.INSTRUCTOR,
            removed_at__isnull=True,
            admin_account__kind=Account.Kind.ADMIN,
            admin_account__status=Account.Status.ACTIVE,
        ).values("admin_account__person_id"),
        status=Person.Status.ACTIVE,
    )


INSTRUCTOR_MODE_KEY = "activities.instructor_requirements_mode"  # VC-46


def instructor_problems(person, day) -> list[str]:
    """RN-M02-26: què li falta a `person` per fer classe el dia `day` (buit si no li falta res):
    ser soci actiu i tenir la llicència tècnica vigent. Mai la categoria ni el número."""
    problems = []
    if not members.is_member(person, on=day):
        problems.append(_("no és soci actiu"))
    info = licences.current(person, day)
    technical = info is not None and info.category == LicenceType.Category.TECHNICAL
    if not technical or info.status != licences.CurrentStatus.ACTIVE:
        problems.append(_("no té llicència tècnica vigent"))
    return problems


def _check_requirements(people, starts_at) -> None:
    """Amb el mode «bloqueig» (VC-46) no s'assigna qui no compleix RN-M02-26; amb «avís»,
    s'assigna i `instructor_warnings` ho marca al responsable."""
    if business_settings.get(INSTRUCTOR_MODE_KEY) != "block":
        return
    day = timezone.localdate(starts_at)
    failing = [p for p in people if instructor_problems(p, day)]
    if failing:
        names = ", ".join(f"{p.first_name} {p.last_name}".strip() for p in failing)
        raise ValidationError(
            _("No compleixen els requisits per fer classe (soci actiu i llicència tècnica "
              "vigent): %(names)s.") % {"names": names}
        )  # fmt: skip


def instructor_warnings(session) -> dict[int, list[str]]:
    """Els instructors de la sessió que no compleixen RN-M02-26 el dia de la sessió, també si
    han deixat de complir-ho després d'assignar-los (la sessió surt marcada al responsable)."""
    day = timezone.localdate(session.starts_at)
    out = {}
    for person in session.instructors.all():
        problems = instructor_problems(person, day)
        if problems:
            out[person.pk] = problems
    return out


def _instructors(people) -> list[Person]:
    people = list(people or ())
    if any(not isinstance(person, Person) for person in people):
        raise ValidationError(_("Tria els instructors de la llista."))
    allowed = set(
        instructor_people().filter(pk__in=[p.pk for p in people]).values_list("pk", flat=True)
    )
    if any(person.pk not in allowed for person in people):
        raise ValidationError(_("Només pot fer classe qui té el rol d'instructor."))
    return people


@transaction.atomic
def add_session(
    activity,
    *,
    by,
    kind,
    starts_at,
    ends_at,
    place,
    is_practice=False,
    instructors=(),
    request=None,
) -> Session:
    """Afegeix una sessió a l'activitat."""
    permissions.require(by, permissions.MANAGE)
    locked = _editable(activity)
    data = _clean_session(
        {
            "kind": kind,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "is_practice": is_practice,
        }
    )
    _place(place)
    if data["ends_at"] <= data["starts_at"]:
        raise ValidationError(_("La sessió ha d'acabar després de començar."))
    people = _instructors(instructors)
    _check_requirements(people, data["starts_at"])
    session = Session.objects.create(activity=locked, place=place, **data)
    session.instructors.set(people)
    audit.record(
        SESSION_ADDED,
        actor=by,
        target=session,
        details={
            "activity": locked.pk,
            "kind": session.kind,
            "starts_at": session.starts_at.isoformat(),
            "place": place.pk,
            "instructors": sorted(p.pk for p in people),
        },
        request=request,
    )
    return session


def _live(session) -> Session:
    locked = Session.objects.select_for_update().get(pk=session.pk)
    _editable(locked.activity)
    if locked.cancelled:
        raise ValidationError(_("Aquesta sessió està cancel·lada."))
    return locked


@transaction.atomic
def update_session(session, *, by, request=None, **fields) -> list[str]:
    """Canvia la classe, l'horari, el lloc o si és una pràctica. Torna els camps canviats."""
    permissions.require(by, permissions.MANAGE)
    unknown = set(fields) - set(SESSION_FIELDS)
    if unknown:
        raise ValidationError(
            _("Aquests camps no es canvien aquí: %(fields)s.")
            % {"fields": ", ".join(sorted(unknown))}
        )
    locked = _live(session)
    fields = _clean_session(fields)
    if "place" in fields:
        _place(fields["place"], current=locked.place)
    starts = fields.get("starts_at", locked.starts_at)
    ends = fields.get("ends_at", locked.ends_at)
    if ends <= starts:
        raise ValidationError(_("La sessió ha d'acabar després de començar."))
    changed = [name for name, value in fields.items() if getattr(locked, name) != value]
    if not changed:
        return []
    # El lloc va al registre pel seu identificador (com totes les claus foranes).
    changes = {
        name: tuple(getattr(v, "pk", v) for v in (getattr(locked, name), fields[name]))
        for name in changed
    }
    for name in changed:
        setattr(locked, name, fields[name])
        setattr(session, name, fields[name])
    locked.save(update_fields=changed)
    audit.record_changes(SESSION_UPDATED, actor=by, target=locked, changes=changes, request=request)
    return sorted(changes)


@transaction.atomic
def set_instructors(session, people, *, by, request=None) -> bool:
    """Deixa `people` com els instructors de la sessió. Torna si ha canviat."""
    permissions.require(by, permissions.MANAGE)
    locked = _live(session)
    people = _instructors(people)
    _check_requirements(people, locked.starts_at)
    before = set(locked.instructors.values_list("pk", flat=True))
    after = {person.pk for person in people}
    if before == after:
        return False
    locked.instructors.set(people)
    audit.record(
        INSTRUCTORS_CHANGED,
        actor=by,
        target=locked,
        field="instructors",
        old=sorted(before),
        new=sorted(after),
        request=request,
    )
    return True


@transaction.atomic
def cancel_session(session, *, by, reason, request=None) -> Session:
    """Cancel·la una sessió amb motiu. No s'esborra: deixa de comptar per a l'inici del curs i
    per al dia a partir del qual es pot marcar com a fet (RN-M02-20)."""
    permissions.require(by, permissions.MANAGE)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal escriure el motiu de la cancel·lació."))
    locked = _live(session)
    locked.cancelled = True
    locked.cancellation_reason = reason
    locked.save(update_fields=["cancelled", "cancellation_reason"])
    session.cancelled, session.cancellation_reason = True, reason
    audit.record(SESSION_CANCELLED, actor=by, target=locked, reason=reason, request=request)
    return session


# --- Programa del dia -----------------------------------------------------------------------------


def _clean_block(raw: dict, kept_places) -> dict:
    unknown = set(raw) - set(BLOCK_FIELDS)
    if unknown:
        raise ValidationError(
            _("Un bloc del programa no té aquests camps: %(fields)s.")
            % {"fields": ", ".join(sorted(unknown))}
        )
    label = (raw.get("label") or "").strip()
    if not label:
        raise ValidationError(_("Cada bloc del programa ha de dir què s'hi fa."))
    starts, ends = raw.get("starts_at"), raw.get("ends_at")
    if not isinstance(starts, datetime.time) or not isinstance(ends, datetime.time | None):
        raise ValidationError(_("Escriu l'hora de cada bloc del programa."))
    if ends is not None and ends <= starts:
        raise ValidationError(_("Un bloc del programa ha d'acabar després de començar."))
    responsible = (raw.get("responsible_label") or "").strip()
    if _CONTACT.search(responsible):
        raise ValidationError(
            _("A «qui se n'encarrega» escriu-hi una funció, sense correu ni telèfon.")
        )
    place = raw.get("place")
    if place is not None:
        _place(place, current=place if place in kept_places else None)
    if len(label) > 80 or len(responsible) > 80:
        raise ValidationError(_("Un dels textos del programa és massa llarg."))
    return {
        "starts_at": starts,
        "ends_at": ends,
        "label": label,
        "place": place,
        "responsible_label": responsible,
    }


@transaction.atomic
def set_programme(activity, blocks, *, by, request=None) -> list[ProgrammeBlock]:
    """Desa el programa del dia sencer, en l'ordre de la llista (pot ser buida)."""
    permissions.require(by, permissions.MANAGE)
    locked = _editable(activity)
    current = locked.programme_blocks.order_by("order")
    kept = {block.place for block in current if block.place is not None}
    cleaned = [_clean_block(dict(raw), kept) for raw in blocks]
    before = [{name: getattr(block, name) for name in BLOCK_FIELDS} for block in current]
    if before == cleaned:
        return list(current)
    locked.programme_blocks.all().delete()
    created = ProgrammeBlock.objects.bulk_create(
        ProgrammeBlock(activity=locked, order=order, **data)
        for order, data in enumerate(cleaned, start=1)
    )
    audit.record(
        PROGRAMME_CHANGED,
        actor=by,
        target=locked,
        field="programme_blocks",
        old=len(before),
        new=len(cleaned),
        request=request,
    )
    return created


# --- Instructors que deixen de ser-ho (T-M02-04b; L-M02-05; decisió 101; RN-RP-12) ---------------

INSTRUCTOR_RELEASED = "activities.session.instructor_released"
RELEASE_ORIGIN = "activities.former_instructors"


def _future_sessions(now):
    """Sessions que encara s'han de fer: futures, no cancel·lades i d'una activitat viva."""
    return Session.objects.filter(
        starts_at__gt=now, cancelled=False, activity__status__in=states.EDITABLE_STATUSES
    )


@transaction.atomic
def release_former_instructors(*, now=None, actor=None) -> list[int]:
    """Treu de les sessions futures les persones que ja no poden fer classe (rol retirat, compte
    desactivat o persona anonimitzada), amb una entrada al registre per sessió. Les passades
    conserven qui hi va fer classe. Ningú no s'hi torna a posar sol. Idempotent. Torna les
    sessions canviades."""
    now = now or timezone.now()
    actor = actor or audit.system(RELEASE_ORIGIN)
    gone = (
        Session.instructors.through.objects.filter(session__in=_future_sessions(now))
        .exclude(person_id__in=instructor_people().values("pk"))
        .values_list("session_id", "person_id")
    )
    by_session: dict[int, set[int]] = {}
    for session_id, person_id in gone:
        by_session.setdefault(session_id, set()).add(person_id)
    for session_id in sorted(by_session):
        session = Session.objects.select_for_update().get(pk=session_id)
        before = set(session.instructors.values_list("pk", flat=True))
        leaving = by_session[session_id] & before
        session.instructors.remove(*leaving)
        audit.record(
            INSTRUCTOR_RELEASED,
            actor=actor,
            target=session,
            field="instructors",
            old=sorted(before),
            new=sorted(before - leaving),
            reason=_("Ha deixat de tenir el rol d'instructor."),
        )
    return sorted(by_session)


def sessions_without_instructor(now=None):
    """Sessions futures sense cap instructor, perquè el responsable n'hi posi un (T-M02-06)."""
    return _future_sessions(now or timezone.now()).filter(instructors__isnull=True)
