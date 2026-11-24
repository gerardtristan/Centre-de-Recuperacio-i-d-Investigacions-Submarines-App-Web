"""Dades dels panells del dashboard (T-M08-05 general i socis; T-M08-06 econòmic; T-M08-07
activitat; M08-6).

Cada panell és un diccionari {codi de l'indicador: `Block`}, en l'ordre del catàleg. Cada xifra
és la que torna el servei de lectura del mòdul (RN-M08-04): aquí només es tria la data, se sumen
els mesos i es passa pels grups petits. Res de cap persona (RN-M08-01): només recomptes,
percentatges i imports.
- **Grups petits** (RN-M08-02): un desglossament d'un indicador de persones passa per
  `privacy.suppress`; una xifra sola no és un desglossament i no s'amaga.
- **Mòdul absent o que falla** (RN-M08-11): sense servei, el bloc no surt (les conferències,
  fins que existeixi l'11; els mandats, sense campanya oberta); si el servei falla, el bloc porta
  `error` i la resta del panell es calcula igual.
- **Imports** (RN-M08-04): en cèntims fins a `text`, que els mostra en euros amb dos decimals;
  la suma dels departaments (o dels comptes) és el total. Els imports no amaguen res.
- **Període** (RN-M08-08): de `starts_on` a `ends_on`, dates incloses; el selector és de la
  T-M08-09. «El darrer dia del període» és avui si el període encara no s'ha acabat.

La vista, el permís DB1, els enllaços al detall i la memòria cau són de la T-M08-09; els gràfics,
de la T-M08-11 (sessió de DISSENY).
"""

import datetime
import logging
from dataclasses import dataclass

from django.utils import timezone

from apps.activities import stats as activity_stats
from apps.core import business_settings
from apps.core.charges import euros
from apps.core.models import Department
from apps.equipment import reviews as equipment_reviews
from apps.equipment import stock as equipment_stock
from apps.expenses import services as expenses
from apps.grants import calendar as grants_calendar
from apps.grants import totals as grants_totals
from apps.grants.reminders import DEADLINE_DAYS
from apps.licences.listing import TO_RENEW_DAYS, expiring
from apps.margins.reports import department_report
from apps.members import services as members
from apps.members.models import Member
from apps.payments import campaigns
from apps.treasury import balances as treasury

from . import privacy
from .indicators import CATALOG

logger = logging.getLogger(__name__)
M = Member.Status
NOT_AVAILABLE = object()  # el servei no hi és: el bloc no surt (RN-M08-11)


@dataclass(frozen=True)
class Breakdown:
    label: str  # «» si l'indicador només en té un; «joined» i «left» per a altes i baixes
    cells: dict  # {clau: privacy.Cell}
    total: privacy.Cell


@dataclass(frozen=True)
class Block:
    code: str
    value: int | None = None  # xifra sola (recompte, percentatge o cèntims); None = sense dades
    breakdowns: tuple = ()  # desglossaments (Breakdown)
    error: bool = False  # RN-M08-11: «No s'ha pogut calcular»


def _months(starts_on, ends_on):
    """El darrer dia de cada mes del període (o `ends_on`, si és abans)."""
    # shortcut: el període comença el dia 1 perquè `members.stats` compta per mesos naturals;
    # si «darrers 12 mesos» (T-M08-09) no fos de mesos sencers, caldria un servei per dates.
    if starts_on.day != 1:
        raise ValueError("El període ha de començar el dia 1 d'un mes.")
    month = starts_on
    while month <= ends_on:
        following = (month + datetime.timedelta(days=31)).replace(day=1)
        yield month, min(following - datetime.timedelta(days=1), ends_on)
        month = following


