"""Àrea del soci: demanar el canvi a ple dret i la baixa (T-M01-17; P14; P-M01-B i P-M01-C, pas
1; wireframes `socis.html#canvi-tipus` i `socis.html#baixa`), i demanar i retirar el pas de ple
dret a simpatitzant (T-M01-42; 073; RN-M01-93; CA-M01-68, 71 i 106).

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
from django.views.decorators.http import require_http_methods, require_POST

from .. import fees, member_requests
from .. import settings as member_settings
from ..fee_rules import SUPPORTER
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


class WithdrawForm(forms.Form):
    confirm = forms.BooleanField(
        label=gettext_lazy("Confirmo que vull retirar la sol·licitud."),
        error_messages={"required": gettext_lazy("Cal que marquis la confirmació.")},
    )


def _pending(member, kind):
    return member.requests.filter(kind=kind, status=MemberRequest.Status.PENDING).first()


def _change_type_page(request, member, *, error="", withdraw_form=None):
    """«Canvi de tipus»: el soci de ple dret hi veu el pas a simpatitzant (073, CA-M01-68); la
    resta, el canvi a ple dret."""
    if member.type.code == member_requests.FULL:
        context = {
            "member": member,
            "error": error,
            "pending": member_requests.downgrades(member)
            .filter(status=MemberRequest.Status.PENDING)
            .first(),
            "accepted": member_requests.accepted_downgrade(member),
            "problem": member_requests.downgrade_problem(member),
            "withdraw_form": withdraw_form or WithdrawForm(),
        }
        return render(request, "members/personal_downgrade.html", context)
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
        "supplement_days": member_settings.supplement_due_days(),  # VC-53 (RN-M01-106)
    }
    return render(request, "members/personal_change_type.html", context)


@never_cache
@require_http_methods(["GET", "POST"])
def change_type_view(request):
    member = _own_member_or_404(request)
    error = ""
    if request.method == "POST":
        # El sentit del canvi el diu el formulari i el servei el torna a comprovar amb el tipus
        # real del soci: una petició manipulada no canvia res (CA-M01-71).
        downgrade = request.POST.get("target") == SUPPORTER
        ask = (
            member_requests.request_downgrade if downgrade else member_requests.request_type_change
        )
        try:
            ask(member, by=request.user, request=request)
        except member_requests.RequestNotAllowed as exc:
            error = exc.messages[0]
        else:
            if downgrade:
                messages.success(request, _("Sol·licitud de pas a simpatitzant enviada."))
                return redirect("members:change_type")
            messages.success(request, _("Sol·licitud de canvi a ple dret enviada."))
            return redirect("members:profile")
    return _change_type_page(request, member, error=error)


@never_cache
@require_POST
def change_type_withdraw_view(request):
    """El soci retira el seu pas a simpatitzant pendent, amb confirmació (RN-M01-93, punt 4;
    CA-M01-106). Cap identificador a la ruta: la sol·licitud surt del soci de la sessió."""
    member = _own_member_or_404(request)
    form = WithdrawForm(request.POST)
    error = ""
    if form.is_valid():
        try:
            member_requests.withdraw_downgrade(member, by=request.user, request=request)
        except member_requests.RequestNotAllowed as exc:
            error = exc.messages[0]
        else:
            messages.success(request, _("Sol·licitud retirada. Si vols, en pots fer una altra."))
            return redirect("members:change_type")
    return _change_type_page(request, member, error=error, withdraw_form=form)


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
