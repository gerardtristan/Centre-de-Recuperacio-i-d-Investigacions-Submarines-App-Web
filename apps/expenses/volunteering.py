"""Hores de voluntariat (T-M09-17; RN-M09-21): per funció, mai per persona, i sense valor en
euros. Cap camp no porta el nom de ningú; el formulari ho dirà (text d'ajuda)."""

from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.core import audit

from .models import VolunteerHours
from .services import ExpenseRejected, _require

VOLUNTEERING = "expenses.volunteering"  # MG13
VOLUNTEER_HOURS_RECORDED = "expenses.volunteer_hours_recorded"


@transaction.atomic
def record_volunteer_hours(
    *, date, hours, role_label, department, by, description=""
) -> VolunteerHours:
    _require(by, VOLUNTEERING)
    try:
        hours = Decimal(str(hours)).quantize(Decimal("0.01"))
    except InvalidOperation:  # text, infinit o massa gran
        hours = Decimal("NaN")
    if not hours.is_finite() or not Decimal("0") < hours <= Decimal("999.99"):
        raise ExpenseRejected(_("Les hores han de ser més de 0 i com a màxim 999,99."))
    role_label, description = (role_label or "").strip(), (description or "").strip()
    if not role_label or len(role_label) > 80 or len(description) > 200:
        raise ExpenseRejected(_("Cal la funció (80 caràcters com a màxim), mai el nom."))
    if not department.active:
        raise ExpenseRejected(_("Tria un departament actiu."))
    entry = VolunteerHours.objects.create(
        date=date,
        hours=hours,
        role_label=role_label,
        department=department,
        description=description,
        recorded_by=by,
    )
    audit.record(
        VOLUNTEER_HOURS_RECORDED,
        actor=by,
        target=entry,
        details={"hours": str(hours), "department": department.name},
    )
    return entry
