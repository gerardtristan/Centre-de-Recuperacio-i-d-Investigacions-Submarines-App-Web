"""`grants.granted_by_department(starts_on, ends_on)` (M09-ajuts-8, per al 08; T-M08-06).

Només lectura i només imports: el concedit de les sol·licituds resoltes dins del període (dates
incloses), per departament. Una denegada no hi compta; una de justificada o tancada, sí, si té
import concedit. El cobrat ja surt a l'informe per departament (`margins.department_report`)."""

from django.db.models import Sum

from .models import GrantApplication


def granted_by_department(starts_on, ends_on) -> dict[str, int]:
    """{nom del departament: cèntims concedits}, per nom."""
    rows = (
        GrantApplication.objects.filter(
            resolved_on__range=(starts_on, ends_on), amount_granted_cents__isnull=False
        )
        .exclude(status=GrantApplication.Status.DENIED)
        .values("department__name")
        .annotate(cents=Sum("amount_granted_cents"))
        .order_by("department__name")
    )
    return {row["department__name"]: row["cents"] for row in rows}
