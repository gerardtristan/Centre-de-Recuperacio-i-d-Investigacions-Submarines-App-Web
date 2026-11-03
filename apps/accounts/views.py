"""Entrades de l'àrea de socis i de l'administració (spec 00, HU-04, HU-05, HU-07 i HU-09),
enllaços del correu del compte personal (C4, C5), seguretat del compte personal (HU-05) i
entrada amb una credencial temporal d'un restabliment per un altre administrador (HU-08).

L'entrada d'administració no té cap enllaç ni cap ruta de recuperació per correu (CA-07.4).
"""

import logging

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_not_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core import audit
from apps.core.permissions import has_perm, permission_required

from . import email_links, tokens, totp
from .forms import CodeForm, DisableTotpForm, LoginForm, NewPasswordForm
from .models import Account
from .security import (
    AREA_ADMIN,
    AREA_PERSONAL,
    WRONG_CODE,
    WRONG_PASSWORD,
    check_credentials,
    client_ip,
    confirm_password_and_code,
    record_failure,
    serialized_attempts,
)
from .sessions import (
    clear_pending,
    complete_login,
    mark_second_factor,
    pending_account,
    pending_next,
    safe_next,
    second_factor_done,
    start_pending,
)

logger = logging.getLogger("cris.security")

NAMESPACE = {AREA_PERSONAL: "accounts", AREA_ADMIN: "administration"}
HOME = {AREA_PERSONAL: "core:home", AREA_ADMIN: "administration:home"}
BAD_CODE = _("El codi no és correcte.")


def _url(area, name):
    return reverse(f"{NAMESPACE[area]}:{name}")


def _finish(request, account, area):
    if account.must_change_password:
        # CA-08.1: amb una credencial temporal, primer s'ha de canviar; fins llavors, cap sessió.
        mark_second_factor(request)
        return redirect(_url(area, "change_temporary_credential"))
    next_url = pending_next(request)
    complete_login(request, account, area)
    return redirect(safe_next(request, next_url) or reverse(HOME[area]))


