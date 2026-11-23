"""T-DX-94 (revisió de DISSENY de la #497): després d'inscriure's, el soci arriba a la pantalla de
pagament amb «Inscripció feta. Ara pots pagar-la.» en un avís d'èxit (`avis-ok`), no en un d'error.
La pantalla de pagament pintava tots els missatges com a error. Només dades inventades."""

import html

import pytest

from apps.accounts.security import AREA_PERSONAL
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_member, an_open_outing
from .test_member_enrolment_views import manager, url  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db


def test_the_enrolment_message_is_a_success_on_the_payment_page(login_as, manager):  # noqa: F811
    outing = an_open_outing(manager, price_member_cents=4500)
    client = login_as(a_member(), AREA_PERSONAL)
    page = html.unescape(client.post(url(outing), follow=True).content.decode())
    text = "Inscripció feta. Ara pots pagar-la."
    assert f'<div class="avis avis-ok" role="status">{text}</div>' in page
    assert f'<div class="avis avis-error" role="alert">{text}</div>' not in page
