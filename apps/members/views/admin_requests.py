"""Administració: sol·licituds de canvi de tipus i de baixa (T-M01-17; P3a i P7; P-M01-B i
P-M01-C; wireframe `admin.html#vista-socis-sollicituds`, pestanyes «Canvis de tipus» i
«Baixes», i el diàleg «Crea una baixa» de la fitxa).

- Consultar: P3a. Resoldre i crear una baixa: P7; el servei ho torna a comprovar en desar
  (RN-RP-10). Sense permís, «no trobat».
- Les altes (P3) no surten aquí: són de la T-M01-14. La ruta definitiva és [A validar, T-M01-17]
  (nota de P-M01-B): es resol des de la vista de sol·licituds perquè el President té P7 sense P4.
- Només es mostren el nom, el número, el tipus i el motiu: cap document, adreça ni data de
  naixement.
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.permissions import has_perm, permission_required, request_permissions, require_perm
from apps.members import member_requests
from apps.members.fee_rules import local_today
from apps.members.models import Member, MemberRequest
from apps.members.services import OwnMemberChange

APPROVE, REJECT = "approve", "reject"


class ResolveForm(forms.Form):
    action = forms.ChoiceField(choices=[(APPROVE, APPROVE), (REJECT, REJECT)])
    effective_on = forms.DateField(
        label=gettext_lazy("Data efectiva de la baixa"),
        help_text=gettext_lazy("Avui o abans. Encara no es poden programar baixes futures."),
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    reason = forms.CharField(
        label=gettext_lazy("Motiu"),
        help_text=gettext_lazy("Obligatori per rebutjar. Per validar, opcional."),
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean(self):
        data = super().clean()
        if data.get("action") == REJECT and not (data.get("reason") or "").strip():
            self.add_error("reason", _("Escriu el motiu del rebuig."))
        if data.get("action") == APPROVE and not data.get("effective_on"):
            self.add_error("effective_on", _("Escriu la data efectiva."))
        return data


class LeaveCreateForm(forms.Form):
    reason = forms.CharField(
        label=gettext_lazy("Motiu"),
        help_text=gettext_lazy("Obligatori. Per exemple, la referència de l'acta de la junta."),
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


def _requests():
    return MemberRequest.objects.filter(kind__in=member_requests.RESOLVABLE).select_related(
        "person", "member__type", "requested_type", "resolved_by"
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
    form = ResolveForm(request.POST or None, initial={"effective_on": local_today()})
    status = 200
    if request.method == "POST":
        require_perm(request, member_requests.RESOLVE_PERMISSION, write=True)
        if form.is_valid():
            data = form.cleaned_data
            try:
                if data["action"] == REJECT:
                    member_requests.reject(
                        member_request, by=request.user, reason=data["reason"], request=request
                    )
                else:
                    member_requests.approve_leave(
                        member_request,
                        by=request.user,
                        effective_on=data["effective_on"],
                        reason=data["reason"],
                        request=request,
                    )
            except OwnMemberChange:
                form.add_error(None, _("No pots resoldre una sol·licitud teva."))
                status = 403
            except ValidationError as exc:
                form.add_error(None, exc.messages[0])
            else:
                messages.success(request, _("Sol·licitud resolta."))
                return redirect("administration:member_request_detail", pk=member_request.pk)
    context = {
        "item": member_request,
        "form": form,
        "can_resolve": can_resolve and not own,
        "own": own,
        "pending": member_request.status == MemberRequest.Status.PENDING,
    }
    return render(request, "members/request_detail.html", context, status=status)


@never_cache
@permission_required(member_requests.RESOLVE_PERMISSION, write=True)
@require_http_methods(["GET", "POST"])
def leave_create_view(request, pk):
    """Baixa per decisió de la junta (pas 1 de P-M01-C). La data es fixa en validar-la."""
    member = get_object_or_404(Member.objects.select_related("person"), pk=pk)
    form = LeaveCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            created = member_requests.request_leave(
                member, by=request.user, reason=form.cleaned_data["reason"], request=request
            )
        except ValidationError as exc:
            form.add_error(None, exc.messages[0])
        else:
            messages.success(
                request,
                _("Sol·licitud de baixa creada. Valida-la i fixa'n la data efectiva."),
            )
            return redirect("administration:member_request_detail", pk=created.pk)
    return render(request, "members/leave_create.html", {"member": member, "form": form})
