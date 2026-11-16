"""T-DX-36 Probador i Pregon: l'editor de la web pública. Contingut d'exemple, inventat i fix."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Editor de la web")
CONTEXT = {
    # Plantilles com a dades; «kind» tria la miniatura (blocs genèrics, cap imatge real).
    "templates": [
        {"id": "pl-portada", "name": _("Portada"), "kind": "portada", "chosen": True},
        {"id": "pl-activitats", "name": _("Activitats"), "kind": "llista", "chosen": False},
        {"id": "pl-noticies", "name": _("Notícies"), "kind": "blog", "chosen": False},
    ],
    # El color només pot ser un dels tokens (pla dels recursos externs)
    "accents": [
        {"id": "ac-daurat", "name": _("Daurat"), "token": "accent", "chosen": True},
        {"id": "ac-mari", "name": _("Marí"), "token": "mari", "chosen": False},
        {"id": "ac-info", "name": _("Blau"), "token": "info", "chosen": False},
    ],
    # Vista en compartir (Pregon): títol i descripció d'exemple, amb el màxim recomanat
    "share": {
        "title": _("Bateig de mar a la Costa Brava"),
        "title_max": 60,
        "description": _(
            "Text d'exemple: una immersió curta i acompanyada per descobrir el busseig "
            "amb el club, pensada per a qui no ha bussejat mai."
        ),
        "description_max": 150,
        "host": "cris1954.cat",
    },
}
