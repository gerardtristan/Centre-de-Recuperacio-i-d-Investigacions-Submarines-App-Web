"""T-DX-19 Avisador: l'editor de permisos dels rols (funcional amb la T-RP-03). Contingut d'exemple.

Les files i els valors inicials surten de la configuració inicial de la matriu (pla, apèndix de
la 059); el canvi del Tresorer és inventat, per ensenyar el resum.
"""

from django.utils.translation import gettext_lazy as _

TITLE = _("Rols i permisos")

ROLES = [_("Secretaria"), _("Tresorer"), _("President"), _("Junta"), _("Administrador")]
YES, NO = _("Sí"), _("—")


def _cells(*values, before=None):
    """Una cel·la per rol; `before` marca el valor d'abans d'un canvi pendent: {índex: valor}."""
    before = before or {}
    return [
        {"role": role, "value": value, "before": before.get(i)}
        for i, (role, value) in enumerate(zip(ROLES, values, strict=True))
    ]


CONTEXT = {
    "roles": ROLES,
    "rows": [
        {
            "code": "P2",
            "name": _("Crear una alta presencial"),
            "cells": _cells(YES, NO, NO, NO, YES),
        },
        {
            "code": "P3a",
            "name": _("Consultar sol·licituds d'alta, de canvi de tipus i de baixa"),
            "cells": _cells(YES, YES, YES, NO, YES),
        },
        {
            "code": "P3",
            "name": _("Aprovar o rebutjar altes"),
            "cells": _cells(YES, NO, YES, NO, YES, before={1: YES}),
        },
        {
            "code": "M3",
            "name": _("Crear comptes d'administrador, assignar i retirar rols"),
            "protected": True,
        },
        {
            "code": "M3b",
            "name": _("Modificar els permisos dels rols"),
            "protected": True,
        },
    ],
    "options": [YES, NO],
    "summary": [
        _("Tresorer: «Aprovar o rebutjar altes» passa de «Sí» a «—»."),
        _("Toca dades personals: les sol·licituds d'alta."),
    ],
    # Noms d'usuari inventats de l'exemple (el resum real els treu dels comptes amb el rol)
    "affected": ["jordi.tresoreria"],
}
