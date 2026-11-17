"""Logotip de la capçalera (T-DX-51; F5 de la revisió de les portes del nivell 2): només es
descarrega el del tema que es veu, ajustat (192 px) i en un format modern; mai els originals.

T-DX-54: a Chromium, Firefox i WebKit (el motor de Safari). Que el logotip amagat no es descarregui
depèn de com cada motor tracta una imatge diferida («lazy») amb display: none, i per això es
prova a tots tres. Cada motor s'obre aquí mateix; la resta de proves no canvia de navegador."""

import os

import pytest
from playwright.sync_api import Error, expect

pytestmark = pytest.mark.e2e

ENGINES = ("chromium", "firefox", "webkit")
CASES = [
    ("light", None, "clar"),
    ("dark", None, "fosc"),
    ("light", "dark", "fosc"),  # el tema triat a mà (tema.js, «cris-tema») guanya al del sistema
    ("dark", "light", "clar"),
]


def launch(playwright, name, scheme):
    """Firefox perd l'emulació de `color_scheme` quan canvia de procés per la capçalera
    Cross-Origin-Opener-Policy de les pàgines (la 00 l'envia): s'hi posa la preferència del
    navegador, com un sistema en fosc de debò."""
    prefs = {"ui.systemUsesDarkTheme": 1 if scheme == "dark" else 0}
    try:
        if name == "firefox":
            return playwright.firefox.launch(firefox_user_prefs=prefs)
        return getattr(playwright, name).launch()
    except Error as error:
        # Al CI hi són sempre (ci.yml). En local, qui només té Chromium no ha de veure-ho fallar:
        # python -m playwright install firefox webkit
        if os.environ.get("CI") or "Executable doesn't exist" not in str(error):
            raise
        pytest.skip(f"{name} de Playwright no és instal·lat en aquest ordinador")


@pytest.mark.parametrize("name", ENGINES)
@pytest.mark.parametrize(("scheme", "saved", "kind"), CASES)
def test_only_the_visible_logo_is_downloaded(playwright, live_server, name, scheme, saved, kind):
    browser = launch(playwright, name, scheme)
    context = browser.new_context(color_scheme=scheme)
    if saved:
        context.add_init_script(f"localStorage.setItem('cris-tema', '{saved}')")
    page = context.new_page()
    seen = []
    page.on("request", lambda r: seen.append(r.url) if "marca/" in r.url else None)
    try:
        page.goto(f"{live_server.url}/entrar/")
        visible = page.locator(".capcalera-compte .marca picture:visible img")
        expect(visible).to_have_count(1)
        page.wait_for_function(
            "() => [...document.querySelectorAll('.marca picture img')]"
            ".some((i) => i.complete && i.naturalWidth > 0)"
        )
        page.wait_for_timeout(300)  # marge per a una segona descàrrega, si n'hi hagués
        assert len(seen) == 1, (name, seen)
        assert f"/img/marca/cris-{kind}-192." in seen[0], (name, seen)
        assert seen[0].endswith((".avif", ".webp")), (name, seen)  # format modern, no el PNG
        assert visible.evaluate("(i) => i.getBoundingClientRect().width") > 0
    finally:
        browser.close()
