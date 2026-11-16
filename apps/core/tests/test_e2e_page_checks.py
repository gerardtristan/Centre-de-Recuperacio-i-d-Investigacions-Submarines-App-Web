"""La comprovació del navegador de les e2e (`PageChecks`) amb objectes falsos, sense navegador.

Una consulta automàtica (HTMX, capçalera `X-CRIS-Automatica`) que troba la sessió ja tancada
no és cap error de la pàgina; qualsevol altra resposta 4xx, sí."""

from types import SimpleNamespace

from apps.core.tests.e2e.conftest import PageChecks

URL = "http://localhost:8000/socis/pagaments/6/estat/"
CONSOLE = "Failed to load resource: the server responded with a status of 401 (Unauthorized)"


class FakePage:
    def __init__(self):
        self.handlers = {}

    def on(self, event, handler):
        self.handlers[event] = handler


def response(status, headers):
    return SimpleNamespace(
        status=status, url=URL, request=SimpleNamespace(method="GET", headers=headers)
    )


def console():
    return SimpleNamespace(type="error", text=CONSOLE, location={"url": URL})


def checks_after(status, headers, console_first=False):
    page = FakePage()
    checks = PageChecks(page)
    events = [("response", response(status, headers)), ("console", console())]
    for name, event in reversed(events) if console_first else events:
        page.handlers[name](event)
    return checks.final_problems()


def test_a_denied_automatic_poll_is_not_a_problem_in_either_order():
    automatic = {"x-cris-automatica": "1"}
    assert checks_after(401, automatic) == []
    assert checks_after(401, automatic, console_first=True) == []
    assert checks_after(403, automatic) == []


def test_any_other_denied_request_is_a_problem():
    assert checks_after(401, {}) == [f"401 GET {URL}", f"consola: {CONSOLE}"]
    assert checks_after(500, {"x-cris-automatica": "1"}) == [
        f"500 GET {URL}",
        f"consola: {CONSOLE}",
    ]


# --- Fitxers estàtics avortats en navegar (CI, execució 43907127835) ------------------------

STATIC = "http://localhost:8000/static/js/errata.js"


def failed(url, resource_type, failure="net::ERR_ABORTED"):
    return SimpleNamespace(url=url, method="GET", resource_type=resource_type, failure=failure)


def checks_after_failure(request):
    page = FakePage()
    checks = PageChecks(page)
    page.handlers["requestfailed"](request)
    return checks.final_problems()


def test_a_static_script_aborted_by_navigation_is_not_a_problem():
    for kind in ("script", "stylesheet", "image", "font"):
        assert checks_after_failure(failed(STATIC, kind)) == []


def test_a_missing_static_file_is_still_a_problem():
    page = FakePage()
    checks = PageChecks(page)
    page.handlers["response"](
        SimpleNamespace(status=404, url=STATIC, request=SimpleNamespace(method="GET", headers={}))
    )
    assert checks.final_problems() == [f"404 GET {STATIC}"]


def test_an_aborted_fetch_or_another_failure_is_still_a_problem():
    fetch = failed("http://localhost:8000/socis/pagaments/6/estat/", "fetch")
    assert checks_after_failure(fetch) == [f"petició fallida: GET {fetch.url} (net::ERR_ABORTED)"]
    xhr_on_static = failed(STATIC, "xhr")
    assert checks_after_failure(xhr_on_static) != []
    refused = failed(STATIC, "script", failure="net::ERR_CONNECTION_REFUSED")
    assert checks_after_failure(refused) != []