class Reads:
    """Les lectures d'un panell, cadascuna feta una sola vegada encara que la facin servir
    diversos blocs."""

    def __init__(self, starts_on, ends_on, now=None):
        self.now = now or timezone.now()
        self.today = timezone.localdate(self.now)
        self.starts_on, self.ends_on = starts_on, ends_on
        self.last_day = min(ends_on, self.today)
        self.min_size = privacy.min_group_size(self.today)
        self._memo = {}

    def _once(self, key, read):
        if key not in self._memo:
            self._memo[key] = read()
        return self._memo[key]

    def members_on(self, day):
        return self._once(("members", day), lambda: members.stats(day))

    def monthly(self):
        """{primer dia del mes: MemberStats del darrer dia del mes} dels mesos ja començats."""
        return {
            first: self.members_on(min(last, self.today))
            for first, last in _months(self.starts_on, self.ends_on)
            if first <= self.today
        }

    def activities(self):
        return self._once(
            "activities",
            lambda: activity_stats.stats(self.starts_on, self.ends_on, now=self.now),
        )

    def departments(self):
        """{departament: `margins.department_report` del període}, l'informe del 09 (HU-M08-02)."""
        return self._once("departments", lambda: {
            department.name: department_report(department, self.starts_on, self.ends_on)
            for department in Department.objects.order_by("name")
        })  # fmt: skip

    def without_invoice(self):
        return self._once(
            "without_invoice",
            lambda: expenses.without_invoice_totals(self.starts_on, self.ends_on),
        )

    def breakdown(self, code, counts, label=""):
        if CATALOG[code].kind == "people":
            cells, total = privacy.suppress(counts, self.min_size)
        else:
            cells = {key: privacy.Cell(value, privacy.SHOWN) for key, value in counts.items()}
            total = privacy.Cell(sum(counts.values()), privacy.SHOWN)
        return Breakdown(label, cells, total)


def _with_status(stats, status) -> dict:
    """{codi del tipus: recompte} dels socis en un estat."""
    by_type = {}
    for (type_code, state), count in stats.by_type_and_status.items():
        if state == status:
            by_type[type_code] = by_type.get(type_code, 0) + count
    return by_type


# --- Lectures de cada indicador ---------------------------------------------------------------


def active_members(r):
    return sum(_with_status(r.members_on(r.last_day), M.ACTIVE).values())


def new_members(r):
    return sum(stats.joined for stats in r.monthly().values())


def unpaid_members(r):
    return sum(_with_status(r.members_on(r.last_day), M.UNPAID).values())


def free_places(r):
    return r.activities().free_places


def licences_to_renew(r):
    return expiring(business_settings.get(TO_RENEW_DAYS, r.today), r.today).count()


def equipment_to_review(r):
    return equipment_reviews.due_items(r.today).count()


def grants_closing(r):
    days = max(business_settings.get(DEADLINE_DAYS, r.today), default=0)
    return len(grants_calendar.calendar(r.today, r.today + datetime.timedelta(days=days)))


def joins_and_leaves(r):
    monthly = r.monthly()
    joined = {month: stats.joined for month, stats in monthly.items()}
    left = {month: stats.left for month, stats in monthly.items()}
    code = "joins_and_leaves"
    return (r.breakdown(code, joined, "joined"), r.breakdown(code, left, "left"))


def active_by_type(r):
    return (r.breakdown("active_by_type", _with_status(r.members_on(r.last_day), M.ACTIVE)),)


def retention(r):
    """1 − baixes del període / socis actius el primer dia del període, en %, arrodonit."""
    active = sum(_with_status(r.members_on(r.starts_on), M.ACTIVE).values())
    if not active or r.starts_on > r.today:
        return None
    left = sum(stats.left for stats in r.monthly().values())
    return round(100 - 100 * left / active)


def signed_mandates(r):
    campaign = campaigns.open_campaign_now()
    if campaign is None:
        return NOT_AVAILABLE
    return campaigns.campaign_status(campaign)["direct_debit"]


def occupancy(r):
    return r.activities().occupancy_percent


def attendance(r):
    return r.activities().attendance_percent


