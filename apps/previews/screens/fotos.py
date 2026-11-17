"""T-DX-37 Fototeca i Expositor: les fotos del soci. Contingut d'exemple; cap foto real."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Fotos")
CONTEXT = {
    "folders": [
        {"name": _("Fauna"), "count": 24, "current": True},
        {"name": _("Sortides"), "count": 18, "current": False},
        {"name": _("Cursos"), "count": 9, "current": False},
    ],
    # «to» tria el degradat decoratiu que fa de foto (regla D11: cap foto de la demostració)
    "photos": [
        {"name": "posidonia-01.jpg", "to": 1, "selected": True},
        {"name": "nudibranqui-02.jpg", "to": 2, "selected": False},
        {"name": "pop-03.jpg", "to": 3, "selected": True},
        {"name": "estrella-04.jpg", "to": 4, "selected": False},
        {"name": "anfora-05.jpg", "to": 2, "selected": False},
        {"name": "mero-06.jpg", "to": 1, "selected": False},
    ],
    "detail": {"name": "posidonia-01.jpg", "tags": [_("fauna"), _("prada"), _("exemple")]},
    "used": 64,  # % de l'espai d'exemple
    # Expositor: la graella de pujada. «state»: llesta, pujant (amb el %), massa petita
    "uploads": [
        {"name": "sortida-01.jpg", "to": 3, "state": "llesta", "cover": True},
        {"name": "sortida-02.jpg", "to": 1, "state": "llesta", "cover": False},
        {"name": "sortida-03.jpg", "to": 4, "state": "pujant", "pct": 60, "cover": False},
        {"name": "sortida-04.jpg", "to": 2, "state": "petita", "cover": False},
    ],
    "min_side": 800,
}
