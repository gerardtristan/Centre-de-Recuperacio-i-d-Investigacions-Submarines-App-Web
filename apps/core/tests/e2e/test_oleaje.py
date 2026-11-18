"""Oleaje a la portada de l'àrea del soci (T-DX-17 i T-DX-60): la capçalera amb la vora en ona i, a
sota, sobre el fons de la pàgina, la quota i el carnet en petit; la franja de pendents només si n'hi
ha. El contrast del text de l'inici és de 4,5:1 o més als dos temes."""

import pytest
from playwright.sync_api import expect

from conftest import PASSWORD

from .conftest import CAPTURES, settle

pytestmark = pytest.mark.e2e


# Contrast mínim del text de l'inici (fora del degradat): el color del text contra el fons opac
# més proper, compost amb les capes semitransparents. El canvas converteix qualsevol color CSS
# (oklch, color-mix…) a sRGB.
MIN_CONTRAST_JS = """() => {
  const ctx = document.createElement('canvas').getContext('2d', {willReadFrequently: true});
  const rgba = c => { ctx.clearRect(0, 0, 1, 1); ctx.fillStyle = '#000'; ctx.fillStyle = c;
    ctx.fillRect(0, 0, 1, 1); const d = ctx.getImageData(0, 0, 1, 1).data;
    return [d[0], d[1], d[2], d[3] / 255]; };
  const over = (top, under) => top.slice(0, 3).map((v, i) => v * top[3] + under[i] * (1 - top[3]));
  const lum = c => { const [r, g, b] = c.map(v => { v /= 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const background = el => { const layers = [];
    for (let e = el; e; e = e.parentElement) { const c = rgba(getComputedStyle(e).backgroundColor);
      if (c[3] > 0) { layers.push(c); if (c[3] === 1) break; } }
    let base = [255, 255, 255];
    for (const c of layers.reverse()) base = over(c, base);
    return base; };
  let worst = 99, where = '';
  const roots = document.querySelectorAll('.inici-portada, .franja-estat, .inici-graella');
  for (const root of roots) for (const el of root.querySelectorAll('*')) {
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!own || el.closest('.visualment-amagat, [aria-hidden="true"]')) continue;
    const fg = rgba(getComputedStyle(el).color), bg = background(el);
    const [a, b] = [lum(over(fg, bg)), lum(bg)].sort((x, y) => y - x);
    const ratio = (a + 0.05) / (b + 0.05);
    if (ratio < worst) {
      worst = ratio; where = el.tagName + ' ' + el.textContent.trim().slice(0, 30);
    }
  }
  return [Math.round(worst * 100) / 100, where];
}"""


def all_widths(page, request, name):
    """T-DX-60: l'inici a totes les amplades del programa de l'escriptori, en clar i en fosc, amb
    el contrast mínim del text (4,5:1) a cada combinació; les xifres van a `contrast.txt`."""
    figures = []
    for width in (1280, 1024, 800, 390, 320):
        page.set_viewport_size({"width": width, "height": 900})
        for theme in ("light", "dark"):
            page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
            page.wait_for_timeout(300)
            settle(page)
            suffix = "-fosc" if theme == "dark" else ""
            path = CAPTURES / request.node.name / f"{name}-{width}{suffix}.png"
            page.screenshot(path=path, full_page=True)
            ratio, where = page.evaluate(MIN_CONTRAST_JS)
            figures.append(f"{name} {width} {theme}: {ratio} ({where})")
            assert ratio >= 4.5, figures[-1]
    (CAPTURES / request.node.name / "contrast.txt").write_text("\n".join(figures), "utf-8")
    page.evaluate("document.documentElement.removeAttribute('data-theme')")
    page.set_viewport_size({"width": 1280, "height": 900})


def test_member_home_has_the_wave_header_and_the_fee_block(
    page, live_server, builder, member, review, page_checks, request
):
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}/")
    portada = page.locator(".oleaje-portada")
    expect(portada.locator("svg.oleaje-vora")).to_be_attached()
    quota = page.locator(".inici-quota")
    expect(quota.get_by_role("heading", name="La teva quota")).to_be_visible()
    expect(quota.get_by_text("Al dia")).to_be_visible()
    expect(quota.get_by_role("link", name="El meu carnet")).to_be_visible()
    card = page.locator(".inici-carnet")
    expect(card.get_by_role("heading", name="El teu carnet")).to_be_visible()
    # Fora del degradat (decisió del propietari): la quota i el carnet, sota la portada.
    assert portada.locator(".inici-quota, .inici-carnet").count() == 0
    expect(page.locator(".franja-estat")).to_have_count(0)
    # Sense animació d'entrada (D20, B10): la quota ja és al seu lloc.
    assert quota.evaluate("e => e.getAnimations().length") == 0
    review("portada-oleaje")
    all_widths(page, request, "inici-al-dia")


def test_a_pending_fee_shows_the_flat_strip_with_pay_now(
    page, live_server, builder, review, page_checks, request
):
    member = builder.approve(
        builder.submit(
            "Marta",
            "Pendent Inventada",
            "marta.pendent@example.org",
            builder.born(40),
            builder.full,
            privacy=True,
            membership_terms=True,
        )
    )
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}/")
    strip = page.locator(".franja-estat")
    expect(strip).to_have_attribute("role", "status")
    expect(strip).to_contain_text("1 pagament pendent")
    pay = strip.get_by_role("link", name="Paga ara")
    assert pay.bounding_box()["height"] >= 56  # §6.5: «Paga ara» de 56 px
    assert page.locator(".boto-principal").count() == 1  # D19
    review("portada-pendent")
    all_widths(page, request, "inici-pendent")
