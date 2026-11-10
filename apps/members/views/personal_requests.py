"""Àrea del soci: demanar el canvi a ple dret i la baixa (T-M01-17; P14; P-M01-B i P-M01-C, pas
1; wireframes `socis.html#canvi-tipus` i `socis.html#baixa`).

El soci surt sempre de la sessió (`request.user.person`): cap ruta no porta cap identificador.
Sense soci, «no trobat» (P14: «propi si és soci»). Les regles i el permís es tornen a comprovar
al servei (`member_requests`), no només aquí.
"""

from django import forms
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .. import fees, member_requests
from ..models import MemberRequest, MembershipType
from .personal import _own_member_or_404, euros


class LeaveForm(forms.Form):
    reason = forms.CharField(
        label=gettext_lazy("Motiu de la baixa"),
        help_text=gettext_lazy("Obligatori. El llegirà la secretaria."),
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    confirm = forms.BooleanField(
        label=gettext_lazy("Confirmo que vull demanar la baixa com a soci."),
        error_messages={"required": gettext_lazy("Cal que marquis la confirmació.")},
    )


def _pending(member, kind):
    return member.requests.filter(kind=kind, status=MemberRequest.Status.PENDING).first()


@never_cache
@require_http_methods(["GET", "POST"])
def change_type_view(request):
    member = _own_member_or_404(request)
    error = ""
    if request.method == "POST":
        try:
            member_requests.request_type_change(member, by=request.user, request=request)
        except member_requests.RequestNotAllowed as exc:
            error = exc.messages[0]
        else:
            messages.success(request, _("Sol·licitud de canvi a ple dret enviada."))
            return redirect("members:profile")
    problem = member_requests.type_change_problem(member)
    target = MembershipType.objects.filter(code=member_requests.FULL, active=True).first()
    context = {
        "member": member,
        "pending": _pending(member, MemberRequest.Kind.CHANGE_TYPE),
        "problem": problem,
        "error": error,
        # C2: el mateix càlcul que crea el càrrec en aprovar-lo (Q-049).
        "supplement_amount": euros(fees.supplement_cents(member, target))
        if target and not problem
        else "",
    }
    return render(request, "members/personal_change_type.html", context)


@never_cache
@require_http_methods(["GET", "POST"])
def leave_view(request):
    member = _own_member_or_404(request)
    form = LeaveForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            member_requests.request_leave(
                member, by=request.user, reason=form.cleaned_data["reason"], request=request
            )
        except member_requests.RequestNotAllowed as exc:
            form.add_error(None, exc.messages[0])
        else:
            messages.success(request, _("Sol·licitud de baixa enviada."))
            return redirect("members:profile")
    context = {
        "member": member,
        "form": form,
        # Pendent o programada (RN-M01-74): no se'n pot demanar cap altra.
        "pending": member_requests.open_leaves(member).first(),
    }
    return render(request, "members/personal_leave.html", context)
