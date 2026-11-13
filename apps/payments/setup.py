"""Compte de trànsit del proveïdor configurat (T-M05a-16, la part del proveïdor; RN-T08).

El proveïdor es configura amb `PAYMENTS_PROVIDER`, i cada desplegament executa `migrate`: en
acabar (`post_migrate`), es demana a la 04 el trànsit del proveïdor. És idempotent, de manera que
en qualsevol entorn amb un proveïdor configurat (també el fals) el compte existeix sense cap pas
a mà, i una notificació pagada acaba en ingrés. El trànsit «Remeses SEPA» arriba amb les remeses.
"""

from django.conf import settings
from django.utils.translation import gettext as _

from apps.treasury import services as treasury

from .providers import REGISTRY


def ensure_transit_account(*, apps, **kwargs):
    code = settings.PAYMENTS_PROVIDER
    if code not in REGISTRY:  # sense proveïdor (o un de desconegut, payments.E002): res a fer
        return
    try:
        apps.get_model("treasury", "TreasuryAccount")
    except LookupError:  # migració enrere fins abans de la tresoreria
        return
    treasury.create_transit_account(code, _("Trànsit del proveïdor «%(code)s»") % {"code": code})
