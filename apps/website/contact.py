"""Contacte (T-M07-11 i T-M07-12; P-M07-D, RN-M07-07, 08 i 14; CA-M07-11 i 12).

- `submit`: el formulari públic, darrere de `website.contact_enabled` (apagat; P-486). Robots,
  sense cap servei de tercers: camp parany, temps mínim i límit per origen. Un robot o un origen
  limitat rep la mateixa resposta que un visitant i no es desa res.
- `visible_to` i `close`: la safata. WP5 (`website.contact`) i, a més, l'abast per motiu: un
  compte només veu els motius que tenen algun dels seus rols (`ContactReason.roles`, WP8).
- `purge_finished`: la tasca diària; esborra els missatges acabats fa més de
  `website.contact_retention_months` i en deixa la traça al registre sense el contingut.

Falten (torn del nucli): l'avís als comptes del motiu i la resposta al visitant per correu (les
plantilles es declaren a `core.mail.TEMPLATE_PRIORITIES`) i les pantalles de la safata i dels
motius (les rutes d'administració s'inclouen a `accounts/admin_urls.py`). Vegeu `docs/estat/M07.md`.
"""

import time

from django.core import signing
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts import limits
from apps.core import audit, business_settings
from apps.core.permissions import active_role_codes, has_perm
from apps.payments.expiry import months_after

from .models import ContactMessage

ENABLED = "website.contact_enabled"
RETENTION_MONTHS = "website.contact_retention_months"
PERMISSION = "website.contact"  # WP5
ACTION_CLOSED = "website.contact_closed"
ACTION_DELETED = "website.contact_deleted"
# Seguretat (M07-6, «Es queden al codi»): un humà no omple el formulari en menys de 3 segons, i
# un formulari obert fa més d'un dia es torna a carregar.
MIN_SECONDS = 3
MAX_AGE = 24 * 3600
_SALT = "website.contact.started"


def started_token() -> str:
    return signing.dumps(time.time(), salt=_SALT)


def looks_like_a_robot(honeypot: str, started: str) -> bool:
    if honeypot:
        return True
    try:
        since = signing.loads(started, salt=_SALT, max_age=MAX_AGE)
    except (signing.BadSignature, TypeError):
        return True
    return time.time() - float(since) < MIN_SECONDS


@transaction.atomic
def submit(data: dict, *, ip: str, privacy_text) -> ContactMessage | None:
    """Desa el missatge, o res si l'origen està limitat. El robot ja l'ha filtrat la vista."""
    # shortcut: comparteix el límit per origen del «Fer-se soci» (P-450), com el 02 (T-M02-14);
    # quan el nucli hi tingui una finalitat pròpia per al contacte, fer-la servir aquí.
    if limits.start_join(ip) is None:
        return None
    return ContactMessage.objects.create(
        reason=data["reason"],
        name=data["name"].strip(),
        email=data["email"],
        body=data["body"].strip(),
        privacy_text=privacy_text,
    )


def visible_to(account):
    """Els missatges dels motius que té algun rol del compte, si té WP5; si no, cap."""
    if not has_perm(account, PERMISSION):
        return ContactMessage.objects.none()
    roles = active_role_codes(account)
    return ContactMessage.objects.filter(reason__roles__code__in=roles).distinct()


@transaction.atomic
def close(message: ContactMessage, *, actor, reason: str) -> ContactMessage:
    """Tancar sense resposta, amb motiu i registre (P-M07-D, RN-M07-14). Fora de l'abast, «no
    trobat» com la resta de la plataforma."""
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal el motiu del tancament."))
    if not (
        has_perm(actor, PERMISSION, write=True) and visible_to(actor).filter(pk=message.pk).exists()
    ):
        raise ContactMessage.DoesNotExist
    message = ContactMessage.objects.select_for_update().get(pk=message.pk)
    if message.status != ContactMessage.Status.NEW:
        raise ValidationError(_("Aquest missatge ja està respost o tancat."))
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
