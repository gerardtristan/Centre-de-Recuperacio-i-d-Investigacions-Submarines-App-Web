"""Recomptes d'activitat per al dashboard (T-M08-04; RP-M08-01; M02-2 el promet al 08).

`activities.stats(starts_on, ends_on)` torna només recomptes: cap persona, cap nom, cap
identificador. Definicions de RN-M08-10 (ocupació i assistència) i RN-M02-07 (places ocupades):
- **Activitats del període:** les que comencen dins del període (dates incloses), sense
  esborranys ni cancel·lades.
- **Ocupació:** inscripcions confirmades / places totals d'aquestes activitats.
- **Assistència:** assistències registrades («hi és») / inscrits confirmats de les sessions fetes
  dins del període: les sessions no cancel·lades d'un curs que ja han acabat (sense les de reforç,
  que només són d'alguns inscrits) i el dia de cada sortida acabada.
- **Inscripcions per setmana:** inscripcions confirmades, pel dia que es van fer, agrupades pel
  dilluns de la setmana; totes les setmanes del període hi surten, també amb 0.
- **Places lliures:** places menys places ocupades (pendents de pagament, confirmades i ofertes,
  RN-M02-07) de les activitats obertes que comencen després d'avui.
"""

import datetime
from dataclasses import dataclass

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import Activity, Attendance, Enrolment, Session

A = Activity.Status
E = Enrolment.Status


@dataclass(frozen=True)
class ActivityStats:
    places: int  # places totals de les activitats del període
    confirmed: int  # inscripcions confirmades d'aquestes activitats
    attended: int  # assistències registrades de les sessions fetes
    expected: int  # inscrits confirmats de les sessions fetes
    weekly: dict  # {dilluns de la setmana: inscripcions confirmades}
    free_places: int  # places lliures de les activitats obertes que comencen després d'avui

    @staticmethod
    def _percent(part, whole):
        return round(100 * part / whole) if whole else None

    @property
    def occupancy_percent(self) -> int | None:
        return self._percent(self.confirmed, self.places)

    @property
    def attendance_percent(self) -> int | None:
        return self._percent(self.attended, self.expected)


def _monday(day):
    return day - datetime.timedelta(days=day.weekday())


def _weekly(starts_on, ends_on) -> dict:
    weeks = {}
    week = _monday(starts_on)
    while week <= ends_on:
        weeks[week] = 0
        week += datetime.timedelta(days=7)
    days = (
        Enrolment.objects.filter(status=E.CONFIRMED)
        .annotate(day=TruncDate("created_at"))
        .filter(day__range=(starts_on, ends_on))
        .values("day")
        .annotate(n=Count("id"))
    )
    for row in days:
        weeks[_monday(row["day"])] += row["n"]
    return weeks


def _attendance(starts_on, ends_on, now) -> tuple[int, int]:
    confirmed = Count("activity__enrolments", filter=Q(activity__enrolments__status=E.CONFIRMED))
    sessions = (
        Session.objects.filter(
            cancelled=False, reinforcement_for__isnull=True, ends_at__lt=now,
            activity__kind=Activity.Kind.COURSE,
        )
        .exclude(activity__status__in=(A.DRAFT, A.CANCELLED))
        .annotate(day=TruncDate("starts_at"))
        .filter(day__range=(starts_on, ends_on))
    )  # fmt: skip
    expected = sum(sessions.annotate(n=confirmed).values_list("n", flat=True))
    attended = Attendance.objects.filter(
        present=True, session__in=sessions, enrolment__status=E.CONFIRMED
    ).count()
    outings = Activity.objects.filter(
        kind=Activity.Kind.OUTING, ends_on__range=(starts_on, ends_on),
        ends_on__lt=timezone.localdate(now),
    ).exclude(status__in=(A.DRAFT, A.CANCELLED))  # fmt: skip
    expected += Enrolment.objects.filter(activity__in=outings, status=E.CONFIRMED).count()
    attended += Attendance.objects.filter(
        present=True, session__isnull=True, enrolment__activity__in=outings,
        enrolment__status=E.CONFIRMED,
    ).count()  # fmt: skip
    return attended, expected


def stats(starts_on: datetime.date, ends_on: datetime.date, now=None) -> ActivityStats:
    """`activities.stats` (RP-M08-01): recomptes del període, dates incloses. Cap persona."""
    now = now or timezone.now()
    today = timezone.localdate(now)
    period = Activity.objects.filter(starts_on__range=(starts_on, ends_on)).exclude(
        status__in=(A.DRAFT, A.CANCELLED)
    )
    places = sum(period.values_list("max_places", flat=True))
    confirmed = Enrolment.objects.filter(activity__in=period, status=E.CONFIRMED).count()
    upcoming = Activity.objects.filter(status=A.OPEN, starts_on__gt=today).annotate(
        taken=Count("enrolments", filter=Q(enrolments__status__in=Enrolment.OCCUPYING))
    )
    free = sum(max(0, row.max_places - row.taken) for row in upcoming)
    attended, expected = _attendance(starts_on, ends_on, now)
    return ActivityStats(
        places=places, confirmed=confirmed, attended=attended, expected=expected,
        weekly=_weekly(starts_on, ends_on), free_places=free,
    )  # fmt: skip


def low_occupancy_count(percent: int, today=None) -> int:
    """Per al dashboard (08; RN-M08-07): activitats obertes que comencen després d'avui (com les
    places lliures) amb l'ocupació (confirmades / places, RN-M08-10) per sota de `percent`.
    Només el recompte, sense permís: el permís DB1 el comprova la vista del dashboard
    (T-M08-09)."""
    today = today or timezone.localdate()
    rows = Activity.objects.filter(status=A.OPEN, starts_on__gt=today, max_places__gt=0).annotate(
        confirmed=Count("enrolments", filter=Q(enrolments__status=E.CONFIRMED))
    )
    return sum(1 for row in rows if 100 * row.confirmed < percent * row.max_places)
