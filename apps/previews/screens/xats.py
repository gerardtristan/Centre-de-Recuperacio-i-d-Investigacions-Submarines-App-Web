"""T-DX-39 Teletipo i Amanuense: els xats (P-97, A; P-95: sense veu). Contingut d'exemple."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Xats")
CONTEXT = {
    # Converses d'exemple: per activitat (només hi entren els inscrits i qui la gestiona) i generals
    "chats": [
        {"name": _("Sortida de dissabte"), "kind": _("Activitat"), "unread": 3, "current": True},
        {"name": _("Curs d'iniciació"), "kind": _("Activitat"), "unread": 0, "current": False},
        {"name": _("Secretaria del club"), "kind": _("General"), "unread": 1, "current": False},
    ],
    # Missatges d'exemple, amb rols i no noms; «mine» = escrit pel soci que mira
    "messages": [
        {
            "who": _("Instructor"),
            "text": _("Bon dia! Dissabte quedem a les 9 al port."),
            "time": "09:12",
            "mine": False,
            "read": True,
        },
        {
            "who": _("Tu"),
            "text": _("Perfecte. Hi haurà lloc al cotxe?"),
            "time": "09:20",
            "mine": True,
            "read": True,
        },
        {
            "who": _("Instructor"),
            "text": _("Sí, en parlem divendres."),
            "time": "10:05",
            "mine": False,
            "read": False,
        },
        {
            "who": _("Organització"),
            "text": _("Recordeu portar el carnet."),
            "time": "10:30",
            "mine": False,
            "read": False,
        },
    ],
}
