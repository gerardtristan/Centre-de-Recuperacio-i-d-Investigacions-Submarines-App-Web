"""T-DX-88: al llistat de llicències, la cel·la d'accions no porta etiqueta («Acció» buida a 390
px a les fitxes sense cap acció), la columna té el nom «Accions» només per al lector de pantalla,
com la resta de llistats d'administració (`members/fees.html`), i l'únic botó principal és el del
fitxer per a la federació (regla D19), no «Filtra». Només dades inventades."""

from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.models import Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)


def test_the_actions_cell_has_no_visible_label(login_as, make_admin, make_licence, make_person):  # noqa: F811
    make_licence(status="paid", person=make_person("Anna", "Vila"))
    make_licence(status="requested", person=make_person("Pere", "Roca"))
    client = login_as(make_admin(Role.Code.SECRETARY), AREA_ADMIN)
    html = main_of(client.get(reverse("administration:licences")).content.decode())
    assert 'data-etiqueta="Acció"' not in html
    assert html.count('<td class="cel-accions">') == 2
    assert '<span class="visualment-amagat">Accions</span>' in html
    assert html.count("boto-principal") == 1
    assert '<button class="boto" type="submit">Filtra</button>' in html
