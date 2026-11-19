"""El carnet sense connexió en un navegador de debò (T-M01-21; CA-M01-17 i, per la 079,
RN-M01-96 i CA-M01-110): el service worker desa la pàgina del carnet (amb el QR), la mostra sense
connexió amb l'avís «Comprovat per última vegada», i en sortir esborra només la còpia del carnet:
la preferència de tema es conserva.

No substitueix la prova en un mòbil real feta per una persona (instal·lació, iPhone).
"""

import time
from types import SimpleNamespace

import pytest
from playwright.sync_api import expect

from conftest import PASSWORD

from .conftest import PageChecks

pytestmark = pytest.mark.e2e

OFFLINE_ERRORS = ("ERR_INTERNET_DISCONNECTED", "ERR_FAILED", "Failed to load resource")


class _Page:
    """Només recull els gestors d'esdeveniments que `PageChecks` registra."""

    def __init__(self):
        self.handlers = {}

    def on(self, event, handler):
        self.handlers[event] = handler


def test_offline_errors_are_ignored_also_when_chromium_logs_them_to_the_console():
    """P-315: Chromium, sense connexió, escriu de vegades a la consola «Failed to load resource:
    net::ERR_INTERNET_DISCONNECTED». Aquest missatge no va a `problems` sinó a la llista de la
    consola, que es resol en acabar la prova: treure'ls de `problems` no n'hi havia prou, i la
    prova de la 081 fallava segons com queia el temps. Sense navegador: és determinista."""
    page = _Page()
    checks = PageChecks(page)
    page.handlers["console"](
        SimpleNamespace(
            type="error",
            text="Failed to load resource: net::ERR_INTERNET_DISCONNECTED",
            location={"url": "http://localhost/socis/carnet/"},
        )
    )
    checks.ignore(*OFFLINE_ERRORS)
    assert checks.final_problems() == []
    # Un missatge que arriba després (en acabar la prova) també s'ignora.
    page.handlers["pageerror"]("TypeError: ERR_FAILED (prova)")
    assert checks.final_problems() == []
    # La resta d'errors continuen comptant.
    page.handlers["pageerror"]("TypeError: un altre error")
    assert checks.final_problems() == ["JavaScript: TypeError: un altre error"]


