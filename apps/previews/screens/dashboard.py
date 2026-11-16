"""T-DX-35 Parrilla: el dashboard configurable. Exemple: només xifres agregades, cap nom."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Dashboard")
CONTEXT = {
    # Veure el dashboard no dona accés a cap dada personal: tot són recomptes i percentatges.
    "active_members": 312,
    "new_this_month": 8,
    "up_to_date": 87,  # % de quotes al corrent (l'anell: 100 = la circumferència)
    # Altes per mes: «h» és l'alçada de la barra sobre 100 (la més alta = 100)
    "signups": [
        {"month": _("jun."), "value": 4, "h": 40},
        {"month": _("jul."), "value": 6, "h": 60},
        {"month": _("ag."), "value": 2, "h": 20},
        {"month": _("set."), "value": 10, "h": 100},
        {"month": _("oct."), "value": 7, "h": 70},
        {"month": _("nov."), "value": 8, "h": 80},
    ],
    # Inscripcions per dia en quatre setmanes: nivell 0 a 3
    "weeks": [
        [0, 1, 0, 2, 1, 3, 2],
        [1, 0, 1, 1, 2, 3, 3],
        [0, 2, 1, 0, 1, 2, 3],
        [1, 1, 0, 2, 2, 3, 1],
    ],
    "places": [
        {"name": _("Cursos"), "free": 9},
        {"name": _("Sortides"), "free": 14},
        {"name": _("Conferències"), "free": 40},
    ],
    "palette": [_("Llicències que caduquen"), _("Material en ús"), _("Inscripcions de la setmana")],
    "layout": (
        '{\n  "socis": [0, 0, 4, 3],\n  "altes": [4, 0, 5, 3],\n  "quotes": [9, 0, 3, 3],\n'
        '  "inscripcions": [0, 3, 6, 3],\n  "places": [6, 3, 6, 3]\n}'
    ),
}
