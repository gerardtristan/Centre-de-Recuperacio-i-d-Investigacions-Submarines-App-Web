"""Les persones que fan classe a les proves del 02 no són sòcies ni tenen llicència: totes les
proves van amb el mode «avís» de RN-M02-26 (VC-46), tret de les de `test_instructor_requirements`,
que posen el mode que proven."""

import pytest

from apps.activities.sessions import INSTRUCTOR_MODE_KEY
from apps.core import business_settings


@pytest.fixture(autouse=True)
def instructors_in_warn_mode(monkeypatch):
    real = business_settings.get
    monkeypatch.setattr(
        business_settings, "get",
        lambda key, at=None: "warn" if key == INSTRUCTOR_MODE_KEY else real(key, at),
    )  # fmt: skip
