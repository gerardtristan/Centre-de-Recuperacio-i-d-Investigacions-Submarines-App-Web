"""Administració: sol·licituds de canvi de tipus i de baixa (T-M01-17; P3a i P7; P-M01-B i
P-M01-C; wireframe `admin.html#vista-socis-sollicituds`, pestanyes «Canvis de tipus» i
«Baixes», i el diàleg «Crea una baixa» de la fitxa).

- Consultar: P3a. Resoldre i crear una baixa: P7; el servei ho torna a comprovar en desar
  (RN-RP-10). Sense permís, «no trobat».
- Les altes (P3) no surten aquí: són de la T-M01-14. Ruta confirmada per la 074 (Q-052): el
  President hi resol amb P3a i P7, sense P4.
- Anul·lar el suplement vençut d'un canvi aprovat: P7a o P8 amb edició (RN-M01-76 i 82; Q-057),
  comprovat aquí i al servei.
- «Crea una baixa»: P7 amb edició i P4 (075, RN-M01-83); sense P4, «no trobat» i cap nom.
- Només es mostren el nom, el número, el tipus i el motiu: cap document, adreça ni data de
  naixement. El resum de quotes d'una baixa el veu qui la pot resoldre; la llista de quotes sense
  pagar, només amb P10 (075, RN-M01-83).
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.permissions import has_perm, permission_required, request_permissions, require_perm
from apps.members import fees, member_requests
from apps.members.fee_rules import local_today
from apps.members.models import AnnualFee, Member, MemberRequest
from apps.members.services import OwnMemberChange
from apps.members.views.personal import euros

APPROVE, REJECT, CANCEL_SUPPLEMENT = "approve", "reject", "cancel_supplement"
MEMBERS_LIST = "members.list"  # P4
FEES_VIEW = "members.fees.view"  # P10


class ResolveForm(forms.Form):
    action = forms.ChoiceField(choices=[(APPROVE, APPROVE), (REJECT, REJECT)])
    effective_on = forms.DateField(
        label=gettext_lazy("Data efectiva de la baixa"),
        help_text=gettext_lazy(
            "Si és una data futura, la baixa queda programada i s'aplica aquell dia."
        ),
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    reason = forms.CharField(
        label=gettext_lazy("Motiu"),
        help_text=gettext_lazy("Obligatori per rebutjar. Per validar, opcional."),
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, kind=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.kind = kind
        if kind == MemberRequest.Kind.CHANGE_TYPE:
            self.fields["reason"].help_text = _(
                "Obligatori per rebutjar. Per aprovar el canvi, opcional."
            )

    def clean(self):
        data = super().clean()
        if data.get("action") == REJECT and not (data.get("reason") or "").strip():
            self.add_error("reason", _("Escriu el motiu del rebuig."))
        leave = self.kind == MemberRequest.Kind.LEAVE
        if data.get("action") == APPROVE and leave and not data.get("effective_on"):
            self.add_error("effective_on", _("Escriu la data efectiva."))
        return data


class CancelSupplementForm(forms.Form):
    reason = forms.CharField(
        label=gettext_lazy("Motiu de l'anul·lació"),
        help_text=gettext_lazy("Obligatori."),
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class LeaveCreateForm(forms.Form):
    reason = forms.CharField(
        label=gettext_lazy("Motiu"),
        help_text=gettext_lazy("Obligatori. Per exemple, la referència de l'acta de la junta."),
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


SUPPLEMENT_STATES = {
    "pending": gettext_lazy("Pendent"),
    "overdue": gettext_lazy("Vençut"),
    "paid": gettext_lazy("Pagat"),
    "cancelled": gettext_lazy("Anul·lat"),
}


def _supplement_state(fee) -> str:
    if fee.charge.status in ("paid", "cancelled"):
        return fee.charge.status
    return "overdue" if member_requests.supplement_overdue(fee) else "pending"


def _requests():
    return MemberRequest.objects.filter(kind__in=member_requests.RESOLVABLE).select_related(
        "person", "member__type", "requested_type", "resolved_by", "supplement_fee__charge"
    )


@never_cache
@permission_required(member_requests.VIEW_PERMISSION)
@require_GET
def requests_list_view(request):
    pending = _requests().filter(status=MemberRequest.Status.PENDING).order_by("created_at", "id")
    context = {
        "changes": [r for r in pending if r.kind == MemberRequest.Kind.CHANGE_TYPE],
        "leaves": [r for r in pending if r.kind == MemberRequest.Kind.LEAVE],
    }
    return render(request, "members/requests_list.html", context)


def _resolve(member_request, data, request) -> str:
    """Crida el servei que toca i torna el missatge d'èxit."""
    if data["action"] == REJECT:
        member_requests.reject(
            member_request, by=request.user, reason=data["reason"], request=request
        )
        return _("Sol·licitud resolta.")
    if member_request.kind == MemberRequest.Kind.CHANGE_TYPE:
        member_requests.approve_type_change(
            member_request, by=request.user, reason=data["reason"], request=request
        )
        return _("Canvi aprovat. S'ha creat el suplement.")
    member_requests.approve_leave(
        member_request,
        by=request.user,
        effective_on=data["effective_on"],
        reason=data["reason"],
        request=request,
    )
    if member_requests.is_scheduled(member_request):
        return _("Baixa validada. Queda programada per al %(date)s.") % {
            "date": member_request.effective_on.strftime("%d/%m/%Y")
        }
    return _("Baixa validada i aplicada.")


