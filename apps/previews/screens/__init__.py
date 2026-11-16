"""Pantalles «En construcció» (design-system §6.9 i §16; pla dels recursos externs §1).

Una pantalla, un fitxer d'aquest paquet, que defineix `TITLE` (text traduïble) i, si cal,
`CONTEXT` (contingut d'exemple, inventat i fix; mai cap consulta a la base de dades). La plantilla
és `templates/previews/<nom>.html` i la ruta, `en-construccio/<nom>/` (els «_» passen a «-»).
Les rutes, l'índex i les proves les troben soles: afegir una pantalla no toca cap fitxer comú.
"""

import importlib
import pkgutil


def discover():
    """Les pantalles, per ordre alfabètic del nom del fitxer: (nom, mòdul)."""
    return [
        (info.name, importlib.import_module(f"{__name__}.{info.name}"))
        for info in sorted(pkgutil.iter_modules(__path__), key=lambda info: info.name)
    ]
