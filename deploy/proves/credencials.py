"""Envia a la bústia de proves (Mailpit) com s'entra a l'entorn de proves, un cop carregades les
dades inventades (decisió 090; docs/entorn-de-proves.md). Així el secret TOTP del servidor no surt
mai als registres: només el veu qui coneix la contrasenya del davant, que obre la bústia."""

import pyotp
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from apps.core.management.commands.seed_demo_data import PASSWORD, ROLE_ACCOUNTS, is_staging

# example.org és un domini reservat (RFC 2606); la bústia de proves ho captura tot igualment.
TO = "proves@example.org"


def envia() -> None:
    if not is_staging():
        raise RuntimeError("Només a l'entorn de proves.")
    secret = settings.STAGING_TOTP_SECRET
    site = settings.PUBLIC_SITE_URL
    accounts = "\n".join(f"  {login}  ({name})" for login, name, _role in ROLE_ACCOUNTS)
    uri = pyotp.TOTP(secret).provisioning_uri(name="proves", issuer_name="C.R.I.S. proves")
    body = f"""Entorn de proves del C.R.I.S. Només dades inventades.

Administració: {site}{reverse('administration:login')}
Comptes (contrasenya: {PASSWORD}):
{accounts}

Codi de doble factor, el mateix per a tots els comptes. Afegeix aquest secret a l'app
d'autenticació (Google Authenticator, Aegis, etc.) com a clau manual:
  {secret}
o obre aquest enllaç des del mòbil:
  {uri}

Àrea personal dels socis inventats: {site}{reverse('accounts:login')}
Els correus de la plataforma arriben a aquesta mateixa bústia: cap no surt a fora.
"""
    send_mail("Entorn de proves: com s'hi entra", body, None, [TO])
