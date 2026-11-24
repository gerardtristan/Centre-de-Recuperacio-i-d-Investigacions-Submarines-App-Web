"""T-DX-98 (revisió de DISSENY de la #530): a «Llicències per confirmar», «Confirma…» va a la cel·la
d'accions (`cel-accions`), amb la capçalera amagada i sense l'etiqueta «Acció» a la taula apilada
del mòbil (T-DX-88). Només dades inventades."""

from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .test_confirm_06 import pending, secretary  # noqa: F401 (fixture)


def test_the_confirm_link_is_in_the_actions_cell(login_as, secretary, pending):  # noqa: F811
    (licence,) = pending()
    client = login_as(secretary, AREA_ADMIN)
    html = main_of(client.get(reverse("administration:licences_unconfirmed")).content.decode())
    url = reverse("administration:licences_confirm", args=[licence.pk])
    assert f'<td class="cel-accions"><a href="{url}">' in html
    assert 'data-etiqueta="Acció"' not in html
    assert '<span class="visualment-amagat">Accions</span>' in html
