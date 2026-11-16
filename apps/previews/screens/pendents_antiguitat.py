"""T-DX-21 Cartola: càrrecs pendents i retornats per antiguitat. Pantalla proposada: el pla no la té
(D1), i els trams de dies són els del recurs, d'exemple. Contingut inventat; els imports ja surten
formatats, i quan funcioni el servidor els calcularà en cèntims."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Pendents per antiguitat")

PENDING = {"label": _("Pendent"), "symbol": "◷", "css": "estat-avis"}
RETURNED = {"label": _("Retornat"), "symbol": "✕", "css": "estat-error"}


BANDS = [
    {"label": _("0–30 dies"), "count": 2, "amount": "130,00 €"},
    {"label": _("31–60 dies"), "count": 2, "amount": "157,00 €"},
    {"label": _("Més de 60 dies"), "count": 1, "amount": "85,00 €", "late": True},
]


def _charge(concept, amount, status):
    return {"concept": concept, "amount": amount, "status": status}


def _row(number, name, *cells):
    """Un soci (número i nom de pila inventats) i, per a cada tram, els seus càrrecs."""
    return {
        "number": number,
        "name": name,
        "cells": [
            {"band": band["label"], "charges": charges}
            for band, charges in zip(BANDS, cells, strict=True)
        ],
    }


CONTEXT = {
    "bands": BANDS,
    "rows": [
        _row(
            "0275",
            "Núria",
            [_charge(_("Sortida a les Medes"), "45,00 €", PENDING)],
            [],
            [_charge(_("Quota anual 2026"), "85,00 €", RETURNED)],
        ),
        _row("0388", "Pau", [], [_charge(_("Quota anual 2026"), "85,00 €", RETURNED)], []),
        _row("0412", "Marta", [_charge(_("Quota anual 2026"), "85,00 €", PENDING)], [], []),
        _row(
            "0501", "Arnau", [], [_charge(_("Llicència federativa 2026"), "72,00 €", PENDING)], []
        ),
    ],
}
