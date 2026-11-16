"""T-DX-27 Vistazo: els projectes del Departament d'Història. Contingut d'exemple, inventat."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Projectes")
CONTEXT = {
    # «to» tria el degradat decoratiu que fa de foto (cap imatge real: regla D11).
    "projects": [
        {
            "id": "p-01",
            "name": _("Arxiu de fotografies"),
            "kind": _("Arxiu"),
            "note": _("Digitalitzar i catalogar les fotos del club dels primers anys."),
            "to": 1,
        },
        {
            "id": "p-02",
            "name": _("Escafandre restaurat"),
            "kind": _("Material"),
            "note": _("Netejar i documentar un equip antic de la col·lecció del club."),
            "to": 2,
        },
        {
            "id": "p-03",
            "name": _("Mapa d'immersions"),
            "kind": _("Litoral"),
            "note": _("Recollir els punts d'immersió històrics del club en un mapa."),
            "to": 3,
        },
        {
            "id": "p-04",
            "name": _("Veus del club"),
            "kind": _("Memòria"),
            "note": _("Entrevistes gravades amb socis veterans, amb el seu consentiment."),
            "to": 4,
        },
    ],
}
