"""Full d'avaluació d'una pràctica (T-M02-17b; P-M02-F pas 1; HU-M02-12; AC10a; RN-M02-17).

- Només qui fa classe a la sessió (AC10a, «les seves sessions»): els serveis d'`assessment` ho
  tornen a comprovar i deixen al registre l'intent fora de l'abast; ningú no s'avalua a si mateix.
- Per a cada alumne confirmat: assolit, no assolit o necessita reforç, amb una observació curta.
  **Sense dades de salut:** ho diu l'ajuda del camp.
- S'hi arriba des de la llista de la sessió («Passar llista»), si la sessió és pràctica.
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .. import assessment
from ..models import Enrolment, PracticeAssessment, Session
from ..permissions import REINFORCEMENT_PROPOSE, can
from . import see_other

NOTES_HELP = gettext_lazy("Curta i pedagògica. Sense dades de salut.")


@never_cache
@require_http_methods(["GET", "POST"])
def sheet_view(request, pk, session_pk):
    session = get_object_or_404(
        Session.objects.select_related("activity"), pk=session_pk, activity_id=pk
    )
    # El servei comprova AC10a per objecte (i deixa l'intent al registre) abans que res.
    rows = assessment.sheet(session, viewer=request.user, request=request)
    if request.method == "POST":
        enrolment = get_object_or_404(Enrolment, pk=request.POST.get("inscripcio"), activity_id=pk)
        try:
            assessment.assess(
                session, enrolment, result=request.POST.get("resultat", ""),
                notes=request.POST.get("observacio", ""), by=request.user, request=request,
            )  # fmt: skip
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
        else:
            messages.success(request, _("Avaluació desada."))
        return see_other("administration:assessment_sheet", pk, session.pk)
    context = {
        "session": session,
        "activity": session.activity,
        "rows": rows,
        "results": PracticeAssessment.Result.choices,
        "can_assess": assessment.can_assess_now(session),
        "notes_help": NOTES_HELP,
        "max_notes": assessment.MAX_NOTES,
        # T-M02-18b: proposar reforç (AC10b), per a qui fa classe al curs.
        "can_propose": can(request.user, REINFORCEMENT_PROPOSE, session.activity),
    }
    return render(request, "activities/assessment_sheet.html", context)
