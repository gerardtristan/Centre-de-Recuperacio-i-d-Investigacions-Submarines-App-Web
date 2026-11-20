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
from django.contrib.auth import logout
from django.core.exceptions import ValidationError
from django.db import OperationalError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.accounts.forms import OneTimeCodeInput
from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN, WRONG_CODE, confirm_code
from apps.accounts.sessions import delete_session_hint

from .. import roles
from ..models import AccountRole, Role
from ..permissions import has_perm, permission_required

MANAGE = "core.accounts.manage"
ASSIGN, REMOVE = "assign", "remove"


class ConfirmForm(forms.Form):
    """Nota, codi TOTP nou i casella de revisió: el que demana qualsevol canvi d'aquesta pantalla
    (RN-RP-06)."""

    note = forms.CharField(
        label=gettext_lazy("Nota"),
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=gettext_lazy(
            "Obligatòria. Queda al registre d'activitat i va al correu d'avís: no hi escriguis "
            "dades personals de ningú."
        ),
        error_messages={"required": gettext_lazy("Escriu la nota del canvi.")},
    )
    code = forms.CharField(
        label=gettext_lazy("El teu codi TOTP"),
        max_length=24,
        help_text=gettext_lazy(
            "Un codi nou de la teva aplicació d'autenticació, per confirmar que ets tu."
        ),
        widget=OneTimeCodeInput(attrs={"autocomplete": "one-time-code", "autocapitalize": "none"}),
    )
    reviewed = forms.BooleanField(
        label=gettext_lazy("He revisat el resum i el compte afectat"),
        error_messages={"required": gettext_lazy("Confirma que has revisat el resum.")},
    )


class RoleChangeForm(ConfirmForm):
    action = forms.ChoiceField(
        choices=[(ASSIGN, ASSIGN), (REMOVE, REMOVE)], widget=forms.HiddenInput
    )
    role = forms.ChoiceField(choices=Role.Code.choices, widget=forms.HiddenInput)


CODE_USED = gettext_lazy(
    "El codi TOTP ja s'ha fet servir: si ho tornes a provar, escriu-ne un de nou."
)
DATABASE_CONFLICT = gettext_lazy(
    "Un altre canvi s'estava desant alhora: torna-ho a provar d'aquí a uns segons."
)


def _change(data, active_codes):
    """(assignar?, rol, ja fet?) si l'acció i el rol tenen sentit; si no, None. «Ja fet» vol dir
    que el compte ja té (o ja no té) el rol: no hi ha res a desar."""
    action, code = data.get("action"), data.get("role")
    role = Role.objects.filter(code=code, is_management=True).first()
    if role is None or action not in (ASSIGN, REMOVE):
        return None
    return action == ASSIGN, role, (action == ASSIGN) == (code in active_codes)


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
    if posted:
        form = RoleChangeForm(request.POST)
        change = _change(request.POST, active_codes)
    else:  # de l'adreça, només l'acció i el rol: mai la nota ni el codi
        initial = {key: request.GET.get(key) for key in ("action", "role")}
        form = RoleChangeForm(initial=initial)
        change = _change(initial, active_codes)
    already = bool(change and change[2])
    change = None if already else change
    if change and change[0] and account.status == Account.Status.DISABLED:
        change = None  # un compte desactivat no rep rols nous (també ho diu el servei)
    blocked = bool(
        change
        and not change[0]
        and change[1].code == Role.Code.ADMINISTRATOR
        and roles.leaves_no_operational_admin(account)
    )
    # Les condicions es miren abans de demanar el codi: un canvi que no es pot fer no el gasta.
    if posted and already:
        form.add_error(None, roles.ALREADY_DONE)
    elif posted and change is None:
        form.add_error(None, _("Aquest canvi no es pot fer."))
    elif posted and not blocked and form.is_valid():
        error = confirm_code(request, request.user, AREA_ADMIN, form.cleaned_data["code"])
        if error is not None:
            form.add_error("code" if error == WRONG_CODE else None, error)
        else:
            assign, role, _done = change
            note = form.cleaned_data["note"]
            try:
                if assign:
                    saved = roles.assign_role(account, role.code, by=request.user, note=note)
                else:
                    saved = roles.remove_role(account, role.code, by=request.user, note=note)
            except roles.AlreadyDone:
                form.add_error(None, roles.ALREADY_DONE)
            except ValidationError as exc:
                form.add_error(None, [*exc.messages, CODE_USED])
            except OperationalError:
                form.add_error(None, [DATABASE_CONFLICT, CODE_USED])
            else:
                if assign and saved is None:  # un altre administrador s'hi ha avançat
                    form.add_error(None, roles.ALREADY_DONE)
                else:
                    messages.success(
                        request,
                        _("Canvi desat. S'ha avisat per correu els comptes que ho han de saber."),
                    )
                    if has_perm(request.user, MANAGE):
                        return redirect("administration:account_roles", pk=account.pk)
                    return redirect("administration:home")  # s'ha tret a si mateix el rol
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
            "already": already,
            "blocked_message": roles.NO_OPERATIONAL_ADMIN,
            "shortage": roles.admin_shortage_warning(),
            "form": form,
        },
    )


