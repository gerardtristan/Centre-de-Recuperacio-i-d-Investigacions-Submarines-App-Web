"""Informes operatius (T-M02-24b; AC20): ocupació de les activitats, participants d'una activitat
i horari per imprimir, amb les descàrregues en CSV.

Els serveis (`reports.py`) comproven el permís i l'abast (l'instructor, només les activitats on fa
classe; fora, «no trobat» i registre) i decideixen què es veu (C3). Les pàgines s'imprimeixen o es
desen com a PDF des del navegador (decisió 079). El CSV dels participants porta noms: es baixa
amb un POST i queda al registre; el de l'ocupació només porta recomptes (GET).
"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.permissions import permission_required

from .. import reports
from ..models import Activity
from ..permissions import REPORTS


def _csv(content: bytes, name: str) -> HttpResponse:
    response = HttpResponse(content, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{name}"'
    return response


@never_cache
@permission_required(REPORTS)
@require_GET
def occupancy_view(request):
    if request.GET.get("format") == "csv":
        return _csv(reports.occupancy_csv(viewer=request.user), "ocupacio-activitats.csv")
    return render(
        request, "activities/reports.html", {"rows": reports.occupancy(viewer=request.user)}
    )


@never_cache
@permission_required(REPORTS)
@require_http_methods(["GET", "POST"])
def participants_view(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    if request.method == "POST":
        content = reports.participants_csv(activity, viewer=request.user, request=request)
        return _csv(content, f"participants-activitat-{activity.pk}.csv")
    headers, rows = reports.participants_report(activity, viewer=request.user, request=request)
    # Cada cel·la amb la seva capçalera: a 390 px la taula es llegeix per targetes (data-etiqueta).
    rows = [list(zip(headers, cells, strict=True)) for cells in rows]
    context = {"activity": activity, "headers": headers, "rows": rows}
    return render(request, "activities/report_participants.html", context)


@never_cache
@permission_required(REPORTS)
@require_GET
def schedule_view(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    data = reports.schedule(activity, viewer=request.user, request=request)
    return render(
        request, "activities/report_schedule.html", {"activity": activity, "schedule": data}
    )
