"""T-DX-41 Antefirma: les signatures de correu de l'administració (P-92, A). Contingut d'exemple."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Signatures de correu")
CONTEXT = {
    # Només càrrec i contacte del club: cap nom ni telèfon personal (pla dels recursos externs)
    "signature": {
        "role": _("Tresoreria"),
        "area": _("Junta directiva"),
        "entity": "C.R.I.S.",
        "email": "cris@cris.es",
        "web": "cris1954.cat",
    },
    "templates": [
        {"name": _("Clàssica"), "chosen": True},
        {"name": _("Amb línia"), "chosen": False},
        {"name": _("Compacta"), "chosen": False},
    ],
    "colors": [
        {"name": _("Daurat"), "token": "accent", "chosen": False},
        {"name": _("Marí"), "token": "mari", "chosen": True},
    ],
}
