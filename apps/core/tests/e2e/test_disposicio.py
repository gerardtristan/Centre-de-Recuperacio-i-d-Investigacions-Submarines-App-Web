"""Disposició a l'escriptori (T-DX-57; sistema de disseny §5.3): a 1280 px les pantalles aprofiten
l'amplada; l'entrada i les pàgines d'error es queden estretes i centrades; a 390 px, com ara.
Les tasques que redistribueixen cada pantalla (T-DX-58 en endavant) hi afegeixen els seus casos."""

import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.core import audit, charges
from apps.core.models import LegalText
from apps.members.models import Member
from apps.members.tests.test_cards import make_member

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


# T-DX-65: la columna principal d'un formulari i el primer element de la columna lateral (el resum
# d'Errata, si n'hi ha, o l'ajuda): [esquerra, dreta, dalt] i l'amplada de la principal.
FORM_JS = """() => {
  const g = document.querySelector('.lateral-formulari');
  const r = e => {
    const b = e.getBoundingClientRect();
    return [Math.round(b.left), Math.round(b.right), Math.round(b.top)];
  };
  const main = g.querySelector(':scope > .columna-principal');
  const side = g.querySelector(':scope > .errata') || g.querySelector(':scope > .columna-lateral');
  return [r(main), main.getBoundingClientRect().width, r(side)];
}"""
FORM_MAX = 40 * 16 + 1  # --amplada-formulari


def assert_form_layout(page, errata=False):
    """A 1280 px, la columna principal fa com a màxim 40rem i la lateral és al costat, a la mateixa
    alçada; a 390 px, una sola columna (Errata a sobre del formulari, l'ajuda a sota); res de
    costat a 320 px."""
    page.set_viewport_size({"width": 1280, "height": 900})
    main, width, side = page.evaluate(FORM_JS)
    assert width <= FORM_MAX and side[0] >= main[1] and abs(side[2] - main[2]) <= 2, (main, side)
    page.set_viewport_size({"width": 390, "height": 800})
    main, width, side = page.evaluate(FORM_JS)
    assert side[0] == main[0], (main, side)
    assert (side[2] < main[2]) if errata else (side[2] > main[2]), (main, side)
    page.set_viewport_size({"width": 320, "height": 800})
    assert page.evaluate(OVERFLOW_JS) <= 0
    page.set_viewport_size({"width": 1280, "height": 900})


def test_member_forms_and_payment_layout(page, live_server, settings, builder, member):
    """T-DX-65: el perfil i el mandat (amb errors: Errata al costat, primer al DOM i amb el focus)
    a 40rem amb la columna lateral; la pantalla de pagament, amb els passos de Tramite al costat."""
    settings.MANDATE_SIGNING_ENABLED = True
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    LegalText.objects.create(kind="sepa_mandate", version=1, content="Text del mandat (prova).")
    charge = charges.create_charge(
        member.person,
        kind="fee",
        amount_cents=9000,
        concept="Quota de prova",
        origin="proves",
        by=audit.system("proves-e2e"),
    )
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
    expect(page).not_to_have_url(re.compile("/entrar/"))

    page.goto(f"{base}{reverse('members:profile')}")
    expect(page.locator(".boto-principal")).to_have_count(1)  # D19
    assert_form_layout(page)

    page.goto(f"{base}{reverse('payments:mandate')}")
    page.get_by_role("button", name="Signa el mandat").click()
    expect(page.locator("[data-errata]")).to_be_focused()
    assert page.evaluate(
        "() => !!(document.querySelector('[data-errata]').compareDocumentPosition("
        "document.getElementById('canvia')) & Node.DOCUMENT_POSITION_FOLLOWING)"
    )
    assert_form_layout(page, errata=True)

    page.goto(f"{base}{reverse('payments:charge', args=[charge.pk])}")
    steps = page.locator("#estat-pagament > .tramite")
    expect(steps).to_be_visible()
    first = page.locator("#estat-pagament > :not(.tramite)").first
    box, pay = steps.bounding_box(), first.bounding_box()
    assert box["x"] >= pay["x"] + pay["width"] and pay["width"] <= FORM_MAX, (box, pay)
    page.set_viewport_size({"width": 390, "height": 800})
    box, pay = steps.bounding_box(), first.bounding_box()
    assert box["x"] == pay["x"] and box["y"] < pay["y"], (box, pay)  # a sobre, com abans
    page.set_viewport_size({"width": 320, "height": 800})
    assert page.evaluate(OVERFLOW_JS) <= 0


