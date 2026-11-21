"""Pas únic dels registres mínims del 01 al 06 (T-M06-14; P-M06-H; CA-M06-14; LC11).

- `preview(actor)`: llegeix `members.licence_records()` i diu què passaria, sense escriure res:
  nova, ja passada, sense caducitat (va a la T-M06-23, «pendent de confirmar») o tipus que el 06
  no coneix (el nom del 01 ha de coincidir amb un tipus del 06, sense distingir majúscules).
- `confirm(actor)`: crea el lot «licences» i una llicència vigent `imported_m01` per registre nou,
  sense càrrec, amb `m01_record_ref` (052, punt 8), i emet `licence.issued` (la còpia del 01
  actualitza la fila d'origen, RN-M01-35).
- `undo(batch, actor)`: desfà el lot si cap llicència no ha canviat des de llavors: les esborra
  (no tenen cap càrrec ni moviment) i el 01 en deslliga les files. Res del 01 s'esborra.
Només l'administrador (LC11). Mai amb dades reals fora de producció.
"""

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
from .models import Licence, LicenceType
from .services import LicenceRequestError

PERMISSION = "licences.import_m01"  # LC11
ACTION_CONFIRMED = "licences.import_m01_confirmed"
ACTION_UNDONE = "licences.import_m01_undone"
NEW, EXISTING, NO_EXPIRY, UNKNOWN_TYPE = "new", "existing", "no_expiry", "unknown_type"


class NothingToImport(LicenceRequestError):
    message = _("No hi ha cap registre nou per passar al 06.")


class CannotUndo(LicenceRequestError):
    message = _(
        "Aquest lot ja no es pot desfer: alguna llicència ha canviat o no és un lot del 06."
    )


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
        elif info.expires_on is None:
            result = NO_EXPIRY
        elif licence_type is None:
            result = UNKNOWN_TYPE
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
    new = [row for row in rows if row.result == NEW]
    if not new:
        raise NothingToImport
    counts = summary(rows)
    digest = hashlib.sha256(json.dumps([asdict(r) for r in rows]).encode()).hexdigest()
    batch = core_imports.open_confirmed(
        ImportBatch.Kind.LICENCES, file_sha256=digest, by=actor,
        counts={"new_count": len(new), "matching_count": counts[EXISTING],
                "error_count": counts[UNKNOWN_TYPE], "excluded_count": counts[NO_EXPIRY]},
    )  # fmt: skip
    types = LicenceType.objects.in_bulk([row.type_id for row in new])
    for row in new:
        licence_type = types[row.type_id]
        licence = Licence.objects.create(
            person_id=row.person_id, licence_type=licence_type,
            validity_rule=licence_type.validity_rule, status=Licence.Status.ACTIVE,
            origin=Licence.Origin.IMPORTED_M01, starts_on=row.issued_on, expires_on=row.expires_on,
            m01_record_ref=row.record_id, import_batch=batch,
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
    # Mateix patró que el desfer de Cluber (apps/members/imports/final.py).
    batch.status, batch.undone_by, batch.undone_at = (
        ImportBatch.Status.UNDONE,
        actor,
        timezone.now(),
    )
    batch.save(update_fields=["status", "undone_by", "undone_at"])
    audit.record(ACTION_UNDONE, actor=actor, target=batch, details={"licences": len(ids)})
    return batch