def weekly_enrolments(r):
    return (r.breakdown("weekly_enrolments", r.activities().weekly),)


def equipment_in_use(r):
    return equipment_stock.in_use_count(r.last_day)


def activity_margin(r):
    return sum(report.margins_total_cents for report in r.departments().values())


def _by_department(r, code, cents_of):
    cents = {name: cents_of(report) for name, report in r.departments().items()}
    return (r.breakdown(code, {name: value for name, value in cents.items() if value}),)


def department_income(r):
    """Ajuts i altres ingressos sense activitat (els de les activitats són dins del marge)."""
    return _by_department(
        r, "department_income", lambda report: report.grants_cents + report.other_income_cents
    )


def department_expenses(r):
    """Despeses pagades sense activitat (les repartides a activitats són dins del marge)."""
    return _by_department(
        r, "department_expenses", lambda report: report.expenses_without_activity_cents
    )


def grants_granted(r):
    granted = grants_totals.granted_by_department(r.starts_on, r.ends_on)
    return (r.breakdown("grants_granted", granted),)


def expenses_without_invoice(r):
    return r.without_invoice()[0]


def expenses_without_invoice_amount(r):
    return r.without_invoice()[1]


def treasury_balances(r):
    """Saldo de cada compte el darrer dia del període; un compte inactiu a zero no surt."""
    accounts = treasury.balances(r.last_day)
    cents = {a.name: a.balance_cents for a in accounts if a.active or a.balance_cents}
    return (r.breakdown("treasury_balances", cents),)


READS = {
    "active_members": active_members,
    "new_members": new_members,
    "unpaid_members": unpaid_members,
    "free_places": free_places,
    "licences_to_renew": licences_to_renew,
    "equipment_to_review": equipment_to_review,
    "grants_closing": grants_closing,
    "joins_and_leaves": joins_and_leaves,
    "active_by_type": active_by_type,
    "retention": retention,
    "signed_mandates": signed_mandates,
    "occupancy": occupancy,
    "attendance": attendance,
    "weekly_enrolments": weekly_enrolments,
    "equipment_in_use": equipment_in_use,
    "activity_margin": activity_margin,
    "department_income": department_income,
    "department_expenses": department_expenses,
    "grants_granted": grants_granted,
    "expenses_without_invoice": expenses_without_invoice,
    "expenses_without_invoice_amount": expenses_without_invoice_amount,
    "treasury_balances": treasury_balances,
}


def _block(code, reads) -> Block | None:
    read = READS.get(code)
    if read is None:
        return None  # sense servei (l'11) o encara sense lectura: el bloc no surt
    try:
        result = read(reads)
    except Exception:  # RN-M08-11: un servei que falla no fa caure el panell
        logger.exception("Dashboard: no s'ha pogut calcular l'indicador %s", code)
        return Block(code, error=True)
    if result is NOT_AVAILABLE:
        return None
    if isinstance(result, tuple):
        return Block(code, breakdowns=result)
    return Block(code, value=result)


def panel(name, starts_on, ends_on, now=None) -> dict[str, Block]:
    """Els blocs d'un panell per al període, en l'ordre del catàleg."""
    reads = Reads(starts_on, ends_on, now)
    blocks = {}
    for code, indicator in CATALOG.items():
        if name in indicator.panels:
            block = _block(code, reads)
            if block is not None:
                blocks[code] = block
    return blocks


def text(code, value, min_size) -> str:
    """Una xifra o una cel·la, per mostrar-la: imports en euros amb dos decimals (RN-M08-04),
    percentatges amb «%» i les cel·les amagades com diu `privacy.Cell.label`."""
    if isinstance(value, privacy.Cell):
        if value.state != privacy.SHOWN:
            return value.label(min_size)
        value = value.value
    if value is None:
        return "—"
    unit = CATALOG[code].unit
    if unit == "cents":
        return euros(value)
    return f"{value} %" if unit == "percent" else str(value)