@never_cache
@permission_required(member_requests.VIEW_PERMISSION)
@require_http_methods(["GET", "POST"])
def request_detail_view(request, pk):
    member_request = get_object_or_404(_requests(), pk=pk)
    perms = request_permissions(request)
    can_resolve = has_perm(
        request.user, member_requests.RESOLVE_PERMISSION, write=True, permissions=perms
    )
    own = member_request.person_id == request.user.person_id
    kind = member_request.kind
    cancelling = request.method == "POST" and request.POST.get("action") == CANCEL_SUPPLEMENT
    form = ResolveForm(
        None if cancelling else (request.POST or None),
        initial={"effective_on": local_today()},
        kind=kind,
    )
    cancel_form = CancelSupplementForm(request.POST if cancelling else None)
    status = 200
    if request.method == "POST":
        # Resoldre: P7 amb edició; anul·lar el suplement: P7a o P8 amb edició. Sense permís,
        # «no trobat».
        if cancelling:
            if not member_requests.can_cancel_supplement(request.user, perms):
                raise Http404
        else:
            require_perm(request, member_requests.RESOLVE_PERMISSION, write=True)
        active = cancel_form if cancelling else form
        if active.is_valid():
            try:
                if cancelling:
                    member_requests.cancel_overdue_supplement(
                        member_request,
                        by=request.user,
                        reason=cancel_form.cleaned_data["reason"],
                        request=request,
                    )
                    message = _("Suplement anul·lat.")
                else:
                    message = _resolve(member_request, form.cleaned_data, request)
            except OwnMemberChange:
                active.add_error(None, _("No pots resoldre una sol·licitud teva."))
                status = 403
            except ValidationError as exc:
                active.add_error(None, exc.messages[0])
            else:
                messages.success(request, message)
                return redirect("administration:member_request_detail", pk=member_request.pk)
    pending = member_request.status == MemberRequest.Status.PENDING
    fee = member_request.supplement_fee
    state = _supplement_state(fee) if fee else ""
    context = {
        "item": member_request,
        "form": form,
        "cancel_form": cancel_form,
        "can_resolve": can_resolve and not own,
        "own": own,
        "pending": pending,
        "scheduled": member_requests.is_scheduled(member_request),
        # C2: el mateix càlcul que crea el càrrec (`fees.supplement_cents`), en euros.
        "supplement_amount": (
            euros(fees.supplement_cents(member_request.member, member_request.requested_type))
            if kind == MemberRequest.Kind.CHANGE_TYPE and pending
            else ""
        ),
        "supplement": fee,
        "supplement_state": SUPPLEMENT_STATES.get(state, ""),
        "supplement_fee_amount": euros(fee.charge.amount_cents) if fee else "",
        # CA-M01-75 i 83: només vençut, amb P7a o P8 d'edició i no el propi; el servei ho torna
        # a comprovar.
        "can_cancel_supplement": state == "overdue"
        and not own
        and member_requests.can_cancel_supplement(request.user, perms),
    }
    if kind == MemberRequest.Kind.LEAVE and pending and can_resolve and not own:
        # C3: resum de conseqüències (RN-M01-20). Depèn de la data que es triï: es mostra la
        # regla i, només amb P10 (075, CA-M01-85), les quotes sense pagar amb el venciment.
        member = member_request.member
        context["show_fees"] = has_perm(request.user, FEES_VIEW, permissions=perms)
        if context["show_fees"]:
            context["unpaid_fees"] = [
                (fee, euros(fee.charge.amount_cents))
                for fee in AnnualFee.objects.filter(
                    member=member, charge__status__in=member_requests.UNPAID_CHARGE
                )
                .select_related("charge")
                .order_by("due_on", "pk")
            ]
        context["pending_change"] = member.requests.filter(
            kind=MemberRequest.Kind.CHANGE_TYPE, status=MemberRequest.Status.PENDING
        ).exists()
    return render(request, "members/request_detail.html", context, status=status)


@never_cache
@permission_required(member_requests.RESOLVE_PERMISSION, write=True)
@permission_required(MEMBERS_LIST)
@require_http_methods(["GET", "POST"])
def leave_create_view(request, pk):
    """Baixa per decisió de la junta (pas 1 de P-M01-C). La data es fixa en validar-la."""
    member = get_object_or_404(Member.objects.select_related("person"), pk=pk)
    form = LeaveCreateForm(request.POST or None)
    status = 200
    if request.method == "POST" and form.is_valid():
        try:
            created = member_requests.request_leave(
                member, by=request.user, reason=form.cleaned_data["reason"], request=request
            )
        except OwnMemberChange as exc:
            form.add_error(None, str(exc))
            status = 403
        except ValidationError as exc:
            form.add_error(None, exc.messages[0])
        else:
            messages.success(
                request,
                _("Sol·licitud de baixa creada. Valida-la i fixa'n la data efectiva."),
            )
            return redirect("administration:member_request_detail", pk=created.pk)
    context = {"member": member, "form": form}
    return render(request, "members/leave_create.html", context, status=status)
