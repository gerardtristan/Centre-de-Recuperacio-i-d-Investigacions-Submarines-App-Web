"""Entrades de l'àrea de socis i de l'administració (spec 00, HU-04, HU-05, HU-07 i HU-09).

L'entrada d'administració no té cap enllaç ni cap ruta de recuperació per correu (CA-07.4).
"""

import logging

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_not_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import totp
from .forms import CodeForm, LoginForm
from .security import AREA_ADMIN, AREA_PERSONAL, check_credentials, client_ip, record_failure
from .sessions import (
    clear_pending,
    complete_login,
    pending_account,
    pending_next,
    safe_next,
    start_pending,
)

logger = logging.getLogger("cris.security")

NAMESPACE = {AREA_PERSONAL: "accounts", AREA_ADMIN: "administration"}
HOME = {AREA_PERSONAL: "core:home", AREA_ADMIN: "administration:home"}
BAD_CODE = "El codi no és correcte."


def _url(area, name):
    return reverse(f"{NAMESPACE[area]}:{name}")


def _finish(request, account, area):
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
        if totp.verify_code(account.totp_device, code):
            return _finish(request, account, area)
        # Codis de recuperació: només els comptes d'administrador en tenen (V-01).
        if area == AREA_ADMIN and totp.use_recovery_code(account, code):
            logger.warning("recovery_code_used account=%s ip=%s", account.pk, client_ip(request))
            return redirect(_url(area, "totp_enrol"))
        if (response := _code_failed(request, area, account)) is not None:
            return response
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
            next_url = pending_next(request)
            complete_login(request, account, area)
            # Els codis es mostren aquesta única vegada; a la base de dades només hi ha
            # les empremtes (CA-09.1).
            return render(
                request,
                "accounts/recovery_codes.html",
                {
                    "codes": codes,
                    "continue_url": safe_next(request, next_url) or reverse(HOME[area]),
                },
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
@require_POST
def logout_view(request, area):
    if request.user.is_authenticated:
        logger.info("logout account=%s area=%s", request.user.pk, area)
    logout(request)  # buida la sessió sencera, també l'estat pendent
    return redirect(_url(area, "login"))


@never_cache
@require_GET
def admin_home(request):
    return render(request, "accounts/admin_home.html")
