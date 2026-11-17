"""Salvaguarda del nivell 1 (T-M05a-06; RN-M05a-11; CA-M05a-09; decisions 025 i 042).

Nivell 1 de producció: dades reals per recollir mètodes i mandats, **cap cobrament real**. Amb
l'entorn real (`PAYMENTS_ENVIRONMENT = "live"`) només es cobra amb `PAYMENTS_LIVE_CHARGES_ALLOWED`,
que s'activa al nivell 2 amb l'autorització de la junta. Un entorn que no és «sandbox» compta com
el real (falla tancada). És l'única lectura d'aquesta autorització fora de les comprovacions
d'arrencada (`checks.py`); una prova ho vigila.

Camins que poden moure diners de debò, i on els atura:
- Targeta, Bizum i transferència, també la del convidat: `checkout.start_payment`, abans de la
  transacció i de parlar amb el proveïdor.
- Ordres i targeta guardada directament a l'adaptador: `PaymentProvider.create_order` i
  `charge_saved_card` (segona barrera).
- Remesa: `remittances.build_remittance`. Fitxer pain.008: `sepa_xml.remittance_file`.

No s'aturen, perquè no cobren: només registren el que el proveïdor o el banc ja han fet, i
aturar-los amagaria diners reals (per exemple, d'un nivell 2 que es desactiva): les
notificacions, la xarxa de seguretat, la importació de liquidacions i la conciliació. Les
devolucions tornen diners d'un pagament que ja existeix i no passen per aquí (contracte de
l'adaptador): P-281.

Cada negativa queda al registre d'activitat («sistema») i al registre de seguretat.
"""

import logging
from functools import wraps

from django.conf import settings

from apps.core import audit

from .providers.base import LIVE, SANDBOX, LiveChargesNotAllowed

REFUSED = "payments.live_charge_refused"
ACTOR = audit.system("payments-level-1")
logger = logging.getLogger("cris.security")


def charges_allowed() -> bool:
    environment = settings.PAYMENTS_ENVIRONMENT
    if environment == SANDBOX:
        return True
    return environment == LIVE and settings.PAYMENTS_LIVE_CHARGES_ALLOWED


def ensure_charges_allowed(operation: str) -> None:
    """`LiveChargesNotAllowed` amb el nivell 1, amb la negativa al registre. `operation`: quin
    camí ho ha demanat (cap dada personal)."""
    if charges_allowed():
        return
    environment = settings.PAYMENTS_ENVIRONMENT
    logger.warning("live_charge_refused operation=%s environment=%s", operation, environment)
    # shortcut: dins d'una transacció que es desfà, l'entrada del registre d'activitat també es
    # desfà (la de seguretat es queda); per això els serveis la criden abans d'obrir-la.
    audit.record(REFUSED, actor=ACTOR, details={"operation": operation, "environment": environment})
    raise LiveChargesNotAllowed(operation)


def requires_charges(operation: str):
    """Decorador: la salvaguarda abans d'entrar a la funció i a la seva transacció, perquè la
    negativa quedi al registre (CA-M05a-09). Va per sobre de `@transaction.atomic`."""

    def decorate(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            ensure_charges_allowed(operation)
            return function(*args, **kwargs)

        return wrapper

    return decorate
