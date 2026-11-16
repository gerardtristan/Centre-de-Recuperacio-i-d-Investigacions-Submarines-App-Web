"""T-DX-34 Emisor: emetre la factura d'un càrrec (mòdul 09; P-93, resposta C). Contingut d'exemple.

La factura no la numera la plataforma: la demana a un servei homologat per Verifactu (RN-M09-17),
i la facturació està desactivada fins que la gestoria respongui (P-02, P-47; RN-M09-19). L'empresa,
el càrrec i l'import són inventats; el NIF es deixa buit perquè cap número d'exemple sembli real.
"""

from django.utils.translation import gettext_lazy as _

TITLE = _("Factures")

CONTEXT = {
    "charge": {
        "concept": _("Lloguer de material · Sortida a les Medes"),
        "amount": "120,00 €",
        "department": _("Sortides (exemple)"),
    },
    "company": _("Empresa d'exemple, SL"),
    "address": _("Carrer d'exemple, 1 · Barcelona"),
    "saved": [_("Empresa d'exemple, SL"), _("Escola d'exemple")],
}
