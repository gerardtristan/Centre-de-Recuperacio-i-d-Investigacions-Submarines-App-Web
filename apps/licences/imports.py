"""Pas únic dels registres mínims del 01 al 06 (T-M06-14; P-M06-H; CA-M06-14; LC11).

- `preview(actor)`: llegeix `members.licence_records()` i diu què passaria, sense escriure res:
  nova, ja passada, sense caducitat («pendent de confirmar», T-M06-23) o tipus que el 06 no
  coneix (el nom del 01 ha de coincidir amb un tipus del 06, sense distingir majúscules).
- `confirm(actor)`: crea el lot «licences» i una llicència vigent `imported_m01` per registre nou
  o sense caducitat, sense càrrec, amb `m01_record_ref` (052, punt 8), i emet `licence.issued`
  (la còpia del 01 actualitza la fila d'origen, RN-M01-35). Les sense caducitat queden
  `expiry_confirmed = false` (RN-M06-24): cap avís ni `licence.expired`.
- `confirm_expiry(licence, expires_on, actor)`: la secretaria hi posa la data (CA-M06-29); puja
  la `version` i la comprovació diària (054) la porta al 01.
- `unconfirmed(actor)` i `confirm_in_bulk(ids, year, actor)`: la llista de pendents i la
  confirmació en bloc de les d'any natural (RN-M06-26, CA-M06-32).
- `undo(batch, actor)`: desfà el lot si cap llicència no ha canviat des de llavors: les esborra
  (no tenen cap càrrec ni moviment) i el 01 en deslliga les files. Res del 01 s'esborra.
Només l'administrador (LC11). Mai amb dades reals fora de producció.
"""

import datetime
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass

from django.db import transaction
from django.db.models import ProtectedError
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import audit
from apps.core import imports as core_imports
from apps.core.models import ImportBatch
from apps.core.permissions import has_perm
from apps.members.licence_copy import detach_licence_copies
from apps.members.services import licence_records

from . import events as licence_events
from .models import Licence, LicenceType, ValidityRule
from .services import ExpiryBeforeStart, LicenceRequestError

PERMISSION = "licences.import_m01"  # LC11
CONFIRM_EXPIRY_PERMISSION = "licences.file"  # LC5 (P-447)
ACTION_EXPIRY_CONFIRMED = "licences.expiry_confirmed"
ACTION_CONFIRMED = "licences.import_m01_confirmed"
ACTION_UNDONE = "licences.import_m01_undone"
NEW, EXISTING, NO_EXPIRY, UNKNOWN_TYPE = "new", "existing", "no_expiry", "unknown_type"


class NothingToImport(LicenceRequestError):
    message = _("No hi ha cap registre nou per passar al 06.")


class CannotUndo(LicenceRequestError):
    message = _(
        "Aquest lot ja no es pot desfer: alguna llicència ha canviat o no és un lot del 06."
    )


class AlreadyConfirmed(LicenceRequestError):
    message = _("Aquesta llicència ja té la caducitat confirmada.")


@dataclass(frozen=True)
class Row:
    record_id: int
    person_id: int
    licence_type: str
    issued_on: str
    expires_on: str | None
    result: str
    type_id: int | None = None


def _require(actor):
    if not has_perm(actor, PERMISSION, write=True):
        raise Http404


def preview(actor) -> list[Row]:
    _require(actor)
    types = {t.name.strip().lower(): t for t in LicenceType.objects.all()}
    done = set(
        Licence.objects.filter(m01_record_ref__isnull=False).values_list(
            "m01_record_ref", flat=True
        )
    )
    rows = []
    for info in licence_records():
        licence_type = types.get(info.licence_type.strip().lower())
        if info.record_id in done:
            result = EXISTING
        elif licence_type is None:
            result = UNKNOWN_TYPE
        elif info.expires_on is None:
            result = NO_EXPIRY
        else:
            result = NEW
        rows.append(Row(
            info.record_id, info.person_id, info.licence_type, info.issued_on.isoformat(),
            info.expires_on.isoformat() if info.expires_on else None, result,
            licence_type.pk if licence_type else None,
        ))  # fmt: skip
    return rows


def summary(rows) -> Counter:
    return Counter(row.result for row in rows)


@transaction.atomic
def confirm(actor) -> ImportBatch:
    rows = preview(actor)
    new = [row for row in rows if row.result in (NEW, NO_EXPIRY)]
    if not new:
        raise NothingToImport
    counts = summary(rows)
    digest = hashlib.sha256(json.dumps([asdict(r) for r in rows]).encode()).hexdigest()
    batch = core_imports.open_confirmed(
        ImportBatch.Kind.LICENCES, file_sha256=digest, by=actor,
        counts={"new_count": len(new), "matching_count": counts[EXISTING],
                "error_count": counts[UNKNOWN_TYPE], "excluded_count": 0},
    )  # fmt: skip
    types = LicenceType.objects.in_bulk([row.type_id for row in new])
    for row in new:
        licence_type = types[row.type_id]
        licence = Licence.objects.create(
            person_id=row.person_id, licence_type=licence_type,
            validity_rule=licence_type.validity_rule, status=Licence.Status.ACTIVE,
            origin=Licence.Origin.IMPORTED_M01, starts_on=row.issued_on, expires_on=row.expires_on,
            expiry_confirmed=row.expires_on is not None, m01_record_ref=row.record_id,
            import_batch=batch,
        )  # fmt: skip
        licence.refresh_from_db()  # dates com a `date` per a l'esdeveniment
        licence_events.activated(licence)
    audit.record(ACTION_CONFIRMED, actor=actor, target=batch, details=dict(counts))
    return batch


