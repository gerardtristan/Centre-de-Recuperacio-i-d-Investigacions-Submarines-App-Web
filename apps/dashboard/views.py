"""Pantalla del dashboard (T-M08-09; P-M08-A i B; RN-M08-05, 08, 09 i 11; CA-M08-01, 06, 08, 12
i 14).

- **Accés:** DB1 (`dashboard.view`); sense, «no trobat» (CA-M08-01). Només llegeix: cap escriptura
  a la base de dades (RN-M08-06, CA-M08-14). DB2 no té cap acció a la primera versió.
- **Període** (RN-M08-08): mes, trimestre, any natural o darrers 12 mesos, sempre el que conté
  avui i de mesos sencers (P-641); un valor no vàlid a l'adreça torna al per defecte, sense error.
- **Memòria cau** (RN-M08-09): les xifres d'un panell i un període, compartides per a tots els
  comptes durant `DASHBOARD_CACHE_SECONDS` (tècnic, entorn; M08-6). Només xifres, mai dades
  personals. Els enllaços es calculen per a cada compte: un bloc enllaça al detall només si el
  compte té el permís del mòdul, que el torna a comprovar (RN-M08-05, CA-M08-06).
- **Ordre i blocs amagats** del compte (T-M08-12, `layout.arrange`), sobre les xifres compartides.
- Sense gràfics (T-M08-11, sessió de DISSENY): xifres i taules.
"""

import datetime

from django.conf import settings
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.core import business_settings
from apps.core.permissions import has_perm, request_permissions, require_perm
from apps.members.models import MembershipType

from . import layout, panels, privacy
from .indicators import CATALOG, PANELS

VIEW = "dashboard.view"  # DB1
DEFAULT_PERIOD = "dashboard.default_period"
PERIODS = {
    "month": _("Aquest mes"),
    "quarter": _("Aquest trimestre"),
    "year": _("Aquest any"),
    "last_12_months": _("Darrers 12 mesos"),
}
BREAKDOWN_LABELS = {"joined": _("Altes"), "left": _("Baixes")}


def _month_end(day: datetime.date) -> datetime.date:
    return (day.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(
        days=1
    )


def bounds(period: str, today: datetime.date) -> tuple[datetime.date, datetime.date]:
    """El primer i el darrer dia del període que conté `today`, de mesos sencers (P-641)."""
    if period == "month":
        return today.replace(day=1), _month_end(today)
    if period == "quarter":
        first = today.replace(month=3 * ((today.month - 1) // 3) + 1, day=1)
        return first, _month_end(first.replace(month=first.month + 2))
    if period == "last_12_months":
        months = today.year * 12 + today.month - 1 - 11
        return datetime.date(months // 12, months % 12 + 1, 1), _month_end(today)
    return datetime.date(today.year, 1, 1), datetime.date(today.year, 12, 31)


def default_period() -> str:
    """`dashboard.default_period` (T-M08-10); un valor fora de la llista no hauria de passar."""
    value = business_settings.get(DEFAULT_PERIOD)
    return value if value in PERIODS else "year"


def _figures(panel, starts_on, ends_on):
    """(blocs, mida mínima, hora del càlcul), de la memòria cau compartida si hi són."""
    key = f"dashboard:{panel}:{starts_on:%Y%m%d}:{ends_on:%Y%m%d}"
    found = cache.get(key)
    if found is None:
        now = timezone.now()
        blocks = panels.panel(panel, starts_on, ends_on, now=now)
        found = (blocks, privacy.min_group_size(timezone.localdate(now)), now)
        cache.set(key, found, settings.DASHBOARD_CACHE_SECONDS)
    return found


def _key_label(code, key, type_names):
    if isinstance(key, datetime.date):
        if code == "weekly_enrolments":
            return date_format(key, "SHORT_DATE_FORMAT")
        return date_format(key, "YEAR_MONTH_FORMAT")
    if code == "active_by_type":
        return type_names.get(key, key)
    return key


def _row(request, perms, block, min_size, type_names):
    indicator = CATALOG[block.code]
    link = ""
    if indicator.detail_permission and has_perm(
        request.user, indicator.detail_permission, permissions=perms
    ):
        link = reverse(indicator.detail_route)
    breakdowns = [
        {
            "label": BREAKDOWN_LABELS.get(breakdown.label, ""),
            "cells": [
                (_key_label(block.code, key, type_names), panels.text(block.code, cell, min_size))
                for key, cell in breakdown.cells.items()
            ],
            "total": panels.text(block.code, breakdown.total, min_size),
        }
        for breakdown in block.breakdowns
    ]
    return {
        "code": block.code,
        "name": indicator.name,
        "definition": indicator.definition,
        "help": indicator.help_text(),
        "unit": indicator.unit,
        "error": block.error,
        "value": None if block.breakdowns else panels.text(block.code, block.value, min_size),
        "breakdowns": breakdowns,
        "link": link,
    }


@never_cache
@require_GET
def dashboard_view(request, panel="general"):
    require_perm(request, VIEW)
    if panel not in PANELS:
        raise Http404
    period = request.GET.get("periode")
    if period not in PERIODS:
        period = default_period()
    starts_on, ends_on = bounds(period, timezone.localdate())
    blocks, min_size, computed_at = _figures(panel, starts_on, ends_on)
    perms = request_permissions(request)
    type_names = dict(MembershipType.objects.values_list("code", "name"))
    context = {
        "panels": PANELS,
        "panel": panel,
        "panel_name": PANELS[panel],
        "periods": PERIODS,
        "period": period,
        "starts_on": starts_on,
        "ends_on": ends_on,
        "computed_at": computed_at,
        "blocks": [
            _row(request, perms, block, min_size, type_names)
            for block in layout.arrange(request.user, blocks).values()
        ],
    }
    return render(request, "dashboard/dashboard.html", context)
