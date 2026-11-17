"""Administració: assignar i retirar rols d'un compte d'administrador (T-RP-02; 059 i 060;
RN-RP-07, 08, 09, 11, 13 i 14; CA-RP-03, 06, 11 i 14). Sense wireframe propi: el patró de les
sol·licituds RGPD i el resum de l'Avisador (`design-system.md`, §6.7 i T-DX-19).

- Només amb M3 (`core.accounts.manage`, protegit i exclusiu de l'administrador): la resta de
  rols, també el President, «no trobat», abans de mirar res.
- Un GET amb l'acció i el rol només mostra el resum: què canvia, el compte afectat i els avisos.
  No desa res.
- Desar és un POST amb CSRF, la nota, la casella de revisió i un codi TOTP nou de qui ho fa
  (RN-RP-06; el mateix control que el restabliment, RN-M01-60). Els serveis de `roles` tornen a
  comprovar el permís, l'administrador operatiu i el registre dins la mateixa transacció.
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN, WRONG_CODE, confirm_code

from .. import roles
from ..models import AccountRole, Role
from ..permissions import has_perm, permission_required

MANAGE = "core.accounts.manage"
ASSIGN, REMOVE = "assign", "remove"


class RoleChangeForm(forms.Form):
    action = forms.ChoiceField(
        choices=[(ASSIGN, ASSIGN), (REMOVE, REMOVE)], widget=forms.HiddenInput
    )
    role = forms.ChoiceField(choices=Role.Code.choices, widget=forms.HiddenInput)
    note = forms.CharField(
        label=gettext_lazy("Nota"),
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=gettext_lazy("Obligatòria. Queda al registre d'activitat i va al correu d'avís."),
        error_messages={"required": gettext_lazy("Escriu la nota del canvi.")},
    )
    code = forms.CharField(
        label=gettext_lazy("El teu codi TOTP"),
        max_length=24,
        help_text=gettext_lazy(
            "Un codi nou de la teva aplicació d'autenticació, per confirmar que ets tu."
        ),
        widget=forms.TextInput(attrs={"autocomplete": "one-time-code", "autocapitalize": "none"}),
    )
    reviewed = forms.BooleanField(
        label=gettext_lazy("He revisat el resum i el compte afectat"),
        error_messages={"required": gettext_lazy("Confirma que has revisat el resum.")},
    )


def _change(data, active_codes):
    """(assignar?, rol) si l'acció i el rol tenen sentit per a aquest compte; si no, None."""
    if not data:
        return None
    action, code = data.get("action"), data.get("role")
    role = Role.objects.filter(code=code, is_management=True).first()
    if role is None or action not in (ASSIGN, REMOVE):
        return None
    if (action == ASSIGN) == (code in active_codes):
        return None
    return action == ASSIGN, role


@never_cache
@permission_required(MANAGE)
@require_http_methods(["GET", "POST"])
def account_roles_view(request, pk):
    account = get_object_or_404(Account, pk=pk, kind=Account.Kind.ADMIN)
    active = list(
        AccountRole.objects.filter(admin_account=account, removed_at__isnull=True)
        .select_related("role", "assigned_by")
        .order_by("role__pk")
    )
    active_codes = {item.role.code for item in active}
    posted = request.method == "POST"
    data = request.POST if posted else request.GET
    change = _change(data, active_codes)
    form = RoleChangeForm(data) if posted else RoleChangeForm(initial=data.dict())
    if posted and change is None:  # p. ex., un altre administrador ja ha fet el canvi
        form.add_error(None, _("Aquest canvi ja no es pot fer amb els rols actuals del compte."))
    elif posted and form.is_valid():
        error = confirm_code(request, request.user, AREA_ADMIN, form.cleaned_data["code"])
        if error is not None:
            form.add_error("code" if error == WRONG_CODE else None, error)
        else:
            assign, role = change
            service = roles.assign_role if assign else roles.remove_role
            try:
                service(account, role.code, by=request.user, note=form.cleaned_data["note"])
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(
                    request,
                    _("Canvi desat. S'ha avisat per correu els comptes que ho han de saber."),
                )
                if has_perm(request.user, MANAGE):
                    return redirect("administration:account_roles", pk=account.pk)
                return redirect("administration:home")  # s'ha tret a si mateix el rol
    blocked = bool(
        change
        and not change[0]
        and change[1].code == Role.Code.ADMINISTRATOR
        and roles.leaves_no_operational_admin(account)
    )
    return render(
        request,
        "core/account_roles.html",
        {
            "account": account,
            "active": active,
            "assignable": Role.objects.filter(is_management=True)
            .exclude(code__in=active_codes)
            .order_by("pk"),
            "change": change,
            "warnings": roles.change_warnings(account, change[1].code, assign=change[0])
            if change
            else [],
            "blocked": blocked,
            "blocked_message": roles.NO_OPERATIONAL_ADMIN,
            "shortage": roles.admin_shortage_warning(),
            "form": form,
        },
    )
