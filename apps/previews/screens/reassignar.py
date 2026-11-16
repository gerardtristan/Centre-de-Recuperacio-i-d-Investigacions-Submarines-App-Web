"""T-DX-30 Reasigna: repartir les sessions d'un instructor que falta (mòdul 02, aparcat; D6).
Contingut d'exemple: instructors amb noms de pila inventats i sessions d'un dia inventat. Quan
funcioni, la proposta la calcularà el servidor i res no canviarà fins a «Confirma els canvis»."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Reassignar sessions")

ABSENT = "Jordi"
POOL = _("Pràctica a la piscina")
SEA = _("Immersió des de la costa")
THEORY = _("Classe teòrica")

CONTEXT = {
    "day": _("Dissabte 21 de novembre (exemple)"),
    "absent": ABSENT,
    "sessions": [
        {"time": "09:00", "name": THEORY, "instructor": "Laia"},
        {
            "time": "10:00",
            "name": POOL,
            "instructor": ABSENT,
            "to": "Laia",
            "shift": _("mateixa hora"),
        },
        {"time": "10:00", "name": SEA, "instructor": "Oriol"},
        {
            "time": "11:30",
            "name": THEORY,
            "instructor": ABSENT,
            "to": "Oriol",
            "shift": _("+30 min"),
        },
        {"time": "12:00", "name": SEA, "instructor": ABSENT, "no_place": True},
        {"time": "16:00", "name": POOL, "instructor": "Laia"},
    ],
    "margins": [_("Mateixa hora"), _("± 30 min"), _("± 1 h")],
    "margin": 1,
}
