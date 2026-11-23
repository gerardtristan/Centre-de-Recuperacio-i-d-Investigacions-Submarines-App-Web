"""Inscripció d'un soci (o d'una persona amb compte personal) des de la seva àrea (T-M02-11;
M02-8; CA-M02-06, 12, 13, 28 i 29).

- Àrea personal: sessió obligatòria (el middleware) i la persona és sempre la del compte; cap
  identificador de persona a la URL. El servei (`enrolment.enrol`, canal `account`) torna a
  comprovar que el compte és el personal d'aquesta persona.
- Abans d'inscriure's, la persona veu el preu que li toca i els requisits: un requisit que bloqueja
  no deixa enviar res; un avís s'enregistra a la inscripció perquè el revisi el responsable.
- Amb càrrec, porta a la pantalla de pagament del 05b; gratuïta, confirmada; plena, a la llista
  d'espera. Les preguntes d'altres mòduls (el material del 03) surten amb `extensions`.
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.members.services import is_member

from .. import enrolment, extensions, public, requirements
from ..models import Activity, Enrolment

S = Enrolment.Status


def _form(activity, person, data=None):
    """Les preguntes de les seccions d'altres mòduls, amb el nom prefixat per la clau."""
    form = forms.Form(data)
    form.sections = []
    for section in extensions.enrolment_sections():
        names = {}
        for name, field in section.fields(activity, person).items():
            key = f"{section.key.replace('.', '_')}__{name}"
            form.fields[key], names[key] = field, name
        if names:
            form.sections.append((section, names))
    return form


def _answers(form) -> dict:
    return {
        section.key: {name: form.cleaned_data[key] for key, name in names.items()}
        for section, names in form.sections
    }


@never_cache
@require_http_methods(["GET", "POST"])
def member_enrol_view(request, pk):
    person = getattr(request.user, "person", None)
    if person is None:
        raise Http404
    try:
        info = public.get_activity(pk)
    except public.NotFound as error:
        raise Http404 from error
    activity = get_object_or_404(Activity, pk=pk)
    live = Enrolment.objects.filter(activity=activity, person=person, status__in=Enrolment.LIVE)
    current = live.select_related("charge").first()
    form = _form(activity, person, request.POST if request.method == "POST" else None)
    if request.method == "POST" and current is None and form.is_valid():
        try:
            with transaction.atomic():
                row = enrolment.enrol(
                    activity, person, channel=Enrolment.Channel.ACCOUNT, actor=request.user,
                    answers=_answers(form), request=request,
                )  # fmt: skip
        except ValidationError as error:
            form.add_error(None, error.messages[0])
        else:
            if row.status == S.PENDING_PAYMENT and row.charge_id:
                messages.success(request, _("Inscripció feta. Ara pots pagar-la."))
                return redirect("payments:charge", row.charge_id)
            messages.success(request, _("Inscripció feta."))
            response = redirect("activities:member_enrol", pk)
            response.status_code = 303
            return response
    member = is_member(person)
    context = {
        "activity": info,
        "current": current,
        "form": form,
        "price": info.price_member if member else info.price_non_member,
        "member": member,
        "check": requirements.check(activity, person),
        "can_enrol": current is None and (member or info.open_to_non_members),
    }
    return render(request, "activities/member_enrol.html", context)
