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