def login_personal(page, base_url, account):
    page.goto(f"{base_url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()


def go_offline(page, context, base):
    """Posa el navegador sense connexió i comprova que ja ho està també per al service worker.

    L'emulació de Playwright no sempre s'aplica a la primera petició que fa el service worker:
    dins la suite sencera, alguna vegada la petició ha sortit a la xarxa i ha tornat la pàgina
    del servidor. És un límit de l'eina de proves, no de la web: sense xarxa de debò el servidor
    no pot respondre. Per això es comprova amb l'inici, que el service worker demana a la xarxa
    sense desar res: si falla o surt la còpia, ja no hi ha connexió; si surt la pàgina del
    servidor, es torna a provar. Així la còpia del carnet no es torna a desar per error."""
    context.set_offline(True)
    deadline = time.monotonic() + 15
    while True:
        try:
            page.goto(f"{base}/")
        except Exception:  # noqa: BLE001 (sense xarxa i sense còpia: el navegador ho diu)
            return
        if page.locator("[data-sense-connexio]:not([hidden])").count():
            return  # la còpia del carnet: el service worker no ha arribat al servidor
        assert time.monotonic() < deadline, "l'emulació de «sense connexió» no s'ha aplicat"
        page.wait_for_timeout(250)


COPY_STAMP = (
    "async () => { const r = await (await caches.open('cris-carnet-v1')).match('/socis/carnet/');"
    " return r ? r.headers.get('X-Cris-Copia-Desada') : null; }"
)


def wait_for_a_copy_saved_since(page, since):
    """Espera que el service worker hagi acabat de desar una còpia posterior a `since` (ms del
    navegador) i que ja no en desi cap altra: la pàgina es pot haver demanat dues vegades."""
    deadline = time.monotonic() + 15
    while True:
        first = page.evaluate(COPY_STAMP)
        page.wait_for_timeout(400)
        if first and first == page.evaluate(COPY_STAMP) and int(first) >= since:
            return
        assert time.monotonic() < deadline, "el service worker no ha desat la còpia del carnet"


def cached_card(page):
    return page.evaluate(
        "async () => { const c = await caches.open('cris-carnet-v1');"
        " return (await c.keys()).map(r => new URL(r.url).pathname); }"
    )


def test_offline_card_copy_and_logout_keeps_the_theme(
    page, context, live_server, builder, member, review, page_checks
):
    base = live_server.url.replace("127.0.0.1", "localhost")  # context segur per al service worker
    account = builder.personal(member.person)
    login_personal(page, base, account)

    # El soci tria el tema fosc a la configuració del compte (T-DX-05b): és una preferència del
    # dispositiu (localStorage).
    page.goto(f"{base}/compte/seguretat/")
    # Clic amb el ratolí al mig de l'opció «Fosc», com faria una persona.
    dark = page.locator('.selector-tema label:has(input[value="dark"])')
    dark.scroll_into_view_if_needed()
    box = dark.bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    assert page.evaluate("localStorage.getItem('cris-tema')") == "dark"

    page.goto(f"{base}/socis/carnet/")
    page.evaluate("navigator.serviceWorker.ready.then(() => true)")
    page.reload()  # ara la pàgina ja la serveix el service worker, que en desa la còpia
    page.get_by_role("button", name="Mostra el QR").click()  # T-DX-61: el QR és al darrere
    expect(page.get_by_role("img", name="Codi QR per verificar el carnet")).to_be_visible()
    page.wait_for_function(
        "async () => (await (await caches.open('cris-carnet-v1')).keys()).length === 1"
    )
    assert cached_card(page) == ["/socis/carnet/"]
    expect(page.get_by_text("Sense connexió: aquesta còpia del carnet")).to_be_hidden(timeout=15000)

    # Sense connexió (CA-M01-17): surt la còpia, amb l'avís i el QR.
    go_offline(page, context, base)
    # Amb #qr la còpia s'obre pel darrere: el gir (carnet.js, desat) també funciona sense connexió.
    page.goto(f"{base}/socis/carnet/#qr")
    expect(page.get_by_text("Sense connexió: aquesta còpia del carnet")).to_be_visible()
    expect(page.get_by_text("Comprovat per última vegada:")).to_be_visible()
    expect(page.get_by_role("img", name="Codi QR per verificar el carnet")).to_be_visible()
    expect(page.get_by_text("Pere Prova Inventat")).to_be_visible()
    review("carnet-sense-connexio")
    context.set_offline(False)
    # Torna la connexió: la còpia es recarrega del servidor (decisió 081, punt 15).
    expect(page.get_by_text("Sense connexió: aquesta còpia del carnet")).to_be_hidden(timeout=15000)

    # En sortir (CA-M01-110): s'esborra la còpia del carnet i el tema es conserva.
    page.goto(f"{base}/")
    page.get_by_role("button", name="Surt").click()
    expect(page).to_have_url(f"{base}/entrar/")
    page.wait_for_function(
        "async () => (await (await caches.open('cris-carnet-v1')).keys()).length === 0"
    )
    assert cached_card(page) == []
    assert page.evaluate("localStorage.getItem('cris-tema')") == "dark"
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "dark"

    # I sense connexió ja no hi ha cap carnet per mostrar.
    go_offline(page, context, base)
    response_failed = False
    try:
        page.goto(f"{base}/socis/carnet/")
    except Exception:  # noqa: BLE001 (el navegador diu que no hi ha connexió)
        response_failed = True
    assert response_failed or "El meu carnet" not in page.content()
    context.set_offline(False)

    # Les peticions fallides mentre no hi havia connexió són les que s'esperaven.
    page_checks.ignore(*OFFLINE_ERRORS)


def _age_the_copy(page, header, value_js):
    """Canvia una capçalera de la còpia desada, com si hagués passat el temps."""
    page.evaluate(
        "async ([name, value]) => { const c = await caches.open('cris-carnet-v1');"
        " const r = await c.match('/socis/carnet/'); const h = new Headers(r.headers);"
        " h.set(name, value); await c.put('/socis/carnet/', new Response(await r.text(),"
        " { headers: h })); }",
        [header, page.evaluate(value_js)],
    )


def _offline_card_is_not_shown(page, context, base):
    go_offline(page, context, base)
    failed = False
    try:
        page.goto(f"{base}/socis/carnet/")
    except Exception:  # noqa: BLE001 (el navegador diu que no hi ha connexió)
        failed = True
    assert failed or "Sense connexió: aquesta còpia" not in page.content()
    context.set_offline(False)
    page.goto(f"{base}/")  # fora de la pàgina d'error del navegador, on no hi ha `caches`
    page.wait_for_function(
        "async () => (await (await caches.open('cris-carnet-v1')).keys()).length === 0"
    )


def test_081_copy_expires_after_30_days_or_the_valid_until_and_refreshes_online(
    page, context, live_server, builder, member, page_checks
):
    """Decisió 081, punt 15: la còpia es mostra com a màxim 30 dies, mai després del «vàlid fins
    al», diu que no és una comprovació en temps real i, quan torna la connexió, la pàgina es
    torna a carregar del servidor."""
    base = live_server.url.replace("127.0.0.1", "localhost")
    login_personal(page, base, builder.personal(member.person))

    def save_copy():
        page.goto(f"{base}/socis/carnet/#qr")  # T-DX-61: amb #qr, el carnet mostra el QR
        page.evaluate("navigator.serviceWorker.ready.then(() => true)")
        since = page.evaluate("Date.now()")
        page.reload()  # ara segur que la serveix el service worker
        expect(page.get_by_role("img", name="Codi QR per verificar el carnet")).to_be_visible()
        wait_for_a_copy_saved_since(page, since)

    def back_online():
        """Torna la connexió: quan el servidor respon, la pàgina es recarrega, ja és la del
        servidor (sense l'avís) i el service worker en desa una còpia nova."""
        since = page.evaluate("Date.now()")
        context.set_offline(False)
        expect(notice).to_be_hidden(timeout=15000)
        wait_for_a_copy_saved_since(page, since)

    notice = page.get_by_text("No és una comprovació en temps real de l'estat del soci.")
    save_copy()
    go_offline(page, context, base)
    # Amb #qr la còpia s'obre pel darrere: el gir (carnet.js, desat) també funciona sense connexió.
    page.goto(f"{base}/socis/carnet/#qr")
    expect(notice).to_be_visible()
    expect(page.get_by_text("es mostra com a màxim 30 dies")).to_be_visible()
    back_online()

    # 29 dies: encara es mostra; 31 dies: s'esborra i no es mostra.
    _age_the_copy(page, "X-Cris-Copia-Desada", "String(Date.now() - 29 * 86400000)")
    go_offline(page, context, base)
    # Amb #qr la còpia s'obre pel darrere: el gir (carnet.js, desat) també funciona sense connexió.
    page.goto(f"{base}/socis/carnet/#qr")
    expect(notice).to_be_visible()
    back_online()
    _age_the_copy(page, "X-Cris-Copia-Desada", "String(Date.now() - 31 * 86400000)")
    _offline_card_is_not_shown(page, context, base)

    # El «vàlid fins al» ja ha passat: tampoc no es mostra, encara que la còpia sigui d'avui.
    save_copy()
    _age_the_copy(
        page,
        "X-Cris-Valid-Fins",
        "(() => { const d = new Date(Date.now() - 86400000);"
        " return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-'"
        " + String(d.getDate()).padStart(2, '0'); })()",
    )
    _offline_card_is_not_shown(page, context, base)

    page_checks.ignore(*OFFLINE_ERRORS)
