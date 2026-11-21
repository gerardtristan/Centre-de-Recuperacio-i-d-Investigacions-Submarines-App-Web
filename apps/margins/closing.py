"""Tancament econòmic d'una activitat i marge congelat (T-M09-12; P-M09-D pas 5; RN-M09-07 i 12;
CA-M09-10 i 11; MG7).

- `close_activity(activitat, by=…)`: només amb MG7 (el tresorer i l'administrador). Es rebutja
  amb els motius si el 02 (`closing_blockers`, també el material pendent del 03) o el 09 (despeses
  repartides a l'activitat sense factura, RN-M09-12) tenen res pendent. Si no, calcula el marge
  real, el congela (`MarginSnapshot`, només INSERT) i crida `activities.mark_closed`, tot en una
  sola transacció.
- `later_adjustments(snapshot)`: el que ha entrat després del tancament (devolucions, comissions o
  repartiments tardans). El marge congelat no canvia: surt al costat com a «ajust posterior» i
  compta al període on entra (CA-M09-11).

**Fora d'aquesta peça:** reobrir un període i substituir el marge (`supersedes`, T-M09-16) i la
pantalla (vistes del 09).
"""

from dataclasses import dataclass

from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import ngettext

from apps.activities import closing as activities
from apps.core import audit
from apps.core.permission_catalog import SCOPE_ALL
from apps.core.permissions import scope_for
from apps.expenses.models import ExpenseAllocation
from apps.expenses.services import without_invoice

from . import calc, services
from .models import MarginSnapshot

CLOSE = "expenses.margin.close_activity"  # MG7
ACTIVITY_CLOSED = "margins.activity_closed"
ClosingBlocked = activities.ClosingBlocked


def blockers(activity) -> list[str]:
    """Els motius del 02 i del 09 que impedeixen tancar l'activitat, sense dades personals."""
    reasons = activities.closing_blockers(activity)
    missing = without_invoice().filter(allocations__activity=activity).distinct().count()
    if missing:
        reasons.append(
            ngettext(
                "Hi ha %(count)s despesa repartida a l'activitat sense factura.",
                "Hi ha %(count)s despeses repartides a l'activitat sense factura.",
                missing,
            )
            % {"count": missing}
        )
    return reasons


def close_activity(activity, *, by, now=None, request=None) -> MarginSnapshot:
    """`margins.close_activity` (M09-8)."""
    if scope_for(by, CLOSE) != SCOPE_ALL:
        raise Http404
    reasons = blockers(activity)
    if reasons:
        raise ClosingBlocked(reasons)
    now = now or timezone.now()
    with transaction.atomic():
        # Bloqueja l'activitat i torna a comprovar els motius del 02 dins la transacció.
        activities.mark_closed(activity, actor=by, now=now, request=request)
        late = blockers(activity)  # una despesa sense factura repartida mentrestant
        if late:
            raise ClosingBlocked(late)
        margin = calc.compute(services.real_inputs(activity), calc.REAL)
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
            closed_at=now,
        )
        audit.record(
            ACTIVITY_CLOSED,
            actor=by,
            target=snapshot,
            new=margin.margin_cents,
            details={"activity": activity.pk},
            request=request,
        )
    return snapshot


def current(activity) -> MarginSnapshot | None:
    """El marge congelat vigent (el que no és substituït)."""
    return MarginSnapshot.objects.filter(activity=activity, superseded_by__isnull=True).first()


@dataclass(frozen=True)
class LaterAdjustments:
    enrolments_cents: int  # ingressos menys devolucions arribats després del tancament
    commissions_cents: int
    costs_cents: int  # repartiments fets després del tancament

    @property
    def margin_effect_cents(self) -> int:
        return self.enrolments_cents - self.commissions_cents - self.costs_cents


def later_adjustments(snapshot) -> LaterAdjustments:
    """«Ajust posterior» (RN-M09-07): el que ha entrat després de congelar el marge."""
    activity = snapshot.activity
    moved = services.activity_movements(activity).filter(recorded_at__gt=snapshot.closed_at)
    enrolments, commissions = services.signed_income(moved)
    allocations = ExpenseAllocation.objects.filter(
        activity=activity, created_at__gt=snapshot.closed_at
    ).exclude(expense__status="annulled")
    return LaterAdjustments(
        enrolments_cents=enrolments,
        commissions_cents=commissions,
        costs_cents=sum(a.amount_cents for a in allocations),
    )
