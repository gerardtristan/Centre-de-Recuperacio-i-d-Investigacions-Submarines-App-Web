"""El carnet sense connexió en un navegador de debò (T-M01-21; CA-M01-17 i, per la 079,
RN-M01-96 i CA-M01-110): el service worker desa la pàgina del carnet (amb el QR), la mostra sense
connexió amb l'avís «Comprovat per última vegada», i en sortir esborra només la còpia del carnet:
la preferència de tema es conserva.

No substitueix la prova en un mòbil real feta per una persona (instal·lació, iPhone).
"""

import pytest
from playwright.sync_api import expect

from conftest import PASSWORD

pytestmark = pytest.mark.e2e

OFFLINE_ERRORS = ("ERR_INTERNET_DISCONNECTED", "ERR_FAILED", "Failed to load resource")


def login_personal(page, base_url, account):
    page.goto(f"{base_url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()


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

    # El soci tria el tema fosc: és una preferència del dispositiu (localStorage).
    # Clic amb el ratolí al mig de l'opció «Fosc», com faria una persona.
    box = page.locator('.selector-tema label:has(input[value="dark"])').bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    assert page.evaluate("localStorage.getItem('cris-tema')") == "dark"

    page.goto(f"{base}/socis/carnet/")
    page.evaluate("navigator.serviceWorker.ready.then(() => true)")
    page.reload()  # ara la pàgina ja la serveix el service worker, que en desa la còpia
    expect(page.get_by_role("img", name="Codi QR per verificar el carnet")).to_be_visible()
    page.wait_for_function(
        "async () => (await (await caches.open('cris-carnet-v1')).keys()).length === 1"
    )
    assert cached_card(page) == ["/socis/carnet/"]
    expect(page.get_by_text("Sense connexió: aquesta còpia del carnet")).to_be_hidden()

    # Sense connexió (CA-M01-17): surt la còpia, amb l'avís i el QR.
    context.set_offline(True)
    page.reload()
    expect(page.get_by_text("Sense connexió: aquesta còpia del carnet")).to_be_visible()
    expect(page.get_by_text("Comprovat per última vegada:")).to_be_visible()
    expect(page.get_by_role("img", name="Codi QR per verificar el carnet")).to_be_visible()
    expect(page.get_by_text("Pere Prova Inventat")).to_be_visible()
    review("carnet-sense-connexio")
    context.set_offline(False)
    # Torna la connexió: la còpia es recarrega del servidor (decisió 081, punt 15).
    expect(page.get_by_text("Sense connexió: aquesta còpia del carnet")).to_be_hidden()

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
    context.set_offline(True)
    response_failed = False
    try:
        page.goto(f"{base}/socis/carnet/")
    except Exception:  # noqa: BLE001 (el navegador diu que no hi ha connexió)
        response_failed = True
    assert response_failed or "El meu carnet" not in page.content()
    context.set_offline(False)

    # Les peticions fallides mentre no hi havia connexió són les que s'esperaven.
    page_checks.problems[:] = [
        p for p in page_checks.problems if not any(text in p for text in OFFLINE_ERRORS)
    ]


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
    context.set_offline(True)
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
        page.goto(f"{base}/socis/carnet/")
        page.evaluate("navigator.serviceWorker.ready.then(() => true)")
        page.reload()
        page.wait_for_function(
            "async () => (await (await caches.open('cris-carnet-v1')).keys()).length === 1"
        )

    save_copy()
    context.set_offline(True)
    page.reload()
    notice = page.get_by_text("No és una comprovació en temps real de l'estat del soci.")
    expect(notice).to_be_visible()
    expect(page.get_by_text("es mostra com a màxim 30 dies")).to_be_visible()

    # Torna la connexió: la pàgina es recarrega i ja és la del servidor (sense l'avís).
    context.set_offline(False)
    expect(notice).to_be_hidden()

    # 29 dies: encara es mostra; 31 dies: s'esborra i no es mostra.
    _age_the_copy(page, "X-Cris-Copia-Desada", "String(Date.now() - 29 * 86400000)")
    context.set_offline(True)
    page.reload()
    expect(notice).to_be_visible()
    context.set_offline(False)
    page.wait_for_function("navigator.onLine")
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

    page_checks.problems[:] = [
        p for p in page_checks.problems if not any(text in p for text in OFFLINE_ERRORS)
    ]
