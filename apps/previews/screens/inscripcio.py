"""T-DX-24 Camilla i Comanda (P-94, resposta A): la inscripció a una activitat. Contingut d'exemple.

Camilla és el flux per passos (activitat, sessió, opcions, confirmar); Comanda, les opcions amb
regles i el botó que no s'encén fins que tot val. Cap dada de salut: el recurs Camilla és una
clínica i d'aquí se n'ha tret tot. Preus i regles són d'exemple, inventats; quan funcioni, els
calcularà i els validarà el servidor.
"""

from django.utils.translation import gettext_lazy as _

TITLE = _("Inscripció a una activitat")


def _opt(label, price="", checked=False):
    return {"label": label, "price": price, "checked": checked}


CONTEXT = {
    "activity": {
        "title": _("Sortida a les Medes"),
        "kind": _("Sortida"),
        "place": _("L'Estartit"),
        "price": "45,00 €",
    },
    "sessions": [
        {
            "when": _("Dissabte 17/04/2027 · 08:00–14:00"),
            "places": _("Queden 6 places"),
            "chosen": True,
        },
        {"when": _("Dissabte 17/04/2027 · 15:00–19:00"), "places": _("Queden 2 places")},
        {"when": _("Diumenge 18/04/2027 · 08:00–14:00"), "places": _("Completa"), "full": True},
    ],
    "groups": [
        {
            "name": _("Material de lloguer"),
            "rule": _("Tria'n fins a 3"),
            "kind": "checkbox",
            "state": _("2 de 3"),
            "ok": True,
            "options": [
                _opt(_("Jaqueta hidrostàtica"), "8,00 €", checked=True),
                _opt(_("Regulador"), "8,00 €", checked=True),
                _opt(_("Ordinador de busseig"), "5,00 €"),
                _opt(_("Llanterna"), "3,00 €"),
            ],
        },
        {
            "name": _("Vestit"),
            "rule": _("Tria'n un"),
            "kind": "radio",
            "state": _("Triat"),
            "ok": True,
            "options": [
                _opt(_("En porto un de meu"), checked=True),
                _opt(_("Neoprè de 5 mm"), "6,00 €"),
                _opt(_("Neoprè de 7 mm"), "6,00 €"),
            ],
        },
        {
            "name": _("Transport"),
            "rule": _("Tria'n un"),
            "kind": "radio",
            "state": _("Falta triar-ne un"),
            "ok": False,
            "options": [_opt(_("Hi vaig pel meu compte")), _opt(_("Plaça al cotxe del club"))],
        },
    ],
    "total": "61,00 €",
    "mine": [
        {"title": _("Curs Open Water"), "state": _("Inscripció confirmada"), "ok": True},
        {"title": _("Sortida a Tossa"), "state": _("Pendent de pagament"), "ok": False},
    ],
}
