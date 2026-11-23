"""Tancar i reobrir períodes (T-M09-16; P-M09-G; RN-M09-15, 16, 24 i 26; CA-M09-13, 14, 15 i 29).

- `checklist(period)`: la llista de control. Línies de l'extracte sense conciliar amb data dins el
  període, activitats acabades dins el període sense tancar, despeses del període sense factura,
  despeses pagades dins el període sense conciliar i factures fallides del període; i els
  elements que el període anterior hi va portar com a excepció i encara no s'han resolt. Cada
  element té una clau estable i un text sense dades personals.
- `close(period, by=…, exceptions={clau: motiu})`: MG11. Es tanca amb la llista buida o portant
  cada element al període següent amb motiu (RN-M09-26 [A validar: tresorer, S-M09-15]). Un
  element sense motiu bloqueja (CA-M09-29). Els períodes es tanquen per ordre.
- `reopen(period, by=…, reason=…)`: MG12 (només l'administrador, CA-M09-15), amb motiu i registre.
  Només es reobre el darrer període tancat: la guarda de la 04 és una sola data (P-471).
- `create_next(by=…, starts_on=None)`: MG11. El període nou comença l'endemà del darrer i dura el
  que diu `margin.period_length` (VC-32, mensual o trimestral) en aquell moment: els existents no
  canvien (RN-M09-28, CA-M09-35). El primer període comença el dia que tria el tresorer.
- `recompute_margin(activity, by=…)`: amb el període del marge congelat reobert, MG7 fa un marge
  nou que substitueix l'anterior (`supersedes`, amb el motiu de la reobertura) i que no inclou els
  moviments tardans (RN-M09-24).

**Fora d'aquesta peça:** el correu al tresorer i a la junta en reobrir (S-M09-13) necessita una
plantilla del nucli; ara només queda al registre. La pantalla, amb les vistes del 09.
"""

import calendar
import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.activities.models import Activity
from apps.core import audit, business_settings
from apps.core.permission_catalog import SCOPE_ALL
from apps.core.permissions import scope_for
from apps.expenses.models import Expense
from apps.expenses.services import without_invoice
from apps.invoicing.models import Invoice
from apps.treasury.models import Reconciliation, StatementLineState

from . import calc, closing, reports, services
from .models import MarginSnapshot, Period, PeriodEvent

CLOSE = "expenses.periods.close"  # MG11
REOPEN = "expenses.periods.reopen"  # MG12
PERIOD_CLOSED = "margins.period_closed"
PERIOD_REOPENED = "margins.period_reopened"
MARGIN_RECOMPUTED = "margins.margin_recomputed"
PERIOD_CREATED = "margins.period_created"
LENGTH = "margin.period_length"  # VC-32
MONTHS = {"monthly": 1, "quarterly": 3}  # les opcions de VC-32
S = Period.Status


class PeriodNotReady(ValidationError):
    """La llista de control té elements sense resoldre ni portar amb motiu (CA-M09-13, 29)."""

    def __init__(self, items):
        super().__init__([item["label"] for item in items])
        self.items = list(items)


def _require(by, code) -> None:
    if scope_for(by, code) != SCOPE_ALL:
        raise Http404


def _own_items(period) -> list[dict]:
    start, end = period.starts_on, period.ends_on
    items = []
    lines = StatementLineState.objects.filter(
        status__in=(StatementLineState.Status.PENDING, StatementLineState.Status.PROPOSED),
        statement_line__value_date__range=(start, end),
    ).order_by("statement_line__value_date", "pk")
    for state in lines:
        line = state.statement_line
        items.append({
            "key": f"statement_line:{line.pk}",
            "label": _("Línia de l'extracte del %(day)s sense conciliar (%(cents)s cèntims).")
            % {"day": f"{line.value_date:%d/%m/%Y}", "cents": line.amount_cents},
        })  # fmt: skip
    done = Activity.objects.filter(status=Activity.Status.DONE, ends_on__range=(start, end))
    for activity in done.order_by("ends_on", "pk"):
        items.append({
            "key": f"activity:{activity.pk}",
            "label": _("Activitat feta sense tancar: %(title)s.") % {"title": activity.title},
        })  # fmt: skip
    for expense in without_invoice().filter(invoice_date__range=(start, end)).order_by("pk"):
        items.append({
            "key": f"expense_without_invoice:{expense.pk}",
            "label": _("Despesa sense factura: %(what)s.") % {"what": expense.description},
        })  # fmt: skip
    reconciled = Reconciliation.objects.filter(undo__isnull=True).values("matched_movements")
    unreconciled = Expense.objects.filter(
        status=Expense.Status.PAID, paid_movement__value_date__range=(start, end)
    ).exclude(paid_movement__in=reconciled)
    for expense in unreconciled.order_by("pk"):
        items.append({
            "key": f"expense_unreconciled:{expense.pk}",
            "label": _("Despesa pagada sense conciliar: %(what)s.") % {"what": expense.description},
        })  # fmt: skip
    failed = Invoice.objects.filter(
        status=Invoice.Status.FAILED, created_at__date__range=(start, end)
    )
    for invoice in failed.order_by("pk"):
        items.append({
            "key": f"invoice_failed:{invoice.pk}",
            "label": _("Factura fallida núm. intern %(pk)s.") % {"pk": invoice.pk},
        })  # fmt: skip
    return items


