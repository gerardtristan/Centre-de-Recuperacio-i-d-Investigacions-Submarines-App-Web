"""T-DX-91: la configuració de proves no encén les pantalles «En construcció» encara que el `.env`
local (o l'entorn) ho faci. Les proves passen igual en local i al CI; la que vol les pantalles
encén `SHOW_UNDER_CONSTRUCTION` ella mateixa (`settings` o `override_settings`)."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CODE = "from django.conf import settings; print(settings.SHOW_UNDER_CONSTRUCTION)"


def test_the_local_environment_does_not_turn_on_the_screens_under_construction():
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings.test",
        "SHOW_UNDER_CONSTRUCTION": "1",
    }
    done = subprocess.run(  # noqa: S603 (ordre fixa de la prova)
        [sys.executable, "-c", CODE], env=env, cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().splitlines()[-1] == "False"
