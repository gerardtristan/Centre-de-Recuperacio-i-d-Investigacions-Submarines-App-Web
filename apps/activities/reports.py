"""Informes operatius (T-M02-24; AC20): participants d'una activitat, horari per imprimir i
ocupació de les activitats. Portat de la branca aparcada; el CSV és el de la resta de la
plataforma (`members.roster.to_csv`: UTF-8 amb BOM, «;» i cap cel·la que sembli una fórmula).

- **Permís i abast.** AC20. Amb l'abast «les seves sessions» (l'instructor), només les activitats
  on fa classe; fora, «no trobat» i registre (`permissions.require` amb l'objecte).
- **Minimització (C3).** L'instructor només hi veu els confirmats, amb nom, titulacions i
  llicència vigent sí o no. La resta de rols amb AC20 hi veuen també l'estat, la posició a la
  llista d'espera, el canal i els requisits per revisar; el preu, només amb AC19. Cap correu,
  telèfon, document ni adreça en cap informe.
- **L'horari** no porta cap nom de persona: les sessions (curs) o els blocs del programa
  (sortida), amb l'hora i el lloc.
- **Ocupació:** només recomptes.

- **El CSV dels participants** porta noms: cada descàrrega queda al registre (qui, quina
  activitat, quantes files i l'empremta del fitxer; cap nom).

Les pàgines d'impressió i les descàrregues són a `views/reports.py` (T-M02-24b).
"""

import hashlib
from dataclasses import dataclass

from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.permission_catalog import SCOPE_OWN_SESSIONS
from apps.core.permissions import scope_for
from apps.licences import services as licences
from apps.members.roster import to_csv

from . import certifications, permissions
from . import enrolment as enrolments
from .models import Activity, Enrolment

A = Activity.Status
S = Enrolment.Status
PARTICIPANTS_EXPORTED = "activities.participants.exported"


def _yes_no(value) -> str:
    return str(_("Sí") if value else _("No"))


def _licence_valid(person, day) -> bool:
    info = licences.current(person, day)
    return info is not None and info.status == licences.CurrentStatus.ACTIVE


def _name(person) -> str:
    return f"{person.first_name} {person.last_name}".strip()


def participants_report(activity, *, viewer, request=None) -> tuple[list[str], list[list]]:
    """Capçaleres i files de l'informe de participants que `viewer` pot veure."""
    permissions.require(viewer, permissions.REPORTS, activity, write=False, request=request)
    rows = Enrolment.objects.filter(activity=activity).select_related("person")
    rows = rows.order_by("person__last_name", "person__first_name", "id")
    if scope_for(viewer, permissions.REPORTS) == SCOPE_OWN_SESSIONS:
        headers = [_("Nom"), _("Titulacions"), _("Llicència vigent")]
        body = [
            [
                _name(row.person),
                ", ".join(str(c) for c in certifications.of(row.person)),
                _yes_no(_licence_valid(row.person, activity.starts_on)),
            ]
            for row in rows.filter(status=S.CONFIRMED)
        ]
        return [str(h) for h in headers], body
    show_price = permissions.can(viewer, permissions.INCOME, write=False)
    headers = [_("Nom"), _("Inscripció"), _("Posició a la llista d'espera"), _("Canal"),
               _("Requisits per revisar")]  # fmt: skip
    if show_price:
        headers += [_("Preu (cèntims)"), _("Tipus de preu")]
    body = []
    for row in rows.exclude(status__in=Enrolment.ENDED):
        cells = [
            _name(row.person), row.get_status_display(), row.waitlist_position or "",
            row.get_channel_display(), row.requirements_warning.replace("\n", "; "),
        ]  # fmt: skip
        if show_price:
            cells += [row.price_cents, row.get_price_kind_display()]
        body.append(cells)
    return [str(h) for h in headers], body


def participants_csv(activity, *, viewer, request=None) -> bytes:
    headers, rows = participants_report(activity, viewer=viewer, request=request)
    content = to_csv(headers, rows)
    audit.record(
        PARTICIPANTS_EXPORTED, actor=viewer, target=activity,
        details={"rows": len(rows), "sha256": hashlib.sha256(content).hexdigest()},
        request=request,
    )  # fmt: skip
    return content


@dataclass(frozen=True)
class Occupancy:
    activity: Activity
    occupied: int
    free: int
    waiting: int
    percent: int


def _visible_activities(viewer):
    rows = Activity.objects.exclude(status=A.DRAFT).order_by("-starts_on", "-id")
    if scope_for(viewer, permissions.REPORTS) == SCOPE_OWN_SESSIONS:
        rows = rows.filter(
            sessions__instructors=viewer.person_id, sessions__cancelled=False
        ).distinct()
    return rows


def occupancy(*, viewer) -> list[Occupancy]:
    """Places ocupades, lliures i en llista d'espera de cada activitat publicada que `viewer`
    pot veure. Només recomptes: cap dada de cap persona."""
    permissions.require(viewer, permissions.REPORTS, write=False)
    out = []
    for activity in _visible_activities(viewer):
        taken = enrolments.occupied(activity)
        out.append(
            Occupancy(
                activity=activity,
                occupied=taken,
                free=max(0, activity.max_places - taken),
                waiting=enrolments.waitlist(activity).count(),
                percent=round(100 * taken / activity.max_places) if activity.max_places else 0,
            )
        )
    return out


def occupancy_csv(*, viewer) -> bytes:
    headers = [_("Activitat"), _("Data d'inici"), _("Estat"), _("Places"), _("Ocupades"),
               _("Lliures"), _("En llista d'espera"), _("Ocupació (%)")]  # fmt: skip
    rows = [
        [row.activity.title, row.activity.starts_on.strftime("%d/%m/%Y"),
         row.activity.get_status_display(), row.activity.max_places, row.occupied, row.free,
         row.waiting, row.percent]
        for row in occupancy(viewer=viewer)
    ]  # fmt: skip
    return to_csv([str(h) for h in headers], rows)


def schedule(activity, *, viewer, request=None) -> dict:
    """L'horari per imprimir: les sessions (curs) o el programa del dia (sortida), amb l'hora i
    el lloc. Cap nom de persona."""
    permissions.require(viewer, permissions.REPORTS, activity, write=False, request=request)
    course = activity.kind == Activity.Kind.COURSE
    return {
        "activity": activity.title,
        "generated_on": timezone.localdate(),
        "sessions": [
            {"kind": s.get_kind_display(), "starts_at": s.starts_at, "ends_at": s.ends_at,
             "place": s.place.name if s.place_id else ""}
            for s in activity.sessions.filter(cancelled=False).select_related("place")
            .order_by("starts_at", "id")
        ] if course else [],
        "blocks": [
            {"label": b.label, "starts_at": b.starts_at, "ends_at": b.ends_at,
             "place": b.place.name if b.place_id else "", "responsible": b.responsible_label}
            for b in activity.programme_blocks.select_related("place").order_by("starts_at", "id")
        ] if not course else [],
    }  # fmt: skip