# La pàgina d'entrada és pública: el missatge no diu res del compte (revisió de #216, punt 4).
LEFT_ADMIN = gettext_lazy("Has sortit de l'administració.")
LOGOUT_TAG = "sortida"  # l'entrada només mostra els missatges amb aquesta etiqueta


@never_cache
@permission_required(MANAGE)
@require_http_methods(["GET", "POST"])
def account_deactivate_view(request, pk):
    """T-RP-02d: desactivar un compte d'administrador, també el propi (RN-RP-20; CA-RP-06 i 16).
    El mateix patró: resum (GET), i POST amb nota, casella i codi TOTP nou, que només es demana
    si el canvi es pot fer. El servei ho torna a comprovar tot dins la transacció."""
    account = get_object_or_404(Account, pk=pk, kind=Account.Kind.ADMIN)
    own = account.pk == request.user.pk
    already = account.status == Account.Status.DISABLED
    blocked = not already and roles.leaves_no_operational_admin(account)
    form = ConfirmForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and already:
        form.add_error(None, roles.ALREADY_DONE)
    elif request.method == "POST" and not blocked and form.is_valid():
        error = confirm_code(request, request.user, AREA_ADMIN, form.cleaned_data["code"])
        if error is not None:
            form.add_error("code" if error == WRONG_CODE else None, error)
        else:
            try:
                roles.deactivate_admin_account(
                    account, by=request.user, note=form.cleaned_data["note"]
                )
            except roles.AlreadyDone:
                already = True  # un altre administrador s'hi ha avançat: cap formulari
                form.add_error(None, [roles.ALREADY_DONE, CODE_USED])
            except ValidationError as exc:
                form.add_error(None, [*exc.messages, CODE_USED])
            except OperationalError:  # la transacció ja s'ha desfet sencera
                form.add_error(None, [DATABASE_CONFLICT, CODE_USED])
            else:
                if own:  # RN-RP-20: també la petició en curs surt de l'administració
                    list(messages.get_messages(request))  # cap missatge d'una altra pantalla
                    logout(request)
                    messages.info(request, LEFT_ADMIN, extra_tags=LOGOUT_TAG)
                    response = redirect("administration:login")
                    delete_session_hint(response)  # cap «La sessió ha caducat» (081)
                    return response
                messages.success(
                    request,
                    _("Compte desactivat. S'ha avisat per correu els comptes que ho han de saber."),
                )
                return redirect("administration:account_roles", pk=account.pk)
    return render(
        request,
        "core/account_deactivate.html",
        {
            "account": account,
            "own": own,
            "already": already,
            "blocked": blocked,
            "blocked_message": roles.NO_OPERATIONAL_ADMIN,
            "form": form,
        },
    )
