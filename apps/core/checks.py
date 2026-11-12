"""Comprovacions d'arrencada de la base comuna (`manage.py check`).

Avís del 80 % del límit diari de correu (T-M00-06; RN-A6, CA-A3; decisió 081, punt 21): el rep
**només l'administrador**, a l'adreça configurada expressament a `EMAIL_ALERT_TO`. La plataforma
no la dedueix de cap compte ni n'inventa cap.

- Una adreça mal escrita és un error a qualsevol entorn (`core.E001`).
- Sense cap adreça, l'avís no és operatiu: només queda al registre d'activitat. La comprovació
  de desplegament (`check --deploy`, el pas del CI amb `--fail-level WARNING`) ho marca com a
  pendent de configuració (`core.W001`), de manera que producció no arrenca com si l'avís
  funcionés.
"""

from django.conf import settings
from django.core.checks import Error, Tags, Warning, register
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

ALERT_SETTING = "EMAIL_ALERT_TO"


def _alert_addresses():
    return [address.strip() for address in getattr(settings, ALERT_SETTING, []) or []]


@register(Tags.compatibility)
def email_alert_addresses_are_valid(app_configs, **kwargs):
    errors = []
    for address in _alert_addresses():
        try:
            validate_email(address)
        except ValidationError:
            errors.append(
                Error(
                    f"{ALERT_SETTING} conté una adreça no vàlida.",
                    hint="Escriu l'adreça de l'administrador que rep l'avís del límit de correu.",
                    id="core.E001",
                )
            )
    return errors


@register(Tags.security, deploy=True)
def email_alert_has_a_recipient(app_configs, **kwargs):
    if _alert_addresses():
        return []
    return [
        Warning(
            f"{ALERT_SETTING} és buida: l'avís del 80 % del límit diari de correu no arriba a "
            "ningú i no és operatiu (decisió 081, punt 21).",
            hint="Configura l'adreça de l'administrador que el rep. No la dedueixis de cap compte.",
            id="core.W001",
        )
    ]