def _code_failed(request, area, account):
    """Un codi incorrecte compta com un intent fallit del compte (V-01): sense aquest límit,
    un codi de sis xifres es podria endevinar provant-los tots."""
    record_failure(request, area, account, "bad_code")
    if account.is_locked(timezone.now()):
        clear_pending(request)
        return redirect(_url(area, "login"))
    return None


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def login_view(request, area):
    form = LoginForm(area, request.POST or None)
    error = None
    next_url = request.POST.get("next") or request.GET.get("next")
    if request.method == "POST" and form.is_valid():
        result = check_credentials(
            request, area, form.cleaned_data["login"], form.cleaned_data["password"]
        )
        account = result.account
        if account is not None:
            if area == AREA_ADMIN or account.has_totp:
                start_pending(request, account, area, next_url)
                if area == AREA_ADMIN and not account.has_totp:
                    # CA-07.1: sense TOTP, només en pot donar d'alta un.
                    return redirect(_url(area, "totp_enrol"))
                return redirect(_url(area, "login_totp"))
            complete_login(request, account, area)
            return redirect(safe_next(request, next_url) or reverse(HOME[area]))
        error = result.error
    return render(
        request,
        "accounts/login.html",
        {"form": form, "error": error, "area": area, "next": safe_next(request, next_url)},
    )


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def login_totp_view(request, area):
    account = pending_account(request, area)
    if account is None:
        clear_pending(request)
        return redirect(_url(area, "login"))
    if not account.has_totp:
        return redirect(_url(area, "totp_enrol" if area == AREA_ADMIN else "login"))

    form = CodeForm(request.POST or None)
    error = None
    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"]
        # D'un en un per origen i per compte, com la contrasenya (C3): el bloqueig es torna a
        # mirar després d'esperar el torn.
        with serialized_attempts(request, account):
            if account.is_locked(timezone.now()):
                outcome = "locked"
            elif totp.verify_code(account.totp_device, code):
                outcome = "ok"
            # Codis de recuperació: només els comptes d'administrador en tenen (V-01).
            elif area == AREA_ADMIN and totp.use_recovery_code(account, code):
                outcome = "recovery"
            else:
                record_failure(request, area, account, "bad_code")
                outcome = "locked" if account.is_locked(timezone.now()) else "bad"
        if outcome == "ok":
            return _finish(request, account, area)
        if outcome == "recovery":
            logger.warning("recovery_code_used account=%s ip=%s", account.pk, client_ip(request))
            audit.record(audit.Action.RECOVERY_CODE_USED, actor=account, request=request)
            return redirect(_url(area, "totp_enrol"))
        if outcome == "locked":
            clear_pending(request)
            return redirect(_url(area, "login"))
        error = BAD_CODE
    return render(request, "accounts/login_totp.html", {"form": form, "error": error, "area": area})


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def totp_enrol_view(request):
    area = AREA_ADMIN
    account = pending_account(request, area)
    if account is None:
        clear_pending(request)
        return redirect(_url(area, "login"))
    if account.has_totp:
        return redirect(_url(area, "login_totp"))

    device = getattr(account, "totp_device", None) or totp.start_enrolment(account)
    form = CodeForm(request.POST or None)
    error = None
    if request.method == "POST" and form.is_valid():
        codes = totp.confirm_enrolment(device, form.cleaned_data["code"])
        if codes is not None:
            logger.info("totp_enrolled account=%s ip=%s", account.pk, client_ip(request))
            # CA-14.4: diu què ha passat, sense el secret ni els codis.
            audit.record(audit.Action.TOTP_ENROLLED, actor=account, request=request)
            next_url = pending_next(request)
            if account.must_change_password:
                # Restabliment de la contrasenya i del TOTP: després dels codis, la contrasenya.
                mark_second_factor(request)
                continue_url = _url(area, "change_temporary_credential")
            else:
                complete_login(request, account, area)
                continue_url = safe_next(request, next_url) or reverse(HOME[area])
            # Els codis es mostren aquesta única vegada; a la base de dades només hi ha
            # les empremtes (CA-09.1).
            return render(
                request,
                "accounts/recovery_codes.html",
                {"codes": codes, "continue_url": continue_url},
            )
        if (response := _code_failed(request, area, account)) is not None:
            return response
        error = BAD_CODE

    secret = totp.secret_of(device)
    return render(
        request,
        "accounts/totp_enrol.html",
        {
            "form": form,
            "error": error,
            "qr_svg": totp.qr_svg(totp.provisioning_uri(device)),
            "secret_groups": [secret[i : i + 4] for i in range(0, len(secret), 4)],
        },
    )


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def temporary_password_change_view(request):
    """CA-08.1: qui entra amb una credencial temporal l'ha de canviar abans de tenir sessió.
    Només després de la contrasenya i del segon factor; la nova ha de ser diferent."""
    area = AREA_ADMIN
    account = pending_account(request, area)
    if (
        account is None
        or not second_factor_done(request)
        or not account.must_change_password
        or account.temporary_password_expired(timezone.now())
    ):
        clear_pending(request)
        return redirect(_url(area, "login"))
    form = NewPasswordForm(account, request.POST or None)
    if request.method == "POST" and form.is_valid():
        if account.check_password(form.cleaned_data["new_password1"]):
            form.add_error("new_password1", _("Ha de ser diferent de la contrasenya temporal."))
        else:
            next_url = pending_next(request)
            with transaction.atomic():
                audit.record(
                    audit.Action.PASSWORD_CHANGED,
                    actor=account,
                    target=account,
                    details={"after_reset": True},
                    request=request,
                )
                form.save(commit=False)
                account.password_temporary_until = None
                account.save(update_fields=["password", "password_temporary_until", "updated_at"])
            complete_login(request, account, area)
            return redirect(safe_next(request, next_url) or reverse(HOME[area]))
    return render(request, "accounts/temporary_password_change.html", {"form": form})


@login_not_required
@require_POST
def logout_view(request, area):
    if request.user.is_authenticated:
        logger.info("logout account=%s area=%s", request.user.pk, area)
        audit.record(
            audit.Action.LOGOUT, actor=request.user, details={"area": area}, request=request
        )
    logout(request)  # buida la sessió sencera, també l'estat pendent
    return redirect(_url(area, "login"))


def _no_referrer(response):
    # Les pàgines dels enllaços d'un sol ús no passen cap adreça a una altra pàgina.
    response["Referrer-Policy"] = "no-referrer"
    return response


def _stash_link(request, session_key, token, url_name):
    """Primera petició d'un enllaç del correu: no canvia res. Desa el testimoni a la sessió i
    redirigeix a l'adreça sense testimoni (vegeu `email_links`)."""
    request.session[session_key] = token
    return _no_referrer(redirect(reverse(url_name)))


@login_not_required
@never_cache
@require_GET
def verify_email_link_view(request, token):
    return _stash_link(request, email_links.VERIFY_SESSION_KEY, token, "accounts:verify_email")


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def verify_email_view(request):
    """CA-04.2: el compte personal s'activa quan es confirma el correu. Amb un POST, perquè
    obrir l'enllaç no ho faci sol."""
    token = request.session.get(email_links.VERIFY_SESSION_KEY, "")
    state = "invalid"
    if request.method == "POST":
        if email_links.confirm_email(token, request=request) is not None:
            state = "done"
        request.session.pop(email_links.VERIFY_SESSION_KEY, None)
    elif tokens.account_for_token(token, tokens.VERIFY_EMAIL) is not None:
        state = "ready"
    if state == "invalid":
        request.session.pop(email_links.VERIFY_SESSION_KEY, None)
    return _no_referrer(render(request, "accounts/verify_email.html", {"state": state}))


