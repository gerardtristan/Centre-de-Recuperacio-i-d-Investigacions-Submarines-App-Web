"""T-DX-24: la inscripció (Camilla) ve d'una clínica; no mostra cap dada de salut."""

import pytest
from django.test import override_settings
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL

pytestmark = pytest.mark.django_db

HEALTH_WORDS = (
    "salut",
    "mèdic",
    "metge",
    "al·lèrg",
    "malalt",
    "medicació",
    "especialitat",
    "pacient",
)


@override_settings(SHOW_UNDER_CONSTRUCTION=True)
def test_the_enrolment_screen_shows_no_health_field(login_as, personal_account):
    client = login_as(personal_account, AREA_PERSONAL)
    html = client.get(reverse("previews:inscripcio")).content.decode().lower()
    assert not [word for word in HEALTH_WORDS if word in html]
