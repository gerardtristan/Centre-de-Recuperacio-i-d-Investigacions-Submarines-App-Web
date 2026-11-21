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
