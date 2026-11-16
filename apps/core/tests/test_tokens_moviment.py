"""T-DX-01: tokens de moviment (design-system §15.4).

Amb `prefers-reduced-motion: reduce`, cada durada passa a 0 i l'escala de premut a 1, i cap
durada no supera el llindar de Doherty, tret de les animacions que no bloquegen (l'ona i Oleaje).
"""

import re
from pathlib import Path

from django.conf import settings

TOKENS = (Path(settings.BASE_DIR) / "static" / "css" / "tokens.css").read_text(encoding="utf-8")
DURATION = re.compile(r"(--m-[a-z-]+):\s*([\d.]+)(ms|s);")
NOT_BLOCKING = {"--m-ona", "--m-oleaje"}


def _durations(text):
    return {
        name: float(value) * (1000 if unit == "s" else 1)
        for name, value, unit in DURATION.findall(text)
    }


def _reduced_motion_block():
    match = re.search(r"@media \(prefers-reduced-motion: reduce\) \{\s*:root \{([^}]*)\}", TOKENS)
    assert match, "falta el bloc de prefers-reduced-motion a tokens.css"
    return match.group(1)


def test_every_duration_is_zero_with_reduced_motion():
    declared = _durations(TOKENS.split("@media (prefers-reduced-motion")[0])
    reduced = _durations(_reduced_motion_block())
    assert declared, "no s'ha trobat cap durada"
    # El llindar és un temps d'espera, no una animació: no passa a 0.
    for name in declared.keys() - {"--m-llindar"}:
        assert reduced.get(name) == 0, f"{name} no passa a 0 amb prefers-reduced-motion"
    assert "--escala-premut: 1;" in _reduced_motion_block()


def test_no_blocking_duration_over_doherty_threshold():
    declared = _durations(TOKENS.split("@media (prefers-reduced-motion")[0])
    limit = declared["--m-llindar"]
    assert limit == 400
    for name, ms in declared.items():
        if name not in NOT_BLOCKING:
            assert ms <= limit, f"{name} ({ms} ms) supera el llindar de {limit} ms"


def test_press_scale_between_4_and_6_percent():
    scale = float(re.search(r"--escala-premut:\s*([\d.]+);", TOKENS).group(1))
    assert 0.94 <= scale <= 0.96
