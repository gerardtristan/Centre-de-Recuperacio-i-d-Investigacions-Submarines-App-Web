"""Contacte (T-M07-11 i T-M07-12; P-M07-D, RN-M07-07, 08 i 14; CA-M07-11 i 12).

- `submit`: el formulari públic, darrere de `website.contact_enabled` (apagat; P-486). Robots,
  sense cap servei de tercers: camp parany, temps mínim i límit per origen. Un robot o un origen
  limitat rep la mateixa resposta que un visitant i no es desa res.
- `visible_to`, `reply` i `close`: la safata. WP5 (`website.contact`) i, a més, l'abast per motiu:
  un compte només veu els motius que tenen algun dels seus rols (`ContactReason.roles`, WP8).
- Correus (T-M07-13b), sempre a la cua: l'avís als comptes del motiu en desar un missatge, només
  amb el nom del motiu, i la resposta al visitant, només amb el motiu i la resposta.
- `purge_finished`: la tasca diària; esborra els missatges acabats fa més de
  `website.contact_retention_months` i en deixa la traça al registre sense el contingut.

Les pantalles de la safata i dels motius (WP8) s'inclouen a `accounts/admin_urls.py`.
"""

import time

from django.core import signing
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.accounts import limits
from apps.core import audit, business_settings, mail
from apps.core.permissions import accounts_with_perm, active_role_codes, has_perm
from apps.payments.expiry import months_after

from .models import ContactMessage

ENABLED = "website.contact_enabled"
RETENTION_MONTHS = "website.contact_retention_months"
PERMISSION = "website.contact"  # WP5
ACTION_ANSWERED = "website.contact_answered"
ACTION_CLOSED = "website.contact_closed"
NOTICE_TEMPLATE = "avis-missatge-contacte"
REPLY_TEMPLATE = "resposta-contacte"
ACTION_DELETED = "website.contact_deleted"
# Seguretat (M07-6, «Es queden al codi»): un humà no omple el formulari en menys de 3 segons, i
# un formulari obert fa més d'un dia es torna a carregar.
MIN_SECONDS = 3
MAX_AGE = 24 * 3600
_SALT = "website.contact.started"
# El motiu del tancament queda al registre després d'esborrar el missatge (CA-M07-12): la
# pantalla de la safata (torn del nucli) el mostra com a ajuda del camp.
CLOSE_REASON_HELP = gettext_lazy("No hi escriguis dades del visitant.")


def started_token() -> str:
    return signing.dumps(time.time(), salt=_SALT)


def _started_at(started: str) -> float | None:
    """L'hora d'obertura si la signatura és bona i té menys d'un dia; si no, `None`."""
    try:
        return float(signing.loads(started, salt=_SALT, max_age=MAX_AGE))
    except (signing.BadSignature, TypeError, ValueError):
        return None


def keep_started(started: str) -> str:
    """En tornar el formulari amb errors, la mateixa hora d'obertura si és vàlida: qui corregeix
    un error de pressa no és un robot (revisió de la #580)."""
    return started if _started_at(started) is not None else started_token()


def looks_like_a_robot(honeypot: str, started: str) -> bool:
    since = _started_at(started)
    return bool(honeypot) or since is None or time.time() - since < MIN_SECONDS


@transaction.atomic
def submit(data: dict, *, ip: str, privacy_text) -> ContactMessage | None:
    """Desa el missatge, o res si l'origen està limitat. El robot ja l'ha filtrat la vista."""
    # shortcut: comparteix el límit per origen del «Fer-se soci» (P-450), com el 02 (T-M02-14);
    # quan el nucli hi tingui una finalitat pròpia per al contacte, fer-la servir aquí.
    if limits.start_join(ip) is None:
        return None
    message = ContactMessage.objects.create(
        reason=data["reason"],
        name=data["name"].strip(),
        email=data["email"],
        body=data["body"].strip(),
        privacy_text=privacy_text,
    )
    notify(message)
    return message


