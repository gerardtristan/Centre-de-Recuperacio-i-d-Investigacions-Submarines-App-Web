"""«Les meves activitats» i el calendari d'una inscripció (T-M02-22b; C16; RN-M02-25 i 45).

Àrea personal (sessió obligatòria): només les inscripcions de la persona del compte. El calendari
`.ics` és d'una inscripció seva (si no, «no trobat») i no porta mai cap persona (`ics.build`).
El certificat (T-M02-22c) és la mateixa pàgina per imprimir que la de l'administració (T-M02-19b),
només d'una inscripció seva amb el certificat emès (si no, «no trobat»).
Els blocs d'altres mòduls (el material del 03) surten amb `extensions.detail_sections`.
«El meu progrés» (T-M02-17c; HU-M02-14) és d'una inscripció seva a un curs amb pràctiques:
només el resultat i l'observació de les seves pràctiques (`assessment.progress`).
"""

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .. import assessment, attendance, certificates, extensions, ics
from ..models import Activity, Enrolment, Session


def _person(request):
    person = getattr(request.user, "person", None)
    if person is None:
        raise Http404
    return person


@never_cache
@require_GET
def my_activities_view(request):
    person = _person(request)
    rows = []
    enrolments = (
        Enrolment.objects.filter(person=person)
        .select_related("activity__place", "charge")
        .order_by("-activity__starts_on", "-pk")
    )
    for row in enrolments:
        sections = [
            render_to_string(section.template_name, {**data, "activity": row.activity}, request)
            for section, data in extensions.detail_sections(
                row.activity, place=extensions.PLACE_PERSONAL, viewer=request.user, person=person
            )
        ]
        rows.append(
            {
                "enrolment": row,
                "live": row.status in Enrolment.LIVE,
                "certificate": certificates.certificate(row),
                "progress": _has_practices(row),
                "sections": sections,
            }
        )
    context = {"rows": rows, "attended": attendance.attendance_for(person)}
    return render(request, "activities/my_activities.html", context)


def _has_practices(row) -> bool:
    return (
        row.activity.kind == Activity.Kind.COURSE
        and row.status in Enrolment.LIVE
        and Session.objects.filter(
            activity_id=row.activity_id, is_practice=True, cancelled=False
        ).exists()
    )


@never_cache
@require_GET
def enrolment_progress_view(request, pk):
    """«El meu progrés» d'una inscripció seva (si no, «no trobat»); cap dada d'altres alumnes."""
    row = get_object_or_404(
        Enrolment.objects.select_related("activity"), pk=pk, person=_person(request)
    )
    if not _has_practices(row):
        raise Http404
    context = {"activity": row.activity, "rows": assessment.progress(row)}
    return render(request, "activities/my_progress.html", context)


@never_cache
@require_GET
def enrolment_calendar_view(request, pk):
    row = get_object_or_404(
        Enrolment.objects.select_related("activity__place"),
        pk=pk, person=_person(request), status__in=Enrolment.LIVE,
    )  # fmt: skip
    activity = row.activity
    body = ics.build(activity, activity.sessions.select_related("place"))
    response = HttpResponse(body, content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="activitat-{activity.pk}.ics"'
    return response


@never_cache
@require_GET
def enrolment_certificate_view(request, pk):
    row = get_object_or_404(
        Enrolment.objects.select_related("person", "activity"), pk=pk, person=_person(request)
    )
    data = certificates.certificate(row)
    if data is None:
        raise Http404
    context = {"certificate": data, "activity": row.activity, "personal": True}
    return render(request, "activities/certificate.html", context)
