"""Inscripció d'un convidat des del web (T-M02-14 i T-M02-34; RN-M02-35; CA-M02-10, 11 i 37).

- **Ruta pública declarada** (`login_not_required`, RN-40), amb CSRF i el límit de peticions per
  origen. Només per a una activitat pública (`public.get_activity`); si no, «no trobat».
- Les regles són de `guests.enrol_guest`: oberta a no socis (si no, com fer-se soci), oberta i dins
  de termini, dades mínimes, privacitat i «Soc major d'edat» amb els textos vigents. A producció,
  mentre la junta no publiqui el text `adult_declaration` (P-458), el servei rebutja totes les
  inscripcions i la pàgina ho diu.
- La resposta és la mateixa tant si el correu ja era d'algú com si no; l'enllaç per pagar arriba
  al correu (enllaç de convidat de la 00). POST, 303 i GET.
"""

from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.accounts import limits
from apps.accounts.security import client_ip
from apps.core import consents

from .. import guests, public
from ..forms import GuestEnrolmentForm
from ..models import Activity

SENT_KEY = "activities_guest_sent"


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def guest_enrol_view(request, pk):
    try:
        info = public.get_activity(pk)
    except public.NotFound as error:
        raise Http404 from error
    texts = {
        "privacy": consents.current_text(guests.PRIVACY),
        "adult": None if info.min_age else consents.current_text(guests.ADULT),
    }
    context = {"activity": info, "texts": texts}
    if request.method == "GET" and request.session.get(SENT_KEY) == pk:
        context["sent_to"] = request.session.pop(SENT_KEY + "_to", "")
        del request.session[SENT_KEY]
        return render(request, "activities/guest_enrol.html", context)
    form = GuestEnrolmentForm(request.POST or None, min_age=info.min_age)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                # shortcut: comparteix el límit per origen del «Fer-se soci» (P-450), com el 06;
                # quan el nucli tingui una finalitat pròpia, fer-la servir aquí.
                if limits.start_join(client_ip(request)) is None:
                    raise ValidationError(
                        _("S'han enviat massa inscripcions seguides. Torna-ho a provar més tard.")
                    )
                activity = Activity.objects.get(pk=pk)
                guests.enrol_guest(activity, form.cleaned_data, request=request)
        except ValidationError as error:
            form.add_error(None, error.messages[0])
        else:
            request.session[SENT_KEY] = pk
            request.session[SENT_KEY + "_to"] = form.cleaned_data["contact_email"]
            response = redirect("activities:guest_enrol", pk)
            response.status_code = 303
            return response
    context["form"] = form
    # P-458: sense el text «Soc major d'edat» publicat (si no hi ha edat mínima), no s'inscriu ningú
    texts_ready = texts["privacy"] is not None and (info.min_age or texts["adult"] is not None)
    context["available"] = info.open_to_non_members and info.registration_open and texts_ready
    return render(request, "activities/guest_enrol.html", context)
