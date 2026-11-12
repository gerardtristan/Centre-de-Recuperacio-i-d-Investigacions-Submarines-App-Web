"""Entrades de l'àrea de socis i de l'administració (spec 00, HU-04, HU-05, HU-07 i HU-09),
enllaços del correu del compte personal (C4, C5), seguretat del compte personal (HU-05) i
entrada amb una credencial temporal d'un restabliment per un altre administrador (HU-08).

L'entrada d'administració no té cap enllaç ni cap ruta de recuperació per correu (CA-07.4).
"""

import logging

from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core import audit, roles
from apps.core.permissions import permission_required

from . import email_links, emergency, invitations, tokens, totp
from .forms import (
    CodeForm,
    DisableTotpForm,
    LoginForm,
    NewPasswordForm,
    RecoveryRequestForm,
    ResetCredentialsForm,
)
from .models import Account
from .security import (
    AREA_ADMIN,
    AREA_PERSONAL,
    TEMPORARY_PASSWORD_VALIDITY,
    WRONG_CODE,
    WRONG_PASSWORD,
    check_credentials,
    client_ip,
    confirm_code,
    confirm_password_and_code,
    record_failure,
    serialized_attempts,
)
from .sessions import (
    clear_pending,
    complete_login,
    delete_session_hint,
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
    can_resend = False
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
        if result.pending is not None and area == AREA_PERSONAL:
            # RN-M01-59: el reenviament només després de la contrasenya correcta.
            email_links.remember_pending(request, result.pending)
            can_resend = True
    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "error": error,
            "area": area,
            "next": safe_next(request, next_url),
            "can_resend": can_resend,
        },
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
    response = redirect(_url(area, "login"))
    delete_session_hint(response)  # qui surt no ha de veure «La sessió ha caducat» (081)
    return response


def _no_referrer(response):
    # La redirecció de l'enllaç del correu ve d'una adreça amb el testimoni: no es passa enlloc.
    response["Referrer-Policy"] = "no-referrer"
    return response


def _same_origin_referrer(response):
    # Pàgina neta del formulari (sense testimoni a l'adreça). Amb «no-referrer», els navegadors
    # envien «Origin: null» al POST i la comprovació CSRF el rebutja.
    response["Referrer-Policy"] = "same-origin"
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
    return _same_origin_referrer(render(request, "accounts/verify_email.html", {"state": state}))


@login_not_required
@never_cache
@require_GET
def change_email_link_view(request, token):
    return _stash_link(request, email_links.CHANGE_SESSION_KEY, token, "accounts:change_email")


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def change_email_view(request):
    """RN-M01-79, CA-M01-78: el correu d'entrada canvia quan es confirma l'enllaç, amb un POST.
    Sense sessió, com la verificació: el testimoni lliga el compte i l'adreça nova. Un enllaç
    caducat, ja fet servir o d'una adreça que ja és d'un altre compte dona el mateix missatge.
    En confirmar-lo, les sessions del compte deixen de valer i només es conserva la de la
    petició, si és del mateix compte (RN-M01-81, CA-M01-82)."""
    token = request.session.get(email_links.CHANGE_SESSION_KEY, "")
    new_email = ""
    if request.method == "POST":
        # Abans de confirmar: després, l'època nova ja no reconeixeria la sessió de la petició.
        session_pk = request.user.pk if request.user.is_authenticated else None
        account = email_links.confirm_email_change(token, request=request)
        if account is not None and session_pk == account.pk:
            update_session_auth_hash(request, account)
        state = "done" if account is not None else "invalid"
    else:
        account, new_email = email_links.email_change_for_token(token)
        state = "ready" if account is not None else "invalid"
    if state != "ready":
        request.session.pop(email_links.CHANGE_SESSION_KEY, None)
    return _same_origin_referrer(
        render(request, "accounts/change_email.html", {"state": state, "new_email": new_email})
    )


def _reset_sent_message():
    hours = email_links.hours(tokens.RESET_PASSWORD)
    return ngettext(
        "Si hi ha un compte actiu amb aquesta adreça, t'hi hem enviat un enllaç per triar una "
        "contrasenya nova. L'enllaç caduca d'aquí a %(hours)d hora i només serveix una vegada. "
        "Si no el reps, mira la carpeta de correu brossa o torna-ho a provar més tard.",
        "Si hi ha un compte actiu amb aquesta adreça, t'hi hem enviat un enllaç per triar una "
        "contrasenya nova. L'enllaç caduca d'aquí a %(hours)d hores i només serveix una vegada. "
        "Si no el reps, mira la carpeta de correu brossa o torna-ho a provar més tard.",
        hours,
    ) % {"hours": hours}