def recipients(reason):
    """Els comptes amb WP5 i algun rol del motiu (RN-M07-07, CA-M07-11)."""
    roles = set(reason.roles.values_list("code", flat=True))
    return [
        account
        for account in accounts_with_perm(PERMISSION, write=True)
        if roles & active_role_codes(account)
    ]


def notify(message: ContactMessage) -> int:
    sent = 0
    for account in recipients(message.reason):
        if account.notification_email:
            mail.queue_email(
                NOTICE_TEMPLATE, to=account.notification_email, person=account.person,
                context={"reason": message.reason.name},
            )  # fmt: skip
            sent += 1
    return sent


def visible_to(account):
    """Els missatges dels motius que té algun rol del compte, si té WP5; si no, cap."""
    if not has_perm(account, PERMISSION):
        return ContactMessage.objects.none()
    roles = active_role_codes(account)
    return ContactMessage.objects.filter(reason__roles__code__in=roles).distinct()


def _lock_new(message, actor):
    """El missatge bloquejat, si el compte el pot gestionar i encara és nou; fora de l'abast,
    «no trobat» com la resta de la plataforma."""
    if not (
        has_perm(actor, PERMISSION, write=True) and visible_to(actor).filter(pk=message.pk).exists()
    ):
        raise ContactMessage.DoesNotExist
    message = ContactMessage.objects.select_for_update().get(pk=message.pk)
    if message.status != ContactMessage.Status.NEW:
        raise ValidationError(_("Aquest missatge ja està respost o tancat."))
    return message


@transaction.atomic
def reply(message: ContactMessage, *, actor, answer: str) -> ContactMessage:
    """Respondre per correu des de cris@cris.es (P-M07-D, 085), amb registre (RN-M07-14)."""
    answer = (answer or "").strip()
    if not answer:
        raise ValidationError(_("Cal escriure la resposta."))
    message = _lock_new(message, actor)
    message.status, message.answer, message.answered_by = (
        ContactMessage.Status.ANSWERED, answer, actor,
    )  # fmt: skip
    message.finished_at = timezone.now()
    message.save(update_fields=["status", "answer", "answered_by", "finished_at"])
    mail.queue_email(
        REPLY_TEMPLATE, to=message.email,
        context={"reason": message.reason.name, "answer": answer},
    )  # fmt: skip
    audit.record(
        ACTION_ANSWERED, actor=actor, target=message, field="status",
        old=ContactMessage.Status.NEW, new=message.status,
    )  # fmt: skip
    return message


@transaction.atomic
def close(message: ContactMessage, *, actor, reason: str) -> ContactMessage:
    """Tancar sense resposta, amb motiu i registre (P-M07-D, RN-M07-14). Fora de l'abast, «no
    trobat» com la resta de la plataforma."""
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal el motiu del tancament."))
    message = _lock_new(message, actor)
    message.status, message.closed_reason = ContactMessage.Status.CLOSED, reason
    message.finished_at = timezone.now()
    message.save(update_fields=["status", "closed_reason", "finished_at"])
    audit.record(
        ACTION_CLOSED, actor=actor, target=message, field="status",
        old=ContactMessage.Status.NEW, new=message.status, reason=reason,
    )  # fmt: skip
    return message


def purge_finished(now=None) -> int:
    """CA-M07-12. Idempotent: un missatge esborrat ja no hi és. Torna quants n'ha esborrat."""
    now = now or timezone.now()
    cutoff = months_after(now, -business_settings.get(RETENTION_MONTHS))
    actor = audit.system("website.contact_retention")
    deleted = 0
    for message in ContactMessage.objects.filter(finished_at__lt=cutoff):
        with transaction.atomic():
            audit.record(
                ACTION_DELETED, actor=actor, target=message,
                details={"status": message.status, "finished_at": message.finished_at.isoformat()},
            )  # fmt: skip
            message.delete()
        deleted += 1
    return deleted