@transaction.atomic
def undo(batch: ImportBatch, actor) -> ImportBatch:
    _require(actor)
    batch = ImportBatch.objects.select_for_update().get(pk=batch.pk)
    if batch.kind != ImportBatch.Kind.LICENCES or batch.status != ImportBatch.Status.CONFIRMED:
        raise CannotUndo
    licences = list(Licence.objects.select_for_update().filter(import_batch=batch))
    if any(lic.version != 1 or lic.status != Licence.Status.ACTIVE for lic in licences):
        raise CannotUndo
    ids = [lic.pk for lic in licences]
    detach_licence_copies(ids)
    try:
        # Sense càrrec ni moviment: esborrar-les desfà el pas (el model ho impedeix a `objects`).
        Licence._base_manager.filter(pk__in=ids).delete()
    except ProtectedError as error:  # una renovació o un avís hi apunten
        raise CannotUndo from error
    # shortcut: escriu el lot del nucli directament, com el desfer de Cluber
    # (apps/members/imports/final.py), perquè `apps.core.imports` no té cap servei per desfer un
    # lot; quan el nucli el tingui, fer-lo servir aquí (P-445).
    batch.status, batch.undone_by, batch.undone_at = (
        ImportBatch.Status.UNDONE,
        actor,
        timezone.now(),
    )
    batch.save(update_fields=["status", "undone_by", "undone_at"])
    audit.record(ACTION_UNDONE, actor=actor, target=batch, details={"licences": len(ids)})
    return batch


@transaction.atomic
def confirm_expiry(licence: Licence, expires_on, *, actor) -> Licence:
    """CA-M06-29 (RN-M06-24): la secretaria posa la data a una llicència «pendent de confirmar»,
    que passa a ser normal (rep avisos i, si caduca, `licence.expired`). Puja la `version`
    (`save`) i la comprovació diària del 01 en copia la data. Sense LC5, «no trobat»."""
    if not has_perm(actor, CONFIRM_EXPIRY_PERMISSION, write=True):
        raise Http404
    licence = Licence.objects.select_for_update().get(pk=licence.pk)
    if licence.expiry_confirmed:
        raise AlreadyConfirmed
    if expires_on < licence.starts_on:
        raise ExpiryBeforeStart
    previous = licence.expires_on
    licence.expires_on, licence.expiry_confirmed = expires_on, True
    licence.save(update_fields=["expires_on", "expiry_confirmed", "updated_at"])
    audit.record(
        ACTION_EXPIRY_CONFIRMED, actor=actor, target=licence, field="expires_on",
        old=previous.isoformat() if previous else None, new=expires_on.isoformat(),
    )  # fmt: skip
    return licence


class NothingSelected(LicenceRequestError):
    message = _("Tria almenys una llicència.")


class YearNotAllowed(LicenceRequestError):
    message = _("L'any de caducitat ha de ser l'actual o el següent.")


class NotPending(LicenceRequestError):
    message = _("Alguna llicència ja no està pendent de confirmar. Torna a carregar la llista.")


class StartsAfterYear(LicenceRequestError):
    message = _(
        "Alguna llicència comença després del 31/12 de l'any triat: treu-la o tria un altre any."
    )


def unconfirmed(actor):
    """RN-M06-26: les pendents de confirmar, amb la data declarada si n'hi ha. LC5."""
    if not has_perm(actor, CONFIRM_EXPIRY_PERMISSION, write=True):
        raise Http404
    return (
        Licence.objects.filter(status=Licence.Status.ACTIVE, expiry_confirmed=False)
        .select_related("person", "licence_type")
        .order_by("person__last_name", "person__first_name", "pk")
    )


def allowed_years(today=None) -> tuple[int, int]:
    """Com al 01 (085, S-4): l'any actual o el següent."""
    year = (today or timezone.localdate()).year
    return year, year + 1


@transaction.atomic
def confirm_in_bulk(licence_ids, year: int, *, actor, today=None) -> int:
    """RN-M06-26 (CA-M06-32): les d'any natural triades caduquen el 31/12 de `year`, tot o res.
    Només les pendents sense data declarada (una de declarada es confirma una a una). Cada una
    puja la `version` i queda al registre amb el valor anterior. Sense LC5, «no trobat»."""
    if not has_perm(actor, CONFIRM_EXPIRY_PERMISSION, write=True):
        raise Http404
    ids = {int(pk) for pk in licence_ids}
    if not ids:
        raise NothingSelected
    if isinstance(year, bool) or year not in allowed_years(today):
        raise YearNotAllowed
    end = datetime.date(year, 12, 31)
    licences = list(
        Licence.objects.select_for_update()
        .filter(pk__in=ids, status=Licence.Status.ACTIVE, expiry_confirmed=False,
                expires_on__isnull=True, validity_rule=ValidityRule.CALENDAR_YEAR)
        .order_by("pk")
    )  # fmt: skip
    if len(licences) != len(ids):
        raise NotPending
    if any(licence.starts_on > end for licence in licences):
        raise StartsAfterYear
    for licence in licences:
        licence.expires_on, licence.expiry_confirmed = end, True
        licence.save(update_fields=["expires_on", "expiry_confirmed", "updated_at"])
        audit.record(
            ACTION_EXPIRY_CONFIRMED, actor=actor, target=licence, field="expires_on",
            old=None, new=end.isoformat(), details={"bulk": True},
        )  # fmt: skip
    return len(licences)
