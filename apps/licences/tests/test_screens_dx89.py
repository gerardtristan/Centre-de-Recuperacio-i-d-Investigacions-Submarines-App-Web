"""T-DX-89 (revisió de DISSENY de les vistes v2 i v3 del 06): a «Tipus i preus», la cel·la
d'accions no porta l'etiqueta «Acció» buida i només hi ha un botó principal (regla D19); a «La meva
llicència», els preus es llegeixen com les dades del perfil (`dades-soci`), alineats amb el
formulari, i no amb la llista d'historial. Només dades inventades."""

from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.models import Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .test_personal_views import client_of, member, priced  # noqa: F401 (fixtures)


def test_prices_actions_cell_and_one_main_button(login_as, make_admin, annual):  # noqa: F811
    client = login_as(make_admin(Role.Code.TREASURER), AREA_ADMIN)
    html = main_of(client.get(reverse("administration:licences_prices")).content.decode())
    assert 'data-etiqueta="Acció"' not in html
    assert html.count('<td class="cel-accions">') == 1
    assert '<span class="visualment-amagat">Accions</span>' in html
    assert html.count("boto-principal") == 1


def test_my_licence_prices_read_as_data(client_of, member, priced):  # noqa: F811
    _account, client = client_of()
    html = main_of(client.get(reverse("licences:mine")).content.decode())
    assert 'class="historial"' not in html
    assert '<dl class="dades-soci">' in html
    assert "<dt>Aficionat" in html and '<dd><span class="import">90,00 €</span></dd>' in html
