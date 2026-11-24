"""T-DX-110 (Camilla al 02, P-94 A): la inscripció del soci porta els passos d'apuntar-se amb la
línia de Tramite (Activitat, Requisits, Confirmació): el pas 2 abans d'inscriure's i el 3 amb el
pagament pendent. Només indica on és: el servidor fa la inscripció. Només dades inventades."""

import re

from apps.accounts.security import AREA_PERSONAL
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import a_member, an_open_outing
from .test_member_enrolment_views import manager, url  # noqa: F401 (fixture)


def current_step(client, activity):
    page = main_of(client.get(url(activity)).content.decode())
    current = r'<li class="tramite-pas es-actual" aria-current="step">(.*?)</li>'
    step = re.search(current, page, re.S)
    return re.sub(r"<[^>]+>", "", step.group(1)).strip() if step else None


def test_the_member_sees_where_she_is(login_as, manager):  # noqa: F811
    outing = an_open_outing(manager, price_member_cents=4500)
    client = login_as(a_member(), AREA_PERSONAL)
    assert current_step(client, outing) == "2Requisits"
    client.post(url(outing))
    assert current_step(client, outing) == "3Confirmació"