def _verification_resent_message():
    hours = email_links.hours(tokens.VERIFY_EMAIL)
    return ngettext(
        "Si el compte encara està pendent de confirmar, t'hem tornat a enviar l'enllaç de "
        "confirmació al correu amb què el vas crear. Caduca d'aquí a %(hours)d hora i només "
        "serveix una vegada. Si no el reps, mira la carpeta de correu brossa o torna-ho a provar "
        "més tard.",
        "Si el compte encara està pendent de confirmar, t'hem tornat a enviar l'enllaç de "
        "confirmació al correu amb què el vas crear. Caduca d'aquí a %(hours)d hores i només "
        "serveix una vegada. Si no el reps, mira la carpeta de correu brossa o torna-ho a provar "
        "més tard.",
        hours,
    ) % {"hours": hours}


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def password_reset_request_view(request):
    """CA-04.3 i CA-M01-48: la mateixa resposta per a qualsevol adreça (compte actiu,
    pendent, desactivat, d'administrador, inexistent o limitat), amb els límits de RN-M01-58."""
    form = RecoveryRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email_links.request_password_reset(request, form.cleaned_data["email"])
        return render(
            request, "accounts/password_reset_request.html", {"sent": _reset_sent_message()}
        )
    return render(request, "accounts/password_reset_request.html", {"form": form})


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def resend_verification_view(request):
    """RN-M01-59: només amb l'estat que deixa la contrasenya correcta d'un compte pendent;
    mentre dura, amb els límits de RN-M01-58 (066). L'adreça no ve mai del navegador.
    El POST redirigeix (303) a aquesta mateixa pàgina en GET (T-M01-38): recarregar-la o
    tornar-hi enrere no torna a enviar res. El GET no envia mai res."""
    if request.method == "POST":
        email_links.resend_verification(request)
        response = redirect("accounts:resend_verification")
        response.status_code = 303
        return response
    sent = email_links.resend_was_requested(request)
    if sent:
        message = _verification_resent_message()
    else:
        message = _("Per demanar un enllaç nou, torna a escriure el correu i la contrasenya.")
    return render(
        request,
        "accounts/resend_verification.html",
        {"message": message, "sent": bool(sent), "expired": not sent},
    )


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
    return _same_origin_referrer(
        render(request, "accounts/password_reset.html", {"state": state, "form": result.form})
    )


@login_not_required
@never_cache
@require_GET
def invitation_link_view(request, token):
    return _stash_link(request, invitations.SESSION_KEY, token, "accounts:invitation")


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def invitation_view(request):
    """079 (RN-M01-87, CA-M01-90): crear el compte personal amb la invitació de l'alta aprovada.
    Només amb un POST. Un enllaç desconegut, caducat, ja fet servir, d'una persona que ja té
    compte o amb un correu que ja és d'un altre compte dona el mateix text. No obre cap sessió."""
    token = request.session.get(invitations.SESSION_KEY, "")
    data = request.POST if request.method == "POST" else None
    result = invitations.accept(token, data, request=request)
    state = "done" if result.done else "ready" if result.form else "invalid"
    if state != "ready":
        request.session.pop(invitations.SESSION_KEY, None)
    return _same_origin_referrer(
        render(request, "accounts/invitation.html", {"state": state, "form": result.form})
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
    return render(
        request,
        "accounts/admin_accounts.html",
        {
            "accounts": accounts,
            "emergency_ready": emergency.warning_for(request.user),
            "emergency_minimum": emergency.MINIMUM,
        },
    )


NO_NOTIFICATION_ADDRESS = _(
    "Aquest compte no té correu de notificació. El restabliment es pot fer, però no se li "
    "podrà enviar l'avís."
)
NOTICE_NO_ADDRESS = _(
    "Restabliment completat. No s'ha pogut enviar l'avís perquè el compte no té correu de "
    "notificació. Avisa la persona afectada per una altra via."
)
NOTICE_QUEUED = _(
    "Restabliment completat. L'avís s'ha posat a la cua d'enviament cap al correu de "
    "notificació del compte; el registre d'enviaments en dirà el resultat."
)
NOTICE_NOT_SENT = _("Restabliment completat. No s'ha enviat l'avís (%(reason)s).")


def _notice_message(notice):
    if notice.queued:
        return NOTICE_QUEUED
    if notice.reason == str(roles.NO_ADDRESS):
        return NOTICE_NO_ADDRESS
    return NOTICE_NOT_SENT % {"reason": notice.reason}


@never_cache
@require_http_methods(["GET", "POST"])
@permission_required("core.accounts.reset_credentials")
def reset_credentials_view(request, pk):
    """HU-08 i RN-M01-60: M4, codi TOTP nou de qui ho fa a la mateixa petició (també amb
    l'excepció de RN-RP-18) i motiu obligatori. La credencial temporal es mostra aquesta
    sola vegada; no va al registre ni a cap correu (RN-17). El canal de lliurament és Q-03,
    obert: la pantalla no en proposa cap."""
    target = Account.objects.filter(pk=pk, kind=Account.Kind.ADMIN).first()
    if target is None:
        raise Http404
    form = ResetCredentialsForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        error = confirm_code(request, request.user, AREA_ADMIN, form.cleaned_data["code"])
        if error is not None:
            form.add_error("code" if error == WRONG_CODE else None, error)
        else:
            note = form.cleaned_data["note"]
            credential = None
            try:
                if form.cleaned_data["what"] == ResetCredentialsForm.PASSWORD:
                    credential, notice = roles.reset_password(target, by=request.user, note=note)
                else:
                    notice = roles.reset_totp(target, by=request.user, note=note)
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                return render(
                    request,
                    "accounts/admin_reset_done.html",
                    {
                        "target": target,
                        "credential": credential,
                        "valid_hours": int(TEMPORARY_PASSWORD_VALIDITY.total_seconds() // 3600),
                        "notice_message": _notice_message(notice),
                        "notice_queued": notice.queued,
                    },
                )
    return render(
        request,
        "accounts/admin_reset.html",
        {
            "target": target,
            "form": form,
            "own_account": target.pk == request.user.pk,
            "no_address_warning": (
                NO_NOTIFICATION_ADDRESS if not target.notification_email else None
            ),
        },
    )


@never_cache
@require_GET
def admin_home(request):
    # Els enllaços són els del menú comú (`navigation.admin_navigation`, T-M01-46): només hi
    # surten amb el permís de la ruta, i cada vista el torna a comprovar igualment.
    # CA-10.1 (T-M00-03): menys de dos comptes d'emergència a punt.
    context = {
        "emergency_ready": emergency.warning_for(request.user),
        "emergency_minimum": emergency.MINIMUM,
    }
    return render(request, "accounts/admin_home.html", context)
