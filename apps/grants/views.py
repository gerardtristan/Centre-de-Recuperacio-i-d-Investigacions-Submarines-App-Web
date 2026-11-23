"""Pantalles dels ajuts a l'administració. Calendari (T-M09A-05; HU-M09A-03; AJ3): el mes que es
tria (amb el mes anterior i el següent) i, a sota, totes les dates a partir d'avui. Sense AJ3,
«no trobat»."""

import datetime

from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.core.permissions import require_perm

from .calendar import calendar

VIEW = "grants.view"  # AJ3


def _month(value: str, today: datetime.date) -> datetime.date:
    """`AAAA-MM` → el primer dia del mes; qualsevol altra cosa, el mes d'avui."""
    try:
        return datetime.datetime.strptime(value or "", "%Y-%m").date()
    except ValueError:
        return today.replace(day=1)


def _shift(first: datetime.date, months: int) -> datetime.date:
    month = first.month - 1 + months
    return first.replace(year=first.year + month // 12, month=month % 12 + 1)


@never_cache
@require_GET
def calendar_view(request):
    require_perm(request, VIEW)
    today = timezone.localdate()
    first = _month(request.GET.get("mes"), today)
    last = _shift(first, 1) - datetime.timedelta(days=1)
    context = {
        "month": first,
        "previous": _shift(first, -1),
        "next": _shift(first, 1),
        "events": calendar(first, last),
        "upcoming": calendar(today, datetime.date.max),  # totes les dates a partir d'avui
    }
    return render(request, "grants/calendar.html", context)
