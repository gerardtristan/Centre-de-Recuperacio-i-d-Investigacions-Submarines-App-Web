"""Verificació del correu i recuperació de la contrasenya del compte personal (spec 00, HU-04,
RN-18; CK C4 i C5). Els comptes d'administrador no en tenen cap: RN-16 i RN-19.

Els correus surten pel servei comú (`apps.core.mail`), mai directament cap al proveïdor.

Els enllaços porten el testimoni a la ruta. Per reduir-ne l'exposició:
- la primera petició no canvia res: desa el testimoni a la sessió i redirigeix a una adreça
  sense testimoni, de manera que no queda a la pàgina, ni a les capçaleres «Referer» de les
  peticions següents, ni a l'historial de la pàgina on es confirma;
- l'operació (confirmar el correu, canviar la contrasenya) només es fa amb un POST: un
  programa que obre els enllaços dels correus per revisar-los no la completa;
- cap testimoni va al registre d'activitat ni als registres de l'aplicació (comprovat amb
  proves). La petició inicial sí que passa pel proxy, que és a part: que els seus registres
  d'accés no guardin aquestes rutes és un pendent d'informàtica abans de dades reals
  (arquitectura §7) [A verificar: informàtica].

Demanar els enllaços (decisió 065): la recuperació i el reenviament de la verificació tenen
els límits de `limits.py` i una resposta pública que no depèn de si el compte existeix, de
l'estat ni de si s'ha limitat. Un compte pendent no rep recuperació (RN-M01-59).

Canvi del correu d'entrada des del perfil (074, RN-M01-79, CA-M01-78): el soci amb sessió
demana l'adreça nova, que rep l'enllaç; el correu d'entrada no canvia fins que es confirma, i
l'adreça antiga en rep un avís sense cap enllaç. Mateixos límits i la mateixa resposta tant si
l'adreça ja té compte com si no.
"""

import logging
import time
from dataclasses import dataclass

from cryptography.fernet import InvalidToken
from django.conf import settings
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from apps.core import audit, crypto, mail, persons
from apps.core.normalization import normalize_email

from . import limits, tokens
from .forms import NewPasswordForm
from .models import Account, EmailLinkRequest, normalize_login
from .security import client_ip

logger = logging.getLogger("cris.security")

VERIFY_SESSION_KEY = "link_verify_email"
RESET_SESSION_KEY = "link_reset_password"
# Compte pendent que ha escrit la contrasenya correcta: permet reenviaments mentre dura, amb
# els límits de RN-M01-58 (RN-M01-59, 066). No és cap sessió: el middleware no el mira i no
# dona accés a res.
RESEND_SESSION_KEY = "verification_resend"

RESET = EmailLinkRequest.Purpose.RESET_PASSWORD
VERIFY = EmailLinkRequest.Purpose.VERIFY_EMAIL
CHANGE = EmailLinkRequest.Purpose.CHANGE_EMAIL
CHANGE_SESSION_KEY = "link_change_email"


def _link(url_name: str, token: str) -> str:
    return settings.PUBLIC_SITE_URL + reverse(url_name, args=[token])