STICKY_JS = "() => getComputedStyle(document.querySelector('.taula thead th')).position"
FILTER_COLUMNS_JS = (
    "() => getComputedStyle(document.querySelector('.barra-filtres'))"
    ".gridTemplateColumns.split(' ').length"
)


def test_admin_lists_on_the_desktop(page, live_server):
    """T-DX-66 (PR 7b): els llistats de l'administració a 1280 px fan més de 1000 px, tenen els
    filtres en una fila amb els botons al costat i la capçalera de la taula fixa; la fila sencera
    porta a la fitxa (és el mateix enllaç); a 390 px la taula és apilada i a 320 no desborda."""
    for n in (1, 2, 3):
        make_member(first=f"Fila{n}", number=40 + n, document=f"0000004{n}A")
    treasurer = make_admin("tresoreria.llistats", "administrator", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    page.set_viewport_size({"width": 1280, "height": 900})
    for name in (
        "administration:members_list",
        "administration:fees",
        "administration:treasury_movements",
    ):
        page.goto(f"{live_server.url}{reverse(name)}")
        assert page.evaluate(WIDTH_JS) > 1000, name
        assert page.evaluate(OVERFLOW_JS) <= 0, name
        assert page.evaluate(FILTER_COLUMNS_JS) == 2, name  # els camps i, al costat, els botons
        expect(page.locator(".capcalera-pagina h1")).to_be_visible()

    page.goto(f"{live_server.url}{reverse('administration:members_list')}")
    assert page.evaluate(STICKY_JS) == "sticky"
    row = page.locator("tbody tr").filter(has_text="Fila2")
    box = row.locator("td").first.bounding_box()  # la cel·la del tipus: no és cap enllaç
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    member = Member.objects.get(member_number=42)
    expect(page).to_have_url(
        f"{live_server.url}{reverse('administration:member_detail', args=[member.pk])}"
    )

    page.set_viewport_size({"width": 390, "height": 800})
    page.goto(f"{live_server.url}{reverse('administration:members_list')}")
    assert page.evaluate(STICKY_JS) != "sticky"  # taula apilada, amb la capçalera amagada
    assert page.evaluate(FILTER_COLUMNS_JS) == 1
    expect(page.locator("tbody tr").first).to_have_css("display", "block")
    page.set_viewport_size({"width": 320, "height": 800})
    for name in ("administration:members_list", "administration:treasury_movements"):
        page.goto(f"{live_server.url}{reverse(name)}")
        assert page.evaluate(OVERFLOW_JS) <= 0, name


def test_admin_forms_layout(page, live_server, secretary, member):
    """T-DX-65: l'alta presencial (amb errors) i l'edició de les dades d'un soci, a 40rem amb la
    columna lateral a l'escriptori."""
    base = live_server.url
    login_admin(page, base, secretary.login)
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(f"{base}{reverse('administration:join_in_person')}")
    page.get_by_role("button", name="Desa la sol·licitud").click()
    expect(page.locator("[data-errata]")).to_be_focused()
    assert_form_layout(page, errata=True)

    page.goto(f"{base}{reverse('administration:member_edit', args=[member.pk])}")
    expect(page.get_by_role("heading", level=1, name="Edita les dades")).to_be_visible()
    assert_form_layout(page)
