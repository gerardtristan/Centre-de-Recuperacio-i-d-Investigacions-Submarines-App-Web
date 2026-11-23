"""T-DX-93 (revisió de DISSENY de la #494): la pàgina dels períodes es titula com l'entrada del
menú, «Tancament de períodes», i no només «Períodes». Només dades inventades."""

from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.models import Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)


def test_the_title_matches_the_menu_entry(login_as, make_admin):  # noqa: F811
    client = login_as(make_admin(Role.Code.TREASURER), AREA_ADMIN)
    response = client.get(reverse("administration:margin_periods"))
    assert "<title>Tancament de períodes · C.R.I.S.</title>" in response.content.decode()
    assert "<h1>Tancament de períodes</h1>" in main_of(response.content.decode())
