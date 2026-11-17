"""T-DX-42 Apoderado: avisos de la junta i textos legals (P-91, A). Contingut d'exemple."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Avisos i textos legals")
CONTEXT = {
    # «state»: confirmar (demana confirmar la lectura), confirmat (amb el dia i l'hora), llegit
    "notices": [
        {
            "id": "avis-assemblea",
            "title": _("Convocatòria de l'assemblea"),
            "text": _(
                "Text d'exemple: la junta convoca l'assemblea de socis. Confirma que l'has llegit."
            ),
            "date": "14/11/2026",
            "state": "confirmar",
        },
        {
            "id": "avis-local",
            "title": _("Canvi d'horari del local"),
            "text": _("Text d'exemple: el local obrirà una hora més tard durant aquest mes."),
            "date": "10/11/2026",
            "state": "confirmat",
            "confirmed": "10/11/2026 18:40",
        },
        {
            "id": "avis-calendari",
            "title": _("Calendari de sortides"),
            "text": _("Text d'exemple: ja es pot consultar el calendari de sortides."),
            "date": "02/11/2026",
            "state": "llegit",
        },
    ],
    # Textos legals d'exemple: la versió acceptada i, si n'hi ha una de nova, la que cal acceptar
    "legal": [
        {"name": _("Normes del club"), "version": "2", "accepted": None},
        {"name": _("Política de privacitat"), "version": "3", "accepted": "05/09/2026"},
    ],
}
