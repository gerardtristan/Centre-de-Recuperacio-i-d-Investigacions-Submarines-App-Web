"""Logotip de la capçalera (T-DX-51; F5 de la revisió de les portes del nivell 2): només es
descarrega el del tema que es veu, ajustat (192 px) i en un format modern; mai els originals."""

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


def logo_requests(page, url):
    seen = []
    page.on("request", lambda r: seen.append(r.url) if "marca/" in r.url else None)
    page.goto(url)
    visible = page.locator(".capcalera-compte .marca picture:visible img")
    expect(visible).to_have_count(1)
    page.wait_for_function(
        "() => [...document.querySelectorAll('.marca picture img')]"
        ".some((i) => i.complete && i.naturalWidth > 0)"
    )
    page.wait_for_timeout(300)  # marge per a una segona descàrrega, si n'hi hagués
    return seen, visible


@pytest.mark.parametrize(
    ("scheme", "saved", "kind"),
    [
        ("light", None, "clar"),
        ("dark", None, "fosc"),
        ("light", "dark", "fosc"),
        ("dark", "light", "clar"),
    ],
)
def test_only_the_visible_logo_is_downloaded(page, live_server, scheme, saved, kind):
    page.emulate_media(color_scheme=scheme)
    if saved:  # el tema triat a mà (tema.js, «cris-tema») guanya al del sistema
        page.add_init_script(f"localStorage.setItem('cris-tema', '{saved}')")
    seen, visible = logo_requests(page, f"{live_server.url}/entrar/")
    assert len(seen) == 1, seen
    assert f"/img/marca/cris-{kind}-192." in seen[0], seen
    assert seen[0].endswith((".avif", ".webp")), seen  # Chromium: format modern, no el PNG
    assert "CRIS_" not in seen[0]
    assert visible.evaluate("(i) => i.getBoundingClientRect().width") > 0
