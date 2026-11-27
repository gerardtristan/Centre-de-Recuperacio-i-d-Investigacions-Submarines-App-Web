"""Entrar al compte personal amb un enllaç d'un sol ús pel correu, sense contrasenya (T-M01-56;
decisió 108, D.3). Mai per a l'entrada d'administració: el testimoni només troba comptes
personals i les rutes són de l'entrada personal. Darrere de `PERSONAL_EMAIL_LOGIN_ENABLED`
(apagat; P-707): apagat, «no trobat».

- Demanar l'enllaç: la mateixa resposta per a qualsevol adreça, amb els límits de RN-M01-58.
- L'enllaç (15 minuts, un sol ús) no fa res en obrir-lo: desa el testimoni a la sessió i porta a
  una pàgina sense testimoni amb el botó «Entra» (POST), com la verificació del correu.
- Un compte amb doble factor continua demanant el codi; un compte bloquejat no entra.
- Revisió G: la petició no busca el compte (la cua l'envia, com la recuperació, T-M01-39b); per
  això no porta cap `next` i s'entra a l'inici.
- Revisió H: abans d'«Entra» es veu el correu emmascarat, i amb una sessió oberta l'enllaç no
  entra (no la substitueix mai).
"""

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from apps.core import audit

from . import email_links, tokens
from .forms import RecoveryRequestForm
from .models import Account
from .security import AREA_PERSONAL
from .sessions import complete_login, start_pending
from .views import _no_referrer, _same_origin_referrer

USED = "auth.email_login_used"
SENT_KEY = "email_login_sent"


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    return f"{local[:1]}***@{domain}"


def _enabled():
    if not settings.PERSONAL_EMAIL_LOGIN_ENABLED:
        raise Http404


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def email_login_request_view(request):
    _enabled()
    if request.method == "GET" and request.session.pop(SENT_KEY, False):
        minutes = int(tokens.EMAIL_LOGIN.max_age.total_seconds() // 60)
        context = {"sent": True, "minutes": minutes}
        return render(request, "accounts/email_login_request.html", context)
    form = RecoveryRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email_links.request_email_login(request, form.cleaned_data["email"])
        request.session[SENT_KEY] = True
        response = redirect("accounts:email_login_request")
        response.status_code = 303
        return response
    return render(request, "accounts/email_login_request.html", {"form": form})


@login_not_required
@never_cache
@require_GET
def email_login_link_view(request, token):
    _enabled()
    request.session[email_links.LOGIN_SESSION_KEY] = token
    return _no_referrer(redirect(reverse("accounts:email_login")))


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
def email_login_view(request):
    _enabled()
    token = request.session.get(email_links.LOGIN_SESSION_KEY, "")
    if request.user.is_authenticated:
        # Revisió H: un enllaç no substitueix mai una sessió oberta (ni la d'un altre compte).
        request.session.pop(email_links.LOGIN_SESSION_KEY, None)
        return render(request, "accounts/email_login.html", {"state": "signed_in"})
    if request.method == "POST":
        request.session.pop(email_links.LOGIN_SESSION_KEY, None)
        with transaction.atomic():
            account, data = tokens.read_token(token, tokens.EMAIL_LOGIN, lock=True)
            usable = (
                account is not None
                and account.status == Account.Status.ACTIVE
                and not account.is_locked(timezone.now())
            )
            if usable:
                audit.record(USED, actor=account, target=account, request=request)
                if account.has_totp:
                    start_pending(request, account, AREA_PERSONAL, None)
                    return redirect("accounts:login_totp")
                complete_login(request, account, AREA_PERSONAL)  # l'última entrada l'invalida
                return redirect("core:home")
        state = "invalid"
    else:
        account = tokens.account_for_token(token, tokens.EMAIL_LOGIN)
        state = "ready" if account else "invalid"
    if state == "invalid":
        request.session.pop(email_links.LOGIN_SESSION_KEY, None)
    # Revisió H: el correu emmascarat, perquè ningú no entri sense saber-ho al compte d'un altre.
    masked = mask_email(account.login) if state == "ready" else ""
    response = render(request, "accounts/email_login.html", {"state": state, "masked": masked})
    return _same_origin_referrer(response)
