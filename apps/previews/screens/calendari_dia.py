"""T-DX-29 Asueto: el calendari d'un dia a l'administració. Contingut d'exemple, inventat i fix.

L'horari, el motiu i les activitats són inventats. A la línia del dia, `start` és la columna de
l'hora d'inici (`c17`–`c22`) i `span` les hores (`s1`–`s6`): classes per tram, sense `style=`.
"""

from django.utils.translation import gettext_lazy as _

TITLE = _("Calendari d'un dia")

CONTEXT = {
    "day": _("Dimecres 14/04/2027 · Local del club"),
    "usual": _("Horari habitual: de 17:00 a 23:00"),
    "hours": ["17:00", "18:00", "19:00", "20:00", "21:00", "22:00"],
    "acts": [
        {
            "title": _("Revisió del material"),
            "hours": "17:00–18:00",
            "start": "c17",
            "span": "s1",
            "fits": True,
        },
        {
            "title": _("Curs Open Water: teoria"),
            "hours": "19:00–21:00",
            "start": "c19",
            "span": "s2",
            "fits": False,
            "free": _("Primera hora lliure: dijous 15/04 a les 19:00"),
        },
        {
            "title": _("Xerrada: fotografia submarina"),
            "hours": "20:00–22:00",
            "start": "c20",
            "span": "s2",
            "fits": False,
            "free": _("Primera hora lliure: dijous 15/04 a les 21:00"),
        },
    ],
}
