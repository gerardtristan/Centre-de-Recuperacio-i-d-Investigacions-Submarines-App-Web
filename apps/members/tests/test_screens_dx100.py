"""T-DX-100: l'entrada del menú i la pàgina de la confirmació en bloc del 01 (T-M01-36) es diuen
«Llicències de la fitxa per confirmar», perquè no es confonguin amb «Llicències per
confirmar» del 06 (licences_unconfirmed). Totes dues són vigents fins al pas únic (T-M06-14;
resposta B del pilot). Només dades inventades."""

from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.models import Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

NAME = "Llicències de la fitxa per confirmar"


def test_the_01_screen_has_its_own_name(login_as, make_admin):  # noqa: F811
    client = login_as(make_admin(Role.Code.SECRETARY), AREA_ADMIN)
    home = client.get(reverse("administration:home")).content.decode()
    assert f">{NAME}</a>" in home and "Llicències pendents de confirmar" not in home
    page = client.get(reverse("administration:licence_bulk_confirm")).content.decode()
    assert f"<title>{NAME} · C.R.I.S.</title>" in page
    assert f"<h1>{NAME}</h1>" in main_of(page)
