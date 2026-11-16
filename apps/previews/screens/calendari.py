"""T-DX-23 Horario: el calendari general de l'àrea del soci. Contingut d'exemple, inventat i fix.

Cada activitat porta la fila on comença (`hNN`, l'hora) i quantes hores dura (`dN`): són classes
per tram, perquè la plantilla no pot portar cap `style=`. Els encavalcaments (`xocs`) els calcularà
el servidor; aquí són fixos.
"""

from django.utils.translation import gettext_lazy as _

TITLE = _("Calendari")


def _act(title, kind, hours, place, start, span, enrolled=False, clash=False):
    return {
        "title": title,
        "kind": kind,
        "hours": hours,
        "place": place,
        "start": start,
        "span": span,
        "enrolled": enrolled,
        "clash": clash,
    }


CONTEXT = {
    "week": _("Setmana del 12 al 18 d'abril de 2027"),
    "hours": [f"{h:02d}:00" for h in range(8, 22)],
    "days": [
        {"name": _("Dilluns 12/04"), "acts": [], "clashes": []},
        {
            "name": _("Dimarts 13/04"),
            "acts": [
                _act(
                    _("Entrenament a la piscina"),
                    _("Entrenament"),
                    "19:00–21:00",
                    _("Piscina de l'exemple"),
                    "h19",
                    "d2",
                ),
            ],
            "clashes": [],
        },
        {
            "name": _("Dimecres 14/04"),
            "acts": [
                _act(
                    _("Curs Open Water: teoria"),
                    _("Curs"),
                    "19:00–21:00",
                    _("Local del club"),
                    "h19",
                    "d2",
                    enrolled=True,
                    clash=True,
                ),
                _act(
                    _("Xerrada: fotografia submarina"),
                    _("Xerrada"),
                    "20:00–22:00",
                    _("Local del club"),
                    "h20",
                    "d2",
                    clash=True,
                ),
            ],
            "clashes": [{"start": "h20", "span": "d1"}],
        },
        {
            "name": _("Dijous 15/04"),
            "acts": [
                _act(
                    _("Curs Open Water: piscina"),
                    _("Curs"),
                    "20:00–22:00",
                    _("Piscina de l'exemple"),
                    "h20",
                    "d2",
                    enrolled=True,
                ),
            ],
            "clashes": [],
        },
        {"name": _("Divendres 16/04"), "acts": [], "clashes": []},
        {
            "name": _("Dissabte 17/04"),
            "acts": [
                _act(
                    _("Sortida a les Medes"),
                    _("Sortida"),
                    "08:00–14:00",
                    _("L'Estartit"),
                    "h08",
                    "d6",
                    enrolled=True,
                ),
            ],
            "clashes": [],
        },
        {
            "name": _("Diumenge 18/04"),
            "acts": [
                _act(
                    _("Sortida a Tossa"),
                    _("Sortida"),
                    "09:00–13:00",
                    _("Tossa de Mar"),
                    "h09",
                    "d4",
                ),
            ],
            "clashes": [],
        },
    ],
    "clash_note": _(
        "Dimecres 14/04, de 20:00 a 21:00, la teva inscripció a «Curs Open Water: teoria» "
        "es trepitja amb «Xerrada: fotografia submarina»."
    ),
}
