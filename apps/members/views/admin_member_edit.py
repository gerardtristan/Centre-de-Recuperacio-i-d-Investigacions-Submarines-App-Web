"""Editar les dades d'un soci (P5) i corregir la data d'alta (P6) des de la fitxa (T-M01-15b).

El permís es comprova abans que el mètode i, de nou, al servei (`apps/members/member_edit.py`),
que també comprova els camps i el conflicte d'interès: amagar un enllaç no és cap control.
Sense permís, sempre «no trobat».
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core.models import Person
from apps.core.permissions import permission_required, request_permissions, require_perm
from apps.members import member_edit, roster
from apps.members.models import Member
from apps.members.services import OwnMemberChange


def _to_detail(member):
    response = redirect("administration:member_detail", member.pk)
    response.status_code = 303
    return response


def _member(request, pk):
    require_perm(request, roster.LIST)  # RN-RP-21
    return get_object_or_404(Member.objects.select_related("person"), pk=pk)


def _handle(request, member, form, template, context, save):
    """GET: el formulari. POST: el servei ho torna a comprovar tot; el conflicte d'interès es
    registra encara que el formulari no sigui vàlid."""
    own = member.person_id == request.user.person_id
    anonymised = member.person.status != Person.Status.ACTIVE
    if request.method == "POST":
        try:
            if own:
                member_edit.authorize(member, request.user, context["permission"], request=request)
            if form.is_valid():
                changed = save(form)
                if changed:
                    messages.success(request, _("Canvis desats. Queden al registre d'activitat."))
                else:
                    messages.info(request, _("No hi havia cap canvi per desar."))
                return _to_detail(member)
        except OwnMemberChange as error:
            messages.error(request, error.args[0])
            return _to_detail(member)
        except ValidationError as error:
            form.add_error(None, error)
    context.update({"member": member, "person": member.person, "form": form, "own": own})
    context["anonymised"] = anonymised
    return render(request, template, context)


@never_cache
@permission_required(member_edit.EDIT)
@require_http_methods(["GET", "POST"])
def member_edit_view(request, pk):
    member = _member(request, pk)
    fields = member_edit.editable_fields(request.user, request_permissions(request))
    form = member_edit.MemberDataForm(
        request.POST if request.method == "POST" else None, person=member.person, fields=fields
    )

    def save(form):
        return member_edit.edit_member_data(
            member, by=request.user, fields=form.person_fields(), request=request
        )

    context = {"permission": member_edit.EDIT}
    return _handle(request, member, form, "members/member_edit.html", context, save)


@never_cache
@permission_required(member_edit.EDIT_JOIN_DATE)
@require_http_methods(["GET", "POST"])
def member_join_date_view(request, pk):
    member = _member(request, pk)
    if not member_edit.can_correct_join_date(request.user, request_permissions(request)):
        raise Http404  # P6 demana P4 sencer: «dades mínimes» no veu la data d'alta
    form = member_edit.JoinDateForm(
        request.POST if request.method == "POST" else None, member=member
    )

    def save(form):
        return member_edit.correct_join_date(
            member,
            by=request.user,
            joined_on=form.cleaned_data["joined_on"],
            approximate=form.cleaned_data["approximate"],
            request=request,
        )

    context = {"permission": member_edit.EDIT_JOIN_DATE}
    return _handle(request, member, form, "members/member_join_date.html", context, save)