@login_not_required
@never_cache
@require_GET
def password_reset_link_view(request, token):
    return _stash_link(request, email_links.RESET_SESSION_KEY, token, "accounts:password_reset")


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def password_reset_view(request):
    """CA-04.4: un enllaç caducat o ja utilitzat no permet canviar la contrasenya."""
    token = request.session.get(email_links.RESET_SESSION_KEY, "")
    data = request.POST if request.method == "POST" else None
    result = email_links.reset_password(token, data, request=request)
    if result.account is None or result.done:
        request.session.pop(email_links.RESET_SESSION_KEY, None)
    state = "done" if result.done else "ready" if result.account else "invalid"
    return _no_referrer(
        render(request, "accounts/password_reset.html", {"state": state, "form": result.form})
    )


@never_cache
@require_GET
def security_view(request):
    """Seguretat del compte personal: estat del doble factor (HU-05)."""
    return render(
        request,
        "accounts/security.html",
        {"has_totp": request.user.has_totp, "disable_form": DisableTotpForm()},
    )


@never_cache
@require_http_methods(["GET", "POST"])
def personal_totp_enrol_view(request):
    """CA-05.1: el compte personal activa el TOTP confirmant un codi vàlid. Sense codis de
    recuperació (V-01). Un codi mal escrit aquí no compta per al bloqueig: la persona ja és
    dins i té el secret a la pantalla, no hi ha res a endevinar."""
    account = request.user
    if account.has_totp:
        return redirect("accounts:security")
    device = getattr(account, "totp_device", None) or totp.start_enrolment(account)
    form = CodeForm(request.POST or None)
    error = None
    if request.method == "POST" and form.is_valid():
        if totp.confirm_enrolment(device, form.cleaned_data["code"], recovery_codes=False) == []:
            logger.info("totp_enrolled account=%s ip=%s", account.pk, client_ip(request))
            audit.record(
                audit.Action.TOTP_ENROLLED,
                actor=account,
                details={"area": AREA_PERSONAL},
                request=request,
            )
            messages.success(request, _("Doble factor activat."))
            return redirect("accounts:security")
        error = BAD_CODE
    secret = totp.secret_of(device)
    return render(
        request,
        "accounts/totp_enrol.html",
        {
            "area": AREA_PERSONAL,
            "form": form,
            "error": error,
            "qr_svg": totp.qr_svg(totp.provisioning_uri(device)),
            "secret_groups": [secret[i : i + 4] for i in range(0, len(secret), 4)],
        },
    )


@never_cache
@require_POST
def personal_totp_disable_view(request):
    """CA-05.2: contrasenya i codi vàlid; els errors compten per al bloqueig (V-01) i el
    canvi queda al registre, sense cap secret."""
    account = request.user
    if not account.has_totp:
        return redirect("accounts:security")
    form = DisableTotpForm(request.POST)
    error = None
    if form.is_valid():
        error = confirm_password_and_code(
            request,
            account,
            AREA_PERSONAL,
            form.cleaned_data["password"],
            form.cleaned_data["code"],
        )
        if error is None:
            with transaction.atomic():
                audit.record(
                    audit.Action.TOTP_DISABLED,
                    actor=account,
                    details={"area": AREA_PERSONAL},
                    request=request,
                )
                totp.disable(account)
            logger.info("totp_disabled account=%s ip=%s", account.pk, client_ip(request))
            messages.success(request, _("Doble factor desactivat."))
            return redirect("accounts:security")
        # L'error al costat del camp que falla (com RN-M01-57); el bloqueig, a tot el formulari.
        field = {WRONG_PASSWORD: "password", WRONG_CODE: "code"}.get(error)
        form.add_error(field, error)
    return render(request, "accounts/security.html", {"has_totp": True, "disable_form": form})


@never_cache
@require_GET
@permission_required("core.accounts.reset_credentials")
def admin_accounts_view(request):
    """Llista mínima dels comptes d'administrador per al restabliment (HU-08), només amb M4.
    Sense permís, «no trobat». Només el que cal per decidir: nom d'usuari, estat, si té el
    doble factor i si té una contrasenya temporal pendent. La T-RP-02 l'ampliarà."""
    accounts = (
        Account.objects.filter(kind=Account.Kind.ADMIN)
        .select_related("totp_device")
        .order_by("login")
    )
    return render(request, "accounts/admin_accounts.html", {"accounts": accounts})


@never_cache
@require_GET
def admin_home(request):
    # L'enllaç només surt amb el permís; la vista el torna a comprovar igualment.
    can_reset = has_perm(request.user, "core.accounts.reset_credentials")
    return render(request, "accounts/admin_home.html", {"can_reset": can_reset})
