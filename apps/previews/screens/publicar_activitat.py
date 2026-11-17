"""T-DX-31 Averia i Pregon: publicar una activitat. Contingut d'exemple, inventat i fix.

Averia posa el formulari amb les preguntes segons el tipus d'activitat i la foto; Pregon, la
vista prèvia de com es veurà en compartir-la (xat, xarxa social i correu). Les preguntes de cada
tipus seran dades; aquí són fixes.
"""

from django.utils.translation import gettext_lazy as _

TITLE = _("Publicar una activitat")

CONTEXT = {
    "kinds": [_("Sortida"), _("Curs"), _("Xerrada")],
    "title": _("Sortida a les Medes"),
    "title_count": 19,
    "title_max": 60,
    "description": _(
        "Dues immersions a les Illes Medes amb sortida des de l'Estartit. "
        "Inclou l'embarcació i l'ampolla; el material de lloguer es tria en apuntar-se."
    ),
    "questions": [
        {"label": _("Lloc"), "value": _("Illes Medes (l'Estartit)")},
        {"label": _("Data"), "value": "17/04/2027"},
        {"label": _("Places"), "value": "12"},
        {"label": _("Preu per a socis"), "value": "45,00 €"},
    ],
    "url": "cris1954.cat/activitats/sortida-a-les-medes",
    "checks": [
        {"text": _("Títol de menys de 60 caràcters"), "ok": True},
        {"text": _("Descripció de menys de 160 caràcters"), "ok": True},
        {"text": _("Falta la imatge per compartir"), "ok": False},
    ],
}
