"""Resultat del curs i certificat (T-M02-19b; P-M02-F passos 5 i 6; RN-M02-16 i 31; CA-M02-19;
AC12 i AC13).

- **Resultats del curs:** qui fa classe a l'activitat (AC12, «les seves sessions») posa apte o no
  apte (amb motiu); qui té AC13 (responsable de cursos i sortides, administrador, President) els
  veu i emet el certificat d'un apte. Els serveis de `certificates` ho tornen a comprovar; ningú no
  es posa apte a si mateix. Sense cap dels dos permisos, «no trobat» (i l'intent fora de l'abast,
  al registre).
- **Certificat:** la pàgina que s'imprimeix o es desa com a PDF des del navegador (decisió 079),
  només amb AC13. El certificat a «Les meves activitats» de l'alumne és de la T-M02-22.
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from .. import certificates, permissions
from ..models import Activity, CertificationLevel, CourseOutcome, Enrolment, TrainingCatalogueEntry
from ..permissions import CERTIFICATE, OUTCOME, can
from . import see_other

PAGE = "administration:course_outcomes"


def _course(pk, user, request):
    activity = get_object_or_404(
        Activity.objects.select_related("catalogue_entry"), pk=pk, kind=Activity.Kind.COURSE
    )
    if not can(user, CERTIFICATE):
        permissions.require(user, OUTCOME, activity, request=request)
    return activity


def _needs_level(activity) -> bool:
    entry = activity.catalogue_entry
    return (
        entry.kind == TrainingCatalogueEntry.Kind.COURSE
        and certificates.default_level(activity) is None
    )


def _post(request, activity):
    enrolment = get_object_or_404(Enrolment, pk=request.POST.get("inscripcio"), activity=activity)
    try:
        if "emet" in request.POST:
            level = None
            if request.POST.get("nivell"):
                level = get_object_or_404(
                    CertificationLevel, pk=request.POST["nivell"], active=True
                )
            certificates.issue(enrolment, by=request.user, level=level, request=request)
            messages.success(request, _("Certificat emès."))
        else:
            certificates.record_outcome(
                enrolment, result=request.POST.get("resultat", ""), by=request.user,
                reason=request.POST.get("motiu", ""), request=request,
            )  # fmt: skip
            messages.success(request, _("Resultat desat."))
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))


@never_cache
@require_http_methods(["GET", "POST"])
def outcomes_view(request, pk):
    activity = _course(pk, request.user, request)
    if request.method == "POST":
        _post(request, activity)
        return see_other(PAGE, activity.pk)
    outcomes = {
        o.enrolment_id: o for o in CourseOutcome.objects.filter(enrolment__activity=activity)
    }
    students = (
        Enrolment.objects.filter(activity=activity, status=Enrolment.Status.CONFIRMED)
        .select_related("person")
        .order_by("person__last_name", "person__first_name", "id")
    )
    context = {
        "activity": activity,
        "rows": [(row, outcomes.get(row.pk)) for row in students],
        "can_decide": can(request.user, OUTCOME, activity)
        and activity.status in certificates.DECIDABLE,
        "can_issue": can(request.user, CERTIFICATE),
        "needs_level": _needs_level(activity),
        "levels": CertificationLevel.objects.filter(active=True).order_by("name"),
        "results": CourseOutcome.Result.choices,
    }
    return render(request, "activities/course_outcomes.html", context)


@never_cache
@require_GET
def certificate_view(request, pk, enrolment_pk):
    permissions.require(request.user, CERTIFICATE, request=request)
    enrolment = get_object_or_404(
        Enrolment.objects.select_related("person", "activity"), pk=enrolment_pk, activity_id=pk
    )
    data = certificates.certificate(enrolment)
    if data is None:
        raise Http404
    return render(
        request,
        "activities/certificate.html",
        {"certificate": data, "activity": enrolment.activity},
    )
