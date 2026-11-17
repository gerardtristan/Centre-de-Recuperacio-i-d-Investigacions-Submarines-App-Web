"""T-DX-38 Convite (P-99, resposta A): la capçalera de la fitxa d'una activitat. D'exemple.

Les places són comptadors, mai qui hi va. Totes les hores són locals (fora «La meva hora»).
"""

from django.utils.translation import gettext_lazy as _

TITLE = _("Fitxa d'una activitat")

CONTEXT = {
    "activity": {
        "kind": _("Sortida"),
        "title": _("Sortida a les Medes"),
        "lede": _("Dues immersions a les Illes Medes amb sortida des del port de l'Estartit."),
        "month": _("abr."),
        "day": "17",
        "weekday": _("dissabte"),
        "date": _("Dissabte 17/04/2027"),
        "hours": "08:00–14:00",
        "place": _("Port de l'Estartit"),
        "place_note": _("Punt de trobada al moll, davant del centre d'immersió"),
        "price": "45,00 €",
    },
    "places_total": 12,
    "places_left": 6,
    # Una casella per plaça: True si està ocupada (sense cap nom).
    "seats": [True] * 6 + [False] * 6,
}
