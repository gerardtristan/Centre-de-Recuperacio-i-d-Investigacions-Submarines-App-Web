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
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts import personal_reset
from apps.accounts.forms import PersonalTotpResetForm
from apps.accounts.security import AREA_ADMIN, WRONG_CODE, confirm_code
from apps.core.models import Person
from apps.core.permissions import permission_required, request_permissions, require_perm
from apps.members import admissions, birth_date, cards, member_edit, roster
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
            reason=form.cleaned_data["reason"],
            request=request,
        )

    context = {"permission": member_edit.EDIT_JOIN_DATE}
    return _handle(request, member, form, "members/member_join_date.html", context, save)


@never_cache
@permission_required(admissions.INVITE_PERMISSION)
@require_POST
def member_invite_view(request, pk):
    """079 (RN-M01-87, especificació punt 7): tornar a enviar la invitació del compte personal.
    M2 amb edició i P4; el servei ho torna a comprovar. Invalida la invitació anterior."""
    member = _member(request, pk)
    if admissions.resend_invitation(member, by=request.user, request=request):
        messages.success(
            request,
            _("Invitació enviada. L'enllaç anterior, si n'hi havia, ja no serveix."),
        )
    else:
        messages.error(
            request,
            _(
                "No s'ha enviat cap invitació: la persona ja té compte personal, no té correu "
                "propi o és menor de 14 anys."
            ),
        )
    return _to_detail(member)


@never_cache
@permission_required(personal_reset.PERMISSION, write=True)
@require_http_methods(["GET", "POST"])
def member_totp_reset_view(request, pk):
    """Decisió 081, punt 24 (P-52; RN-M01-104): la secretaria restableix en persona el doble
    factor del compte personal del soci (M2 amb edició i P4). Comprovació presencial de la
    identitat amb el document, motiu i un codi TOTP nou de qui ho fa a la mateixa petició. El
    servei ho torna a comprovar tot."""
    member = _member(request, pk)
    account = personal_reset.personal_account_with_totp(member.person)
    own = member.person_id == request.user.person_id
    form = PersonalTotpResetForm(request.POST or None)
    if request.method == "POST" and account is not None and not own and form.is_valid():
        error = confirm_code(request, request.user, AREA_ADMIN, form.cleaned_data["code"])
        if error is not None:
            form.add_error("code" if error == WRONG_CODE else None, error)
        else:
            try:
                queued = personal_reset.reset_personal_totp(
                    account,
                    by=request.user,
                    document=form.cleaned_data["document"],
                    identity_checked=form.cleaned_data["identity_checked"],
                    note=form.cleaned_data["note"],
                    request=request,
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(
                    request,
                    _("Doble factor restablert. El soci ja pot entrar amb la contrasenya.")
                    if queued
                    else _(
                        "Doble factor restablert. No s'ha pogut enviar l'avís al soci: "
                        "explica-li-ho en persona."
                    ),
                )
                return _to_detail(member)
    return render(
        request,
        "members/member_totp_reset.html",
        {"member": member, "person": member.person, "account": account, "own": own, "form": form},
    )


@never_cache
@permission_required(member_edit.EDIT, write=True)
@require_POST
def member_birth_date_check_view(request, pk):
    """Decisió 081, punt 16 (RN-M01-99): la secretaria marca la data de naixement com a
    comprovada amb el document (P5 amb C1, i P4). No condiciona l'exempció ni cap altra cosa que
    la data ja fa; no es desa cap còpia del document."""
    member = _member(request, pk)
    try:
        changed = birth_date.mark_checked(
            member, by=request.user, confirmed=bool(request.POST.get("confirmo")), request=request
        )
    except OwnMemberChange as error:
        messages.error(request, error.args[0])
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        if changed:
            messages.success(request, _("Data de naixement marcada com a comprovada."))
        else:
            messages.info(request, _("La data de naixement ja constava com a comprovada."))
    return _to_detail(member)


@never_cache
@permission_required(cards.REVOKE_PERMISSION, write=True)
@require_POST
def member_card_revoke_view(request, pk):
    """079 (A-21, RN-M01-92; P21): la secretaria revoca el carnet d'un soci amb motiu. P21 amb
    edició i P4; el servei ho torna a comprovar, registra el conflicte d'interès i exigeix el
    motiu. No n'emet cap de nou: el soci el demana des de la seva pàgina del carnet."""
    member = _member(request, pk)
    try:
        revoked = cards.revoke_by_admin(
            member, by=request.user, reason=request.POST.get("motiu", ""), request=request
        )
    except OwnMemberChange as error:
        messages.error(request, error.args[0])
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        if revoked is None:
            messages.info(request, _("Aquest soci no tenia cap carnet per revocar."))
        else:
            messages.success(
                request,
                _(
                    "Carnet revocat: el seu codi QR ja no és vàlid. El soci en pot demanar un "
                    "de nou des de la seva pàgina del carnet."
                ),
            )
    return _to_detail(member)