def _previous(period):
    return Period.objects.filter(ends_on__lt=period.starts_on).order_by("-ends_on").first()


def _carried(period) -> list[dict]:
    """Els elements que el període anterior va portar a aquest i que encara no s'han resolt."""
    previous = _previous(period)
    if previous is None or previous.status != S.CLOSED:
        return []
    event = previous.events.filter(action=PeriodEvent.Action.CLOSE).order_by("-at", "-pk").first()
    if event is None or not event.exceptions:
        return []
    pending = {item["key"] for item in checklist(previous)}
    return [
        {"key": e["key"], "label": e["label"], "carried_from": previous.pk}
        for e in event.exceptions
        if e["key"] in pending
    ]


def checklist(period) -> list[dict]:
    """La llista de control del període (P-M09-G pas 1)."""
    own = _own_items(period)
    keys = {item["key"] for item in own}
    return own + [item for item in _carried(period) if item["key"] not in keys]


def close(period, *, by, exceptions=None, now=None) -> PeriodEvent:
    """Tanca el període (P-M09-G pas 3)."""
    _require(by, CLOSE)
    exceptions = {key: (reason or "").strip() for key, reason in (exceptions or {}).items()}
    with transaction.atomic():
        period = Period.objects.select_for_update().get(pk=period.pk)
        if period.status != S.OPEN:
            raise ValidationError(_("Aquest període ja és tancat."))
        if Period.objects.filter(ends_on__lt=period.starts_on, status=S.OPEN).exists():
            raise ValidationError(_("Abans s'han de tancar els períodes anteriors."))
        items = checklist(period)
        keys = {item["key"] for item in items}
        if set(exceptions) - keys:
            raise ValidationError(_("Hi ha excepcions d'elements que no són a la llista."))
        blocking = [item for item in items if not exceptions.get(item["key"])]
        if blocking:
            raise PeriodNotReady(blocking)
        carried = [
            {"key": item["key"], "label": item["label"], "reason": exceptions[item["key"]]}
            for item in items
        ]
        period.status = S.CLOSED
        period.save(update_fields=["status"])
        event = PeriodEvent.objects.create(
            period=period, action=PeriodEvent.Action.CLOSE, actor=by,
            at=now or timezone.now(), checklist=items, exceptions=carried,
        )  # fmt: skip
        audit.record(
            PERIOD_CLOSED, actor=by, target=period, field="status", old=S.OPEN, new=S.CLOSED,
            details={"exceptions": carried},
        )  # fmt: skip
    return event


def reopen(period, *, by, reason, now=None) -> PeriodEvent:
    """Reobre el darrer període tancat, amb motiu (RN-M09-16). Només per als errors de la feina
    del propi període; el que arriba tard no el reobre."""
    _require(by, REOPEN)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal el motiu de la reobertura."))
    with transaction.atomic():
        period = Period.objects.select_for_update().get(pk=period.pk)
        if period.status != S.CLOSED:
            raise ValidationError(_("Aquest període no és tancat."))
        if Period.objects.filter(status=S.CLOSED, starts_on__gt=period.starts_on).exists():
            raise ValidationError(_("Només es pot reobrir el darrer període tancat."))
        period.status = S.OPEN
        period.save(update_fields=["status"])
        event = PeriodEvent.objects.create(
            period=period, action=PeriodEvent.Action.REOPEN, reason=reason, actor=by,
            at=now or timezone.now(), checklist=checklist(period),
        )  # fmt: skip
        audit.record(
            PERIOD_REOPENED, actor=by, target=period, field="status", old=S.CLOSED, new=S.OPEN,
            reason=reason,
        )  # fmt: skip
    return event


