"""Verificació del correu i recuperació de la contrasenya del compte personal (spec 00, HU-04,
RN-18; CK C4 i C5). Els comptes d'administrador no en tenen cap: RN-16 i RN-19.

Els correus surten pel servei comú (`apps.core.mail`), mai directament cap al proveïdor.

Els enllaços porten el testimoni a la ruta. Per reduir-ne l'exposició:
- la primera petició no canvia res: desa el testimoni a la sessió i redirigeix a una adreça
  sense testimoni, de manera que no queda a la pàgina, ni a les capçaleres «Referer» de les
  peticions següents, ni a l'historial de la pàgina on es confirma;
- l'operació (confirmar el correu, canviar la contrasenya) només es fa amb un POST: un
  programa que obre els enllaços dels correus per revisar-los no la completa;
- cap testimoni va al registre d'activitat ni als registres del servidor de la plataforma.
La petició inicial sí que passa pel proxy: els seus registres d'accés no han de guardar
aquestes rutes (arquitectura, variables i proxy) [A verificar: informàtica].
"""

from django.conf import settings
from django.db import transaction
from django.urls import reverse

from apps.core import audit, mail

from . import tokens
from .models import Account

VERIFY_SESSION_KEY = "link_verify_email"
RESET_SESSION_KEY = "link_reset_password"


def _link(url_name: str, token: str) -> str:
    return settings.PUBLIC_BASE_URL + reverse(url_name, args=[token])


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
            "hours": int(tokens.VERIFY_EMAIL.max_age.total_seconds() // 3600),
        },
    )
    return True


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
