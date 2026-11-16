"""T-DX-22 Deposito: transferències i pagaments a revisar.

Funcional amb la T-M04-12 i la T-M05b-16. Contingut d'exemple, inventat: socis amb número i nom de
pila, referències amb el format de la T-M04-10 (sense cap control vàlid) i cap IBAN ni nom de qui
ordena la transferència.
"""

from django.utils.translation import gettext_lazy as _

TITLE = _("Transferències i pagaments a revisar")

CONTEXT = {
    "transfers": [
        {
            "id": "tr-1",
            "date": "12/11/2026",
            "amount": "85,00 €",
            "reference": "CRIS-7KQ4M-X",
            "charge": _("Quota anual 2026 · 0412 Marta · 85,00 €"),
            "proposed": True,
        },
        {
            "id": "tr-2",
            "date": "13/11/2026",
            "amount": "80,00 €",
            "reference": "CRIS-3HT9P-B",
            "charge": _("Quota anual 2026 · 0388 Pau · 85,00 €"),
            "blocker": _("L'import no coincideix amb el del càrrec."),
        },
    ],
    "payments": [
        {
            "id": "pg-1",
            "method": _("Bizum"),
            "amount": "85,00 €",
            "charge": _("Quota anual 2026 · 0275 Núria"),
            "reason": _("Pagament duplicat: la quota ja s'havia pagat per transferència."),
        },
    ],
}