def hours(purpose: tokens.Purpose) -> int:
    """Caducitat d'un enllaç en hores, per als textos (mai un literal: V-01)."""
    return int(purpose.max_age.total_seconds() // 3600)


def send_verification(account: Account) -> bool:
    """Envia l'enllaç de verificació a un compte personal pendent. Torna si s'ha posat a la
    cua. No ho fa per a cap altre compte (RN-19: els d'administrador no es verifiquen)."""
    if account.kind != Account.Kind.PERSONAL or account.status != Account.Status.PENDING:
        return False
    mail.queue_email(
        "verificacio-correu",
        to=account.login,
        person=account.person,
        context={
            "link": _link(
                "accounts:verify_email_link", tokens.make_token(account, tokens.VERIFY_EMAIL)
            ),
            "hours": hours(tokens.VERIFY_EMAIL),
        },
    )
    return True


def _send_reset(account: Account) -> None:
    mail.queue_email(
        "recuperacio-contrasenya",
        to=account.login,
        person=account.person,
        context={
            "link": _link(
                "accounts:password_reset_link", tokens.make_token(account, tokens.RESET_PASSWORD)
            ),
            "hours": hours(tokens.RESET_PASSWORD),
        },
    )


def _limited(request, purpose: str, scope: str, account: Account | None = None) -> None:
    logger.info("email_link_limited purpose=%s scope=%s ip=%s", purpose, scope, client_ip(request))
    audit.record(
        audit.Action.EMAIL_LINK_LIMITED,
        actor=audit.ANONYMOUS,
        target=account,
        details={"purpose": purpose, "scope": scope},
        request=request,
    )


def _send_link(request, purpose: str, find_account, wanted_status: str, send) -> None:
    """Petició pública d'un enllaç amb els límits de RN-M01-58. No torna res: qui la crida
    respon sempre el mateix.

    Tot va dins d'una transacció, d'un en un per origen i per destinatari (bloquejos
    consultius): moltes peticions alhora no superen els límits. L'estat del compte es torna
    a comprovar amb la fila bloquejada just abans d'enviar."""
    ip = client_ip(request)
    with transaction.atomic():
        limits.lock_origin(ip)
        if limits.origin_limited(ip):
            _limited(request, purpose, "origin")
            return
        accepted = EmailLinkRequest.objects.create(ip_address=ip, purpose=purpose)
        account = find_account()
        if account is None:
            return
        key = limits.recipient_key(account.login)
        limits.lock_recipient(key)
        account = (
            Account.objects.select_for_update()
            .filter(pk=account.pk, kind=Account.Kind.PERSONAL, status=wanted_status)
            .first()
        )
        if account is None or limits.recipient_key(account.login) != key:
            return
        if limits.recipient_limited(key, purpose):
            # La fila es queda i compta per a l'origen (RN-M01-58, 066): si no, el límit
            # d'origen avançaria diferent segons si l'adreça té compte actiu.
            _limited(request, purpose, "recipient", account)
            return
        send(account)
        accepted.recipient_hash = key
        accepted.save(update_fields=["recipient_hash"])
        audit.record(
            audit.Action.EMAIL_LINK_SENT,
            actor=audit.ANONYMOUS,
            target=account,
            details={"purpose": purpose},
            request=request,
        )


def request_password_reset(request, email: str) -> None:
    """CA-04.3 i CA-M01-48: només un compte personal actiu rep l'enllaç; la resposta és la
    mateixa per a qualsevol adreça. Un compte pendent no en rep cap (RN-M01-59)."""

    def find_account():
        return Account.objects.filter(
            login=normalize_login(email), kind=Account.Kind.PERSONAL
        ).first()

    _send_link(request, RESET, find_account, Account.Status.ACTIVE, _send_reset)


def remember_pending(request, account: Account) -> None:
    """Després de la contrasenya correcta d'un compte pendent: permet reenviaments durant
    `limits.RESEND_STATE`. El compte el decideix el servidor."""
    request.session[RESEND_SESSION_KEY] = {"account": account.pk, "at": time.time()}


def resend_state_valid(request) -> bool:
    """L'estat de reenviament encara dura (no envia res). Si ha caducat, s'esborra."""
    data = request.session.get(RESEND_SESSION_KEY)
    if not data or time.time() - data.get("at", 0) > limits.RESEND_STATE.total_seconds():
        request.session.pop(RESEND_SESSION_KEY, None)
        return False
    return True


def resend_was_requested(request) -> bool:
    """Per a la pàgina posterior al POST: l'estat dura i s'hi ha demanat algun reenviament."""
    return resend_state_valid(request) and bool(
        request.session[RESEND_SESSION_KEY].get("requested")
    )


def resend_verification(request) -> bool:
    """Reenviament de la verificació (RN-M01-59, 066). L'estat no es consumeix: mentre dura,
    cada reenviament passa pels límits de RN-M01-58 i torna a comprovar que el compte és
    pendent. Torna False si no n'hi havia o havia caducat (cal tornar a escriure la
    contrasenya). Si l'estat era vàlid, la resposta no diu si s'ha enviat o s'ha limitat."""
    if not resend_state_valid(request):
        return False
    data = request.session[RESEND_SESSION_KEY]
    # La pàgina de després (GET) mostra la confirmació només si se n'ha demanat un en aquest
    # estat; un estat nou (remember_pending) torna a començar sense la marca.
    data["requested"] = True
    request.session.modified = True

    def find_account():
        return Account.objects.filter(pk=data.get("account"), kind=Account.Kind.PERSONAL).first()

    _send_link(request, VERIFY, find_account, Account.Status.PENDING, send_verification)
    return True


@dataclass
class ResetResult:
    account: Account | None = None
    form: NewPasswordForm | None = None
    done: bool = False


def reset_password(token: str, data=None, *, request=None) -> ResetResult:
    """CA-04.3 i CA-04.4: contrasenya nova amb l'enllaç de recuperació.

    Sense `data`, només comprova l'enllaç i torna el formulari buit. Amb `data`, ho fa tot
    amb la fila del compte bloquejada: si dues peticions arriben alhora, la segona troba la
    contrasenya ja canviada i el testimoni ja no val. Només comptes actius.

    No toca el doble factor: si el compte en té, l'entrada continua demanant-lo. Canviar la
    contrasenya tanca les sessions obertes del compte (l'empremta de sessió en depèn)."""
    with transaction.atomic():
        account = tokens.account_for_token(token, tokens.RESET_PASSWORD, lock=data is not None)
        if account is None or account.status != Account.Status.ACTIVE:
            return ResetResult()
        form = NewPasswordForm(account, data)
        if data is None or not form.is_valid():
            return ResetResult(account=account, form=form)
        audit.record(
            audit.Action.PASSWORD_RESET,
            actor=account,
            target=account,
            details={"channel": "email"},
            request=request,
        )
        form.save()
        return ResetResult(account=account, done=True)


@transaction.atomic
def confirm_email(token: str, *, request=None) -> Account | None:
    """Activa el compte pendent del testimoni (CA-04.2). Torna None si el testimoni no és vàlid
    o ja s'ha fet servir. La fila queda bloquejada: dues confirmacions alhora en fan una."""
    account = tokens.account_for_token(token, tokens.VERIFY_EMAIL, lock=True)
    if account is None or account.status != Account.Status.PENDING:
        return None
    audit.record(
        audit.Action.EMAIL_VERIFIED,
        actor=account,
        target=account,
        field="status",
        old=account.status,
        new=Account.Status.ACTIVE,
        request=request,
    )
    account.status = Account.Status.ACTIVE
    account.save(update_fields=["status", "updated_at"])
    return account


def request_email_change(request, account: Account, new_email: str) -> None:
    """RN-M01-79: envia a l'adreça nova l'enllaç per confirmar-la. No torna res: qui la crida
    respon sempre el mateix. No s'envia res si l'adreça és la mateixa, si ja és d'un altre
    compte, si el compte no és personal i actiu o si s'ha limitat (RN-M01-58: per origen,
    conjunt amb la recuperació i el reenviament, i per destinatari i finalitat)."""
    ip = client_ip(request)
    new_email = normalize_email(new_email)
    with transaction.atomic():
        limits.lock_origin(ip)
        if limits.origin_limited(ip):
            _limited(request, CHANGE, "origin", account)
            return
        accepted = EmailLinkRequest.objects.create(ip_address=ip, purpose=CHANGE)
        key = limits.recipient_key(new_email)
        limits.lock_recipient(key)
        account = (
            Account.objects.select_for_update()
            .filter(pk=account.pk, kind=Account.Kind.PERSONAL, status=Account.Status.ACTIVE)
            .first()
        )
        if account is None or Account.objects.filter(login=new_email).exists():
            return  # també la mateixa adreça: ja és el seu correu d'entrada
        if limits.recipient_limited(key, CHANGE):
            _limited(request, CHANGE, "recipient", account)
            return
        token = tokens.make_token(account, tokens.CHANGE_EMAIL, e=crypto.encrypt(new_email))
        mail.queue_email(
            "canvi-correu",
            to=new_email,
            person=account.person,
            context={
                "link": _link("accounts:change_email_link", token),
                "hours": hours(tokens.CHANGE_EMAIL),
            },
        )
        accepted.recipient_hash = key
        accepted.save(update_fields=["recipient_hash"])
        audit.record(
            audit.Action.EMAIL_LINK_SENT,
            actor=account,
            target=account,
            details={"purpose": CHANGE},
            request=request,
        )


def email_change_for_token(token: str, *, lock: bool = False) -> tuple[Account | None, str]:
    """El compte i l'adreça nova del testimoni, si encara és vàlid i el compte és actiu."""
    account, data = tokens.read_token(token, tokens.CHANGE_EMAIL, lock=lock)
    if account is None or account.status != Account.Status.ACTIVE:
        return None, ""
    try:
        return account, normalize_email(crypto.decrypt(str(data.get("e", ""))))
    except InvalidToken:
        return None, ""


@transaction.atomic
def confirm_email_change(token: str, *, request=None) -> Account | None:
    """Confirma el correu d'entrada nou (RN-M01-79). Torna None si l'enllaç no és vàlid, ja
    s'ha fet servir (l'empremta inclou el correu) o l'adreça ha passat a ser d'un altre compte
    entre la petició i la confirmació. El contacte de la persona canvia només si era l'adreça
    antiga. Les sessions obertes del compte no es tanquen (no està decidit)."""
    account, new_email = email_change_for_token(token, lock=True)
    if account is None or Account.objects.filter(login=new_email).exists():
        return None
    old_email = account.login
    account.login = new_email
    try:
        with transaction.atomic():
            account.save(update_fields=["login", "updated_at"])
    except IntegrityError:  # una altra confirmació simultània amb la mateixa adreça
        return None
    audit.record(
        audit.Action.LOGIN_EMAIL_CHANGED,
        actor=account,
        target=account,
        field="login",
        old=old_email,
        new=new_email,
        request=request,
    )
    person = account.person
    if normalize_email(person.contact_email) == old_email:
        persons.update(person, by=account, request=request, contact_email=new_email)
    mail.queue_email(
        "avis-canvi-correu", to=old_email, person=person, context={"when": timezone.now()}
    )
    return account
