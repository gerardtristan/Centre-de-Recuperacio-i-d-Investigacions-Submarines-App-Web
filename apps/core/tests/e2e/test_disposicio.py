"""Disposició a l'escriptori (T-DX-57; sistema de disseny §5.3): a 1280 px les pantalles aprofiten
l'amplada; l'entrada i les pàgines d'error es queden estretes i centrades; a 390 px, com ara.
Les tasques que redistribueixen cada pantalla (T-DX-58 en endavant) hi afegeixen els seus casos."""

import pytest
from django.urls import reverse

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e

WIDTH_JS = "() => document.getElementById('contingut').getBoundingClientRect().width"
OVERFLOW_JS = "() => document.documentElement.scrollWidth - window.innerWidth"


def test_admin_lists_use_the_width_and_login_stays_narrow(page, live_server):
    base = live_server.url
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(f"{base}/entrar/")
    assert page.evaluate(WIDTH_JS) <= 28 * 16 + 1  # cos-estret
    treasurer = make_admin("tresoreria.prova", "administrator", "treasurer")
    login_admin(page, base, treasurer.login)
    for name in ("administration:members_list", "administration:payments_list"):
        page.goto(f"{base}{reverse(name)}")
        assert page.evaluate(WIDTH_JS) > 1000, name  # abans, 960 px
        assert page.evaluate(OVERFLOW_JS) <= 0, name
    for width in (390, 320):
        page.set_viewport_size({"width": width, "height": 800})
        page.goto(f"{base}{reverse('administration:members_list')}")
        assert page.evaluate(OVERFLOW_JS) <= 0, width


GRID_JS = """(classes) => {
  const g = document.createElement('div');
  g.className = classes;
  g.innerHTML = '<p>a</p><p>b</p>';
  document.getElementById('contingut').append(g);
  const s = getComputedStyle(g);
  const out = [s.gridTemplateColumns.split(' ').length, s.columnGap];
  g.remove();
  return out;
}"""


def test_two_columns_on_tablet_and_proportions_beside_the_sidebar(page, live_server):
    """T-DX-57b: graella-2 fa dues columnes a la tauleta (el cos en fa ~42rem) i les proporcions al
    costat de la barra lateral a 1280 px; la regla dels fills del cos no li treu l'espai."""
    admin = make_admin("admin.graella", "administrator")
    login_admin(page, live_server.url, admin.login)
    page.set_viewport_size({"width": 800, "height": 900})
    page.goto(f"{live_server.url}{reverse('administration:members_list')}")
    assert page.evaluate(GRID_JS, "graella-2")[0] == 2
    page.set_viewport_size({"width": 1024, "height": 900})
    page.goto(f"{live_server.url}{reverse('administration:members_list')}")
    columns, gap = page.evaluate(GRID_JS, "graella-2 graella-5-7")
    assert columns == 2 and gap == "24px", (columns, gap)  # --e-5, no el --e-4 de comptes.css
    page.set_viewport_size({"width": 1280, "height": 900})  # el cos, al costat de la barra: ~59rem
    page.goto(f"{live_server.url}{reverse('administration:members_list')}")
    columns, gap = page.evaluate(GRID_JS, "graella-2 graella-5-7")
    assert columns == 2 and gap == "32px", (columns, gap)  # proporcions 5/7, amb --e-6
    page.set_viewport_size({"width": 390, "height": 900})
    page.goto(f"{live_server.url}{reverse('administration:members_list')}")
    assert page.evaluate(GRID_JS, "graella-2")[0] == 1


# Amplades de la columna esquerra i la dreta d'una graella (els dos primers fills).
COLUMNS_JS = """s => [...document.querySelector(s).children].slice(0, 2)
    .map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.left), r.width]; })"""


def test_member_home_layout(page, live_server, builder, member):
    """T-DX-60: la portada 7/5 i la part de baix 8/4 a l'escriptori; dues columnes iguals que no
    es toquen a la tauleta; una a sota de l'altra al mòbil; res de costat a 320 px."""
    base = live_server.url
    account = builder.personal(member.person)
    page.goto(f"{base}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(builder.password)
    page.get_by_role("button", name="Entrar").click()
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(f"{base}/")
    (left, right) = page.evaluate(COLUMNS_JS, ".inici-portada")
    assert right[0] > left[0] and abs(left[1] / right[1] - 7 / 5) < 0.1, (left, right)
    (left, right) = page.evaluate(COLUMNS_JS, ".inici-graella")
    assert right[0] > left[0] and abs(left[1] / right[1] - 8 / 4) < 0.15, (left, right)
    page.set_viewport_size({"width": 800, "height": 900})
    (left, right) = page.evaluate(COLUMNS_JS, ".inici-portada")
    assert abs(left[1] - right[1]) < 2 and right[0] - (left[0] + left[1]) >= 24, (left, right)
    page.set_viewport_size({"width": 390, "height": 800})
    (left, right) = page.evaluate(COLUMNS_JS, ".inici-portada")
    assert left[0] == right[0], (left, right)  # l'una a sota de l'altra
    page.set_viewport_size({"width": 320, "height": 800})
    assert page.evaluate(OVERFLOW_JS) <= 0
