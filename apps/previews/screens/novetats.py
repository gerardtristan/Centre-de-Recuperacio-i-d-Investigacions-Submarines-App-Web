"""T-DX-09 Baliza (P-98, resposta C): les novetats i el centre d'avisos. Contingut d'exemple."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Novetats i avisos")
CONTEXT = {
    "items": [
        {
            "id": "nov-carnet",
            "title": _("El carnet ja es pot baixar"),
            "note": _(
                "Des de «El meu carnet» ara pots desar-ne una còpia per quan no tinguis cobertura."
            ),
            "new": True,
        },
        {
            "id": "nov-tema",
            "title": _("Tema fosc a la configuració"),
            "note": _(
                "A «Seguretat del compte» pots triar el tema clar, el fosc o el del sistema."
            ),
            "new": True,
        },
        {
            "id": "nov-sortides",
            "title": _("Calendari de sortides"),
            "note": _("Aviat podràs veure i apuntar-te a les sortides del club des d'aquí."),
            "new": False,
        },
    ],
}
