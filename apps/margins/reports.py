"""Informes per departament, subtipus i projecte, i CSV (T-M09-14; P-M09-E; RN-M09-08; S-M09-06;
CA-M09-20). Només lectura: qui els mostra comprova MG8.

Un departament mostra per separat la suma dels marges de les seves activitats tancades i les
despeses sense activitat (S-M09-06); els ajuts surten en una línia pròpia i mai dins el marge
d'una activitat (RN-M09-08)."""

import csv
import io
from collections.abc import Mapping
from dataclasses import dataclass

from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.expenses.models import Expense, ExpenseAllocation, OtherIncome

from .models import MarginSnapshot

GROUPS = ("activity", "subtype", "project")


@dataclass(frozen=True)
class DepartmentReport:
    department: str
    activity_margins_cents: Mapping[str, int]  # activitat (o subtipus, o projecte) → marge
    expenses_without_activity_cents: int
    grants_cents: int
    other_income_cents: int

    @property
    def margins_total_cents(self) -> int:
        return sum(self.activity_margins_cents.values())

    @property
    def total_cents(self) -> int:
        return (
            self.margins_total_cents
            - self.expenses_without_activity_cents
            + self.grants_cents
            + self.other_income_cents
        )


def _label(activity, group_by) -> str:
    if group_by == "subtype":
        return activity.subtype.name if activity.subtype_id else _("Sense subtipus")
    if group_by == "project":
        return activity.project.name if activity.project_id else _("Sense projecte")
    # El número la fa única: dues sortides poden tenir el mateix títol i el mateix dia.
    return f"{activity.title} ({activity.starts_on:%d/%m/%Y}, núm. {activity.pk})"


def first_closed_at(snapshot):
    """Un marge recalculat en reobrir el període (T-M09-16) és del període del tancament
    original."""
    while snapshot.supersedes_id:
        snapshot = snapshot.supersedes
    return snapshot.closed_at


def _frozen_margins(department, starts_on, ends_on, group_by="activity") -> dict[str, int]:
    """Marges congelats vigents (T-M09-12) de les activitats del departament tancades dins el
    període, per activitat, subtipus o projecte (P-M09-E)."""
    if group_by not in GROUPS:
        raise ValueError(f"agrupació desconeguda: {group_by}")
    snapshots = (
        MarginSnapshot.objects.filter(activity__department=department, superseded_by__isnull=True)
        .select_related("activity__subtype", "activity__project")
        .order_by("activity__starts_on", "pk")
    )
    margins: dict[str, int] = {}
    for snapshot in snapshots:
        if starts_on <= timezone.localdate(first_closed_at(snapshot)) <= ends_on:
            key = _label(snapshot.activity, group_by)
            margins[key] = margins.get(key, 0) + snapshot.margin_cents
    return margins


def department_report(department, starts_on, ends_on, group_by="activity") -> DepartmentReport:
    """`margins.department_report` (M09-8) per a un període (dates incloses). Les despeses
    pagades compten per la data de valor del pagament; la part repartida a activitats (T-M09-07)
    ja és dins el marge de cada activitat i no torna a sortir com a despesa sense activitat."""
    expenses = Expense.objects.filter(
        department=department,
        status=Expense.Status.PAID,
        paid_movement__value_date__range=(starts_on, ends_on),
    )
    spent = expenses.aggregate(t=Sum("amount_cents"))["t"] or 0
    allocated = (
        ExpenseAllocation.objects.filter(expense__in=expenses).aggregate(t=Sum("amount_cents"))["t"]
        or 0
    )
    incomes = OtherIncome.objects.filter(
        department=department, movement__value_date__range=(starts_on, ends_on)
    )
    grants = incomes.filter(kind=OtherIncome.Kind.GRANT)
    return DepartmentReport(
        department=department.name,
        activity_margins_cents=_frozen_margins(department, starts_on, ends_on, group_by),
        expenses_without_activity_cents=spent - allocated,
        grants_cents=grants.aggregate(t=Sum("amount_cents"))["t"] or 0,
        other_income_cents=incomes.exclude(kind=OtherIncome.Kind.GRANT).aggregate(
            t=Sum("amount_cents")
        )["t"]
        or 0,
    )


def _safe(text: str) -> str:
    # Un text que comença com una fórmula no s'ha d'executar en obrir el CSV.
    return f"'{text}" if text[:1] in ("=", "+", "-", "@") else text


def to_csv(report: DepartmentReport) -> str:
    """El CSV de l'informe (S-M09-10), en cèntims enters perquè no hi hagi arrodoniments."""
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";", lineterminator="\n")
    writer.writerow([_("Departament"), _("Concepte"), _("Import (cèntims)")])
    for name, cents in report.activity_margins_cents.items():
        label = _("Marge: %(name)s") % {"name": name}
        writer.writerow([_safe(report.department), _safe(label), cents])
    rows = [
        (_("Suma dels marges"), report.margins_total_cents),
        (_("Despeses sense activitat"), -report.expenses_without_activity_cents),
        (_("Ajuts"), report.grants_cents),
        (_("Altres ingressos sense activitat"), report.other_income_cents),
        (_("Total del departament"), report.total_cents),
    ]
    for label, cents in rows:
        writer.writerow([_safe(report.department), label, cents])
    return out.getvalue()
