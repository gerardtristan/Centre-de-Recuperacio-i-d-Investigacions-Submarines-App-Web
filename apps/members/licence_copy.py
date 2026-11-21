"""Còpia de lectura de la llicència del 06 (T-M01-31; 052 i 054; RN-M01-35 a 40).

El 06 és l'únic propietari de les llicències i emet `licence.issued`, `renewed` i `cancelled`
amb `version` i `occurred_at`. Aquí s'aplica cada esdeveniment a `LicenceRecord`:
- només per a socis (RN-M01-39); una persona que no ho és no té còpia;
- la fila amb el mateix `licence_ref` o, si la llicència ve del pas únic, la fila d'origen
  (`m01_record_ref`, RN-M01-35);
- només si la `version` és més gran que `source_version` (RN-M01-40): un esdeveniment repetit o
  més vell no fa res; es compara la versió, mai l'hora;
- `licence.cancelled` omple `cancelled_on`; res s'esborra (RN-M01-36). `licence.expired` no hi
  arriba: la caducitat ja surt de la data.
El 01 no importa cap model del 06: només llegeix el contingut de l'esdeveniment.
"""

import datetime

from django.db import transaction

from apps.core import audit, events

from .models import LicenceRecord, Member

SYSTEM = audit.system("members.licence_copy")
ACTION = "members.licence_copy_applied"
ACTION_DETACHED = "members.licence_copy_detached"
NAMES = (events.LICENCE_ISSUED, events.LICENCE_RENEWED, events.LICENCE_CANCELLED)


def on_licence_event(event) -> None:
    payload = event.payload
    member = Member.objects.filter(person_id=payload.get("person")).first()
    if member is None:
        return  # RN-M01-39
    rows = LicenceRecord.objects.select_for_update()
    record = rows.filter(licence_ref=payload["licence"]).first()
    if record is None and payload.get("m01_record_ref"):
        record = rows.filter(pk=payload["m01_record_ref"], member=member).first()
    version = payload["version"]
    if record is not None and record.source_version is not None:
        if version <= record.source_version:
            return  # RN-M01-37 i RN-M01-40
    if event.name == events.LICENCE_CANCELLED:
        if record is None:
            return  # no n'hi ha cap còpia: res a cancel·lar
        record.cancelled_on = datetime.datetime.fromisoformat(payload["occurred_at"]).date()
    else:
        record = record or LicenceRecord(member=member, source=LicenceRecord.Source.LICENCES)
        record.licence_type = payload["licence_type"][:100]
        record.issued_on = datetime.date.fromisoformat(payload["starts_on"])
        record.expires_on = datetime.date.fromisoformat(payload["expires_on"])
        record.expiry_declared = False
    created = record.pk is None
    record.licence_ref = payload["licence"]
    record.source_version = version
    record.save()
    audit.record(
        ACTION, actor=SYSTEM, target=record,
        details={"event": event.name, "licence": payload["licence"], "version": version,
                 "created": created},
    )  # fmt: skip


def detach_licence_copies(licence_refs) -> int:
    """El pas únic del 06 s'ha desfet (T-M06-14): les files del 01 deixen d'apuntar a aquelles
    llicències i tornen a ser registres propis del 01. No s'esborra res (RN-M01-36). Torna
    quantes files ha deslligat."""
    rows = LicenceRecord.objects.select_for_update().filter(licence_ref__in=list(licence_refs))
    done = 0
    for record in rows:
        record.licence_ref = record.source_version = record.cancelled_on = None
        record.save(update_fields=["licence_ref", "source_version", "cancelled_on"])
        audit.record(ACTION_DETACHED, actor=SYSTEM, target=record)
        done += 1
    return done


# --- Comprovació diària (T-M01-31b; RN-M01-41 a 44; 054) ------------------------------------

CHECK_ACTOR = audit.system("comprovació diària")
ACTION_CORRECTED = "members.licence_check_corrected"
ACTION_DONE = "members.licence_check_done"
ACTION_SKIPPED = "members.licence_check_skipped"
FIELDS = ("licence_type", "issued_on", "expires_on", "cancelled_on", "source_version")
_source = None


def register_licence_source(source) -> None:
    """El 06 hi registra, en arrencar, la funció que torna l'estat actual de les seves llicències
    (RN-M06-17): una llista de diccionaris amb `licence`, `person`, `licence_type`, `starts_on`,
    `expires_on`, `cancelled_on` i `version` (dates com a `date`)."""
    global _source
    _source = source


def _wanted(row) -> dict:
    return {"licence_type": row["licence_type"][:100], "issued_on": row["starts_on"],
            "expires_on": row["expires_on"], "cancelled_on": row["cancelled_on"],
            "source_version": row["version"]}  # fmt: skip


@transaction.atomic
def daily_check() -> dict:
    """RN-M01-41 a 44: compara la còpia amb el 06 i la corregeix (el 06 té raó). Sense font, no
    fa res. Si la font falla o torna buida mentre hi ha còpies, se salta sencera. Una fila que el
    06 no té no es toca: surt «per revisar». Res s'esborra."""
    if _source is None:
        return {"skipped": "no_source"}
    copies = LicenceRecord.objects.filter(licence_ref__isnull=False)
    try:
        rows = list(_source())
    except Exception as error:  # noqa: BLE001 (qualsevol error de la font salta la comprovació)
        return _skip(type(error).__name__)
    if not rows and copies.exists():
        return _skip("empty")
    by_ref = {row["licence"]: row for row in rows}
    counts = {"checked": 0, "corrected": 0, "created": 0, "to_review": []}
    for record in copies.select_for_update():
        counts["checked"] += 1
        row = by_ref.pop(record.licence_ref, None)
        if row is None:
            counts["to_review"].append(record.pk)  # RN-M01-42
            continue
        wanted = _wanted(row)
        changes = {f: (getattr(record, f), v) for f, v in wanted.items() if getattr(record, f) != v}
        if changes:
            for field, (_old, new) in changes.items():
                setattr(record, field, new)
            record.save(update_fields=list(changes))
            logged = {f: (str(old), str(new)) for f, (old, new) in changes.items()}
            audit.record_changes(ACTION_CORRECTED, actor=CHECK_ACTOR, target=record, changes=logged)
            counts["corrected"] += 1
    members = dict(
        Member.objects.filter(person_id__in={r["person"] for r in by_ref.values()}).values_list(
            "person_id", "pk"
        )
    )
    for row in by_ref.values():  # una còpia que no hi és (un esdeveniment perdut)
        if row["person"] in members and row["cancelled_on"] is None:
            record = LicenceRecord.objects.create(
                member_id=members[row["person"]], source=LicenceRecord.Source.LICENCES,
                licence_ref=row["licence"], **_wanted(row),
            )  # fmt: skip
            audit.record(ACTION_CORRECTED, actor=CHECK_ACTOR, target=record,
                         details={"created": True})  # fmt: skip
            counts["created"] += 1
    audit.record(ACTION_DONE, actor=CHECK_ACTOR, details={**counts,
                 "to_review": len(counts["to_review"])})  # fmt: skip
    return counts


def _skip(reason: str) -> dict:
    # RN-M01-44: cap canvi; queda al registre. L'avís (RN-M01-43, qui el rep) és una pregunta
    # oberta del pla [A validar: informàtica]: fins llavors, només el registre d'activitat.
    audit.record(ACTION_SKIPPED, actor=CHECK_ACTOR, details={"reason": reason})
    return {"skipped": reason}
