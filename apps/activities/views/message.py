"""Missatge de l'organitzador als inscrits (T-M02-21c; RN-M02-19; AC15). El servei
(`notifications.send_message`) torna a comprovar AC15 per a l'activitat; sense, «no trobat».
S'hi arriba des de la fitxa de l'activitat."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .. import notifications, permissions
from ..models import Activity, Enrolment
from . import see_other


@never_cache
@require_http_methods(["GET", "POST"])
def message_view(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    permissions.require(request.user, permissions.MESSAGE, activity, request=request)
    error = None
    if request.method == "POST":
        try:
            sent = notifications.send_message(
                activity, by=request.user, subject=request.POST.get("assumpte", ""),
                body=request.POST.get("text", ""), request=request,
            )  # fmt: skip
        except ValidationError as exc:
            error = " ".join(exc.messages)
        else:
            messages.success(
                request,
                ngettext(
                    "Missatge a la cua per a %(count)s persona.",
                    "Missatge a la cua per a %(count)s persones.",
                    sent,
                )
                % {"count": sent},
            )
            return see_other("administration:activity_detail", activity.pk)
    live = Enrolment.objects.filter(activity=activity, status__in=Enrolment.LIVE)
    context = {
        "activity": activity,
        "recipients": live.aggregate(n=Count("pk"))["n"],
        "error": error,
        "data": request.POST,
        "max_subject": notifications.MAX_SUBJECT,
        "max_body": notifications.MAX_BODY,
        "help": _("Només dades de l'activitat. Sense dades de salut ni de cap altra persona."),
    }
    return render(request, "activities/activity_message.html", context)
