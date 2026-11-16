"""T-DX-12 Deposito: el comprovant d'una transferència (proposta; el pla no el té, D1). Contingut
d'exemple, inventat i fix: cap persona, cap IBAN."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Comprovant de la transferència")
CONTEXT = {
    "concept": _("Quota de soci 2026"),
    "amount": "90,00 €",
    "reference": "Q-2026-EXEMPLE",
    "sent_on": "16/11/2026",
}
