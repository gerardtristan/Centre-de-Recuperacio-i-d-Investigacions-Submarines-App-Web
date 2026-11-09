"""Afegir i corregir el registre mínim de llicència des de la fitxa (T-M01-23; RN-M01-29, P19).

El permís (P19 sencer i P4) es comprova abans que el mètode i, de nou, al servei
(`apps/members/licences.py`), que també comprova el conflicte d'interès: amagar un enllaç no és
cap control. Sense permís, o si el registre no és d'aquest soci, sempre «no trobat».
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core.models import Person
from apps.core.permissions import permission_required, request_permissions
from apps.members import licences
from apps.members.models import LicenceRecord, Member
from apps.members.services import OwnMemberChange


def _member(request, pk):
    if not licences.can_manage(request.user, request_permissions(request)):
        raise Http404  # RN-RP-21: també P4
    return get_object_or_404(Member.objects.select_related("person"), pk=pk)


def _to_detail(member):
    response = redirect("administration:member_detail", member.pk)
    response.status_code = 303
    return response


def _handle(request, member, form, title, save):
    own = member.person_id == request.user.person_id
    if request.method == "POST":
        try:
            if own:
                licences.authorize(member, request.user, request=request)
            if form.is_valid():
                if save(form):
                    messages.success(request, _("Llicència desada. Queda al registre d'activitat."))
                else:
                    messages.info(request, _("No hi havia cap canvi per desar."))
                return _to_detail(member)
        except OwnMemberChange as error:
            messages.error(request, error.args[0])
            return _to_detail(member)
        except ValidationError as error:
            form.add_error(None, error)
    context = {
        "member": member,
        "person": member.person,
        "form": form,
        "title": title,
        "own": own,
        "anonymised": member.person.status != Person.Status.ACTIVE,
    }
    return render(request, "members/licence_form.html", context)


def _data(form):
    return {
        "licence_type": form.cleaned_data["licence_type"],
        "issued_on": form.cleaned_data["issued_on"],
        "expires_on": form.cleaned_data["expires_on"],
    }


@never_cache
@permission_required(licences.MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def licence_add_view(request, pk):
    member = _member(request, pk)
    form = licences.LicenceRecordForm(request.POST if request.method == "POST" else None)

    def save(form):
        return licences.add_record(member, by=request.user, request=request, **_data(form))

    return _handle(request, member, form, _("Afegeix una llicència"), save)


@never_cache
@permission_required(licences.MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def licence_edit_view(request, pk, record_pk):
    member = _member(request, pk)
    record = get_object_or_404(LicenceRecord, pk=record_pk, member=member)  # per objecte
    form = licences.LicenceRecordForm(
        request.POST if request.method == "POST" else None, record=record
    )

    def save(form):
        return licences.correct_record(record, by=request.user, request=request, **_data(form))

    return _handle(request, member, form, _("Corregeix la llicència"), save)
