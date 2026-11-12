"""Sessions d'un curs i programa del dia d'una sortida (T-M02-03; P-M02-B, pas 2; M02-6).

- **Sessions** (`add_session`, `update_session`, `cancel_session`, `set_instructors`): teoria,
  piscina o mar, amb data, hora, lloc i instructors. Una sessió no s'esborra: es cancel·la amb
  motiu. Se'n poden afegir mentre l'activitat no s'hagi fet ni cancel·lat.
- **Instructors:** persones amb el rol d'instructor actiu en un compte d'administrador actiu
  (M02-6). Les condicions de RN-M02-26 (soci actiu i llicència tècnica vigent) són de la T-M02-30,
  que depèn del 06.
- **Programa del dia** (`set_programme`): la llista de blocs sencera, en ordre. Qui se n'encarrega
  és una funció («cap d'immersió»), mai un nom ni dades de contacte.
- **Permís:** AC7 amb edició; sense, «no trobat».

El pla no limita les sessions als cursos ni el programa a les sortides (CA-M02-04 parla d'una
activitat amb sessions i blocs), i aquí tampoc es limita.

**Fora d'aquesta peça:** les sessions de reforç (`reinforcement_for`, T-M02-18), l'avís als inscrits
quan canvia una sessió o el programa (RN-M02-18, T-M02-21) i les pantalles (T-M02-06).
"""

import datetime
import re

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.models import AccountRole, Person, Role

from . import permissions, states
from .models import Activity, ProgrammeBlock, Session

SESSION_ADDED = "activities.session.added"
SESSION_UPDATED = "activities.session.updated"
SESSION_CANCELLED = "activities.session.cancelled"
INSTRUCTORS_CHANGED = "activities.session.instructors_changed"
PROGRAMME_CHANGED = "activities.programme.changed"

SESSION_FIELDS = ("kind", "starts_at", "ends_at", "location", "is_practice")
BLOCK_FIELDS = ("starts_at", "ends_at", "label", "location", "responsible_label")
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


def _clean_session(data: dict) -> dict:
    out = dict(data)
    if "kind" in out and out["kind"] not in Session.Kind.values:
        raise ValidationError(_("La sessió ha de ser de teoria, de piscina o de mar."))
    for name in ("starts_at", "ends_at"):
        if name in out:
            _moment(out[name])
    if "location" in out:
        out["location"] = (out["location"] or "").strip()
        if len(out["location"]) > 140:
            raise ValidationError(_("El lloc és massa llarg (màxim, 140 caràcters)."))
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
    location="",
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
            "location": location,
            "is_practice": is_practice,
        }
    )
    if data["ends_at"] <= data["starts_at"]:
        raise ValidationError(_("La sessió ha d'acabar després de començar."))
    people = _instructors(instructors)
    session = Session.objects.create(activity=locked, **data)
    session.instructors.set(people)
    audit.record(
        SESSION_ADDED,
        actor=by,
        target=session,
        details={
            "activity": locked.pk,
            "kind": session.kind,
            "starts_at": session.starts_at.isoformat(),
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
    starts = fields.get("starts_at", locked.starts_at)
    ends = fields.get("ends_at", locked.ends_at)
    if ends <= starts:
        raise ValidationError(_("La sessió ha d'acabar després de començar."))
    changes = {
        name: (getattr(locked, name), value)
        for name, value in fields.items()
        if getattr(locked, name) != value
    }
    if not changes:
        return []
    for name in changes:
        setattr(locked, name, fields[name])
        setattr(session, name, fields[name])
    locked.save(update_fields=list(changes))
    audit.record_changes(SESSION_UPDATED, actor=by, target=locked, changes=changes, request=request)
    return sorted(changes)


@transaction.atomic
def set_instructors(session, people, *, by, request=None) -> bool:
    """Deixa `people` com els instructors de la sessió. Torna si ha canviat."""
    permissions.require(by, permissions.MANAGE)
    locked = _live(session)
    people = _instructors(people)
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


def _clean_block(raw: dict) -> dict:
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
    location = (raw.get("location") or "").strip()
    if len(label) > 80 or len(responsible) > 80 or len(location) > 140:
        raise ValidationError(_("Un dels textos del programa és massa llarg."))
    return {
        "starts_at": starts,
        "ends_at": ends,
        "label": label,
        "location": location,
        "responsible_label": responsible,
    }


@transaction.atomic
def set_programme(activity, blocks, *, by, request=None) -> list[ProgrammeBlock]:
    """Desa el programa del dia sencer, en l'ordre de la llista (pot ser buida)."""
    permissions.require(by, permissions.MANAGE)
    locked = _editable(activity)
    cleaned = [_clean_block(dict(raw)) for raw in blocks]
    current = locked.programme_blocks.order_by("order")
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
