"""Supressió de grups petits (T-M08-03; RN-M08-02; CA-M08-03; P-487, decisió 105).

En un desglossament de persones (per tipus, per estat, per activitat...), una cel·la amb menys
de `dashboard.min_group_size` persones es mostra «menys de N». Si les cel·les petites sumen més
de 0 i menys de N, també s'amaga la visible més petita, perquè restant del total no se'n pugui
saber la suma (P-649); una cel·la a zero surt «menys de N» però no obliga a amagar res. El total es
mostra sempre, tret que ell mateix sigui per sota del mínim (P-648; també quan el desglossament
té una sola cel·la petita, perquè llavors el total és la cel·la).
No s'aplica als imports: només als indicadors de tipus «persones» (`indicators.KINDS`).
"""

from dataclasses import dataclass

from django.utils.translation import gettext as _

from apps.core import business_settings

MIN_GROUP_SIZE = "dashboard.min_group_size"

SHOWN, BELOW, HIDDEN = "shown", "below", "hidden"


@dataclass(frozen=True)
class Cell:
    value: int
    state: str  # SHOWN, BELOW (menys de N) o HIDDEN (amagada perquè no es dedueixi pel total)

    def label(self, min_size: int) -> str:
        if self.state == SHOWN:
            return str(self.value)
        if self.state == BELOW:
            return _("menys de %(n)s") % {"n": min_size}
        return _("amagat")


def suppress(counts: dict, min_size: int) -> tuple[dict, Cell]:
    """{clau: recompte} → ({clau: Cell}, total), en el mateix ordre. Funció pura."""
    below = {key for key, value in counts.items() if value < min_size}
    hidden = set()
    rest = [key for key in counts if key not in below]
    # P-649: n'hi ha prou amb una: una cel·la visible ja té N o més, i la suma amagada hi arriba.
    if 0 < sum(counts[key] for key in below) < min_size and rest:
        # La visible més petita; amb empat, la primera del desglossament.
        hidden.add(min(rest, key=lambda key: counts[key]))
    cells = {
        key: Cell(value, BELOW if key in below else HIDDEN if key in hidden else SHOWN)
        for key, value in counts.items()
    }
    total = sum(counts.values())
    # Un total per sota del mínim també és un grup petit (P-648); buit, no hi ha cap grup.
    small = bool(counts) and total < min_size
    return cells, Cell(total, BELOW if small else SHOWN)


def min_group_size(at=None) -> int:
    return business_settings.get(MIN_GROUP_SIZE, at)
