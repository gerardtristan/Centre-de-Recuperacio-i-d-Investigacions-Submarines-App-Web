"""Fitxer de calendari d'una activitat (T-M02-08; RN-M02-25 i RN-M02-45).

`build(...)` genera el text d'un fitxer `.ics` (RFC 5545) amb les sessions que se li donen o, si
no n'hi ha, amb els dies de l'activitat. **No hi posa mai cap persona:** ni organitzador, ni
assistents, ni instructors; només el títol, l'horari i el nom del lloc (mai les notes del lloc).

Qui el podrà descarregar és el participant, per a les seves sessions, des de «Les meves
activitats» (`/socis/activitats/{inscripció}/calendari.ics`): aquesta ruta és de la T-M02-22, quan
hi hagi inscripcions. Aquí només hi ha el generador.
"""

import datetime

from django.utils import timezone

PRODID = "-//C.R.I.S.//Plataforma//CA"
DOMAIN = "cris1954.cat"
_ESCAPES = (("\\", "\\\\"), (";", "\\;"), (",", "\\,"), ("\r\n", "\\n"), ("\n", "\\n"))


def escape(text: str) -> str:
    for old, new in _ESCAPES:
        text = text.replace(old, new)
    return text


def fold(line: str) -> str:
    """Les línies de més de 75 octets es parteixen i continuen amb un espai (RFC 5545, 3.1)."""
    data = line.encode("utf-8")
    if len(data) <= 75:
        return line
    parts, limit = [], 75
    while data:
        cut = min(limit, len(data))
        while cut < len(data) and (data[cut] & 0xC0) == 0x80:  # no partir un caràcter
            cut -= 1
        parts.append(data[:cut].decode("utf-8"))
        data, limit = data[cut:], 74
    return "\r\n ".join(parts)


def _place_name(*places) -> str:
    return next((place.name for place in places if place is not None), "")


def _utc(moment: datetime.datetime) -> str:
    return moment.astimezone(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")


def _event(uid, stamp, summary, location, start, end) -> list[str]:
    lines = ["BEGIN:VEVENT", f"UID:{uid}@{DOMAIN}", f"DTSTAMP:{stamp}", start, end]
    lines.append(f"SUMMARY:{escape(summary)}")
    if location:
        lines.append(f"LOCATION:{escape(location)}")
    lines.append("END:VEVENT")
    return lines


def build(activity, sessions=(), *, now=None) -> str:
    """El calendari de `activity` amb `sessions` (les del participant). Sense sessions, un
    esdeveniment de dia sencer del primer a l'últim dia de l'activitat."""
    stamp = _utc(now or timezone.now())
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:{PRODID}", "CALSCALE:GREGORIAN"]
    sessions = [s for s in sessions if not s.cancelled]
    for session in sessions:
        lines += _event(
            f"activitat-{activity.pk}-sessio-{session.pk}",
            stamp,
            f"{activity.title} ({session.get_kind_display()})",
            _place_name(session.place, activity.place),
            f"DTSTART:{_utc(session.starts_at)}",
            f"DTEND:{_utc(session.ends_at)}",
        )
    if not sessions:
        after = activity.ends_on + datetime.timedelta(days=1)  # DTEND és exclusiu
        lines += _event(
            f"activitat-{activity.pk}",
            stamp,
            activity.title,
            activity.meeting_point or _place_name(activity.place),
            f"DTSTART;VALUE=DATE:{activity.starts_on:%Y%m%d}",
            f"DTEND;VALUE=DATE:{after:%Y%m%d}",
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in lines) + "\r\n"