def _add_months(day, months):
    month = day.month - 1 + months
    year, month = day.year + month // 12, month % 12 + 1
    return day.replace(
        year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1])
    )


def next_dates(starts_on=None) -> tuple[datetime.date, datetime.date] | None:
    """Les dates del període que es crearia ara; sense cap període, cal `starts_on`."""
    last = Period.objects.order_by("-ends_on").first()
    if last is not None:
        starts_on = last.ends_on + datetime.timedelta(days=1)
    if starts_on is None:
        return None
    months = MONTHS[business_settings.get(LENGTH)]
    return starts_on, _add_months(starts_on, months) - datetime.timedelta(days=1)


def create_next(*, by, starts_on=None, today=None) -> Period:
    """RN-M09-28: el període següent, sense forats ni solapaments. No se'n crea cap mentre el
    darrer encara no ha començat (no s'apilen períodes futurs)."""
    _require(by, CLOSE)
    today = today or timezone.localdate()
    with transaction.atomic():
        last = Period.objects.select_for_update().order_by("-ends_on").first()
        if last is not None and last.starts_on > today:
            raise ValidationError(_("El darrer període encara no ha començat."))
        if last is None and not isinstance(starts_on, datetime.date):
            raise ValidationError(_("Cal el dia que comença el primer període."))
        starts_on, ends_on = next_dates(None if last else starts_on)
        period = Period.objects.create(starts_on=starts_on, ends_on=ends_on)
        audit.record(
            PERIOD_CREATED, actor=by, target=period,
            details={"starts_on": starts_on.isoformat(), "ends_on": ends_on.isoformat(),
                     "length": business_settings.get(LENGTH)},
        )  # fmt: skip
    return period


def _period_of(day):
    return Period.objects.filter(starts_on__lte=day, ends_on__gte=day).first()


def late_movements(activity, period):
    """RN-M09-24: moviments d'origen extern que van entrar al període obert amb una data de valor
    original dins el període reobert. Surten a part i no compten al marge recalculat."""
    return services.activity_movements(activity).filter(
        original_value_date__range=(period.starts_on, period.ends_on)
    )


def recompute_margin(activity, *, by) -> MarginSnapshot:
    """Un marge nou que substitueix el congelat, només amb el seu període reobert (RN-M09-07)."""
    if scope_for(by, closing.CLOSE) != SCOPE_ALL:
        raise Http404
    current = closing.current(activity)
    if current is None:
        raise ValidationError(_("Aquesta activitat no té cap marge congelat."))
    first = reports.first_closed_at(current)
    period = _period_of(timezone.localdate(first))
    reopened = (
        period is not None
        and period.status == S.OPEN
        and period.events.filter(action=PeriodEvent.Action.REOPEN, at__gt=first)
        .order_by("-at")
        .first()
    )
    if not reopened:
        raise ValidationError(_("Només es recalcula el marge d'un període reobert."))
    late = late_movements(activity, period).values("pk")
    counted = services.activity_movements(activity).exclude(pk__in=late)
    margin = calc.compute(services.real_inputs(activity, movements=counted), calc.REAL)
    with transaction.atomic():
        snapshot = MarginSnapshot.objects.create(
            activity=activity,
            income_enrolments_cents=margin.income_enrolments_cents,
            other_direct_income_cents=margin.other_direct_income_cents,
            direct_costs_cents=margin.direct_costs_cents,
            material_cost_cents=margin.material_cost_cents,
            margin_cents=margin.margin_cents,
            margin_pct_tenths=margin.margin_pct_tenths,
            participants=margin.participants,
            breakdown=margin.breakdown,
            closed_by=by,
            # L'informe el compta al període del tancament original (`reports.first_closed_at`);
            # l'ajust posterior es compta a partir d'ara.
            closed_at=timezone.now(),
            supersedes=current,
            reopen_reason=reopened.reason,
        )
        audit.record(
            MARGIN_RECOMPUTED, actor=by, target=snapshot, old=current.margin_cents,
            new=margin.margin_cents, reason=reopened.reason, details={"activity": activity.pk},
        )  # fmt: skip
    return snapshot
