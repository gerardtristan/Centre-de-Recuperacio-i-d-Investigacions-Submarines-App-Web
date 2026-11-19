"""Proves e2e al navegador (T-M00-07): Playwright i `live_server` de pytest-django.

Només dades inventades. Només s'executen amb `pytest -m e2e` (pyproject.toml).

- El servidor en viu té la seva connexió: les dades s'han de confirmar de debò. Per això
  `transactional_db` es redefineix aquí amb la neteja de `CommittedDataTestCase` (esborra les
  files noves), perquè el TRUNCATE de pytest-django xoca amb els disparadors del registre
  d'activitat i esborraria les dades de les migracions.
- `page_checks` fa fallar la prova si hi ha errors a la consola, errors de JavaScript,
  peticions que no arriben o respostes 4xx/5xx que la prova no ha declarat.
- `capture` desa cada pantalla a 1280 i 390 px a `.e2e-captures/<prova>/`, fora de Git.
"""

import os
from pathlib import Path
from urllib.parse import urlparse

import pyotp
import pytest
from django.conf import settings
from django.utils import timezone

from apps.accounts.models import Account, TotpDevice
from apps.accounts.sessions import AUTOMATIC_HEADER
from apps.core import consents
from apps.core.crypto import encrypt
from apps.core.models import AccountRole, Person, Role
from apps.members.demo_data import _Builder
from apps.members.models import MembershipNumberCounter
from conftest import PASSWORD, committed_snapshot, delete_committed_rows

# Chromium dins del paquet de Playwright (a .venv), no a la memòria cau de l'usuari.
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "0")

# El mateix TOTP de proves que `make_admin` (apps/core/tests/conftest.py); no és cap secret.
TOTP_KEY = "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"  # gitleaks:allow (TOTP inventat de les proves)
CAPTURES = Path(settings.BASE_DIR) / ".e2e-captures"
WIDTHS = (1280, 390)
TEXT_KINDS = ("privacy", "membership_terms", "guardian_authorization")


@pytest.fixture(scope="session", autouse=True)
def _async_unsafe_only_in_e2e():
    """Playwright síncron té un bucle d'esdeveniments obert al fil principal i Django hi
    rebutja l'ORM. Només a les e2e (CA-M00-07d)."""
    # shortcut: si les e2e s'executen juntes amb les altres (`-m ""`), queda posat fins al final
    # de la sessió; amb `pytest -m e2e` no n'hi ha cap altra. Les proves síncrones no ho noten.
    previous = os.environ.get("DJANGO_ALLOW_ASYNC_UNSAFE")
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    yield
    if previous is None:
        os.environ.pop("DJANGO_ALLOW_ASYNC_UNSAFE", None)
    else:
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = previous


@pytest.fixture
def transactional_db(_async_unsafe_only_in_e2e, django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        tables, start = committed_snapshot()
        # Les e2e aproven altes de debò i el comptador de números (una fila de les migracions)
        # avança: es torna al valor d'abans, perquè una altra execució amb `--reuse-db` no
        # comenci amb un comptador desfasat.
        counter = MembershipNumberCounter.objects.values_list("last_number", flat=True).first()
        yield
        delete_committed_rows(tables, start)
        if counter is not None:
            MembershipNumberCounter.objects.filter(pk=1).update(last_number=counter)


STATIC_RESOURCE_TYPES = frozenset({"script", "stylesheet", "image", "font"})


class PageChecks:
    def __init__(self, page):
        self.problems = []
        self.expected = set()  # (estat, camí) que la prova espera
        self.downloads = set()  # camins de descàrregues que la prova espera
        # Consultes automàtiques (HTMX cada pocs segons) que han trobat la sessió ja tancada.
        self.automatic_denied = set()
        self._console_resource = []  # (camí, text): es resolen en acabar
        page.on("console", self._console)
        page.on("pageerror", lambda error: self.problems.append(f"JavaScript: {error}"))
        page.on("requestfailed", self._failed)
        page.on("response", self._response)

    def final_problems(self):
        """Els problemes, sense el missatge de consola de les consultes automàtiques denegades
        (Chromium l'escriu a part de la resposta, i pot arribar abans o després)."""
        console = [
            f"consola: {text}"
            for path, text in self._console_resource
            if path not in self.automatic_denied
        ]
        return self.problems + console

    def expect(self, status, path):
        self.expected.add((status, path))

    def expect_download(self, path_prefix):
        """Chromium avorta (`net::ERR_ABORTED`) la navegació que es converteix en una descàrrega:
        no és cap error si la prova l'espera. Només aquest error i només en aquest camí."""
        self.downloads.add(path_prefix)

    def _console(self, message):
        # Chromium també escriu a la consola les respostes 4xx: les que la prova espera no compten.
        path = urlparse((message.location or {}).get("url", "")).path
        declared = message.text.startswith("Failed to load resource") and any(
            path == expected for _, expected in self.expected
        )
        if message.type != "error" or declared:
            return
        if message.text.startswith("Failed to load resource"):
            self._console_resource.append((path, message.text))
        else:
            self.problems.append(f"consola: {message.text}")

    def _failed(self, request):
        path = urlparse(request.url).path
        if request.failure == "net::ERR_ABORTED" and any(
            path.startswith(prefix) for prefix in self.downloads
        ):
            return
        # Un fitxer estàtic (guió, full d'estil, imatge, lletra) que la pàgina encara carregava
        # quan la prova n'ha obert una altra: Chromium l'avorta. No és cap error de la pàgina, i
        # un fitxer que falta surt com a 404 a `_response`, mai aquí. Una petició de dades (fetch
        # o XHR, HTMX) avortada continua comptant.
        if (
            request.failure == "net::ERR_ABORTED"
            and request.resource_type in STATIC_RESOURCE_TYPES
            and path.startswith("/static/")
        ):
            return
        self.problems.append(f"petició fallida: {request.method} {request.url} ({request.failure})")

    def _response(self, response):
        path = urlparse(response.url).path
        ((header, value),) = AUTOMATIC_HEADER.items()
        if response.status in (401, 403) and response.request.headers.get(header.lower()) == value:
            # Una consulta automàtica que surt quan la sessió s'acaba (en sortir, en canviar de
            # compte o en acabar la prova) no és cap error de la pàgina. Si la prova en depèn,
            # el seu `expect` ja falla.
            self.automatic_denied.add(path)
            return
        if response.status >= 400 and (response.status, path) not in self.expected:
            self.problems.append(f"{response.status} {response.request.method} {response.url}")


_warmed = []


@pytest.fixture(autouse=True)
def _warm_first_load(request):
    """P-313: la primera càrrega d'una tanda arrenca en fred el servidor i el navegador (9 s amb
    la memòria cau del disc buida, 0,3 s les següents) i, amb la màquina carregada, passava dels
    30 s de Playwright. Abans de la primera prova amb `live_server`, una visita d'escalfament a
    `/entrar/` en un context a part, una sola vegada per tanda. És l'únic temps llarg: els de les
    proves no canvien."""
    if _warmed or "live_server" not in request.fixturenames:
        return
    request.getfixturevalue("transactional_db")  # el servidor en viu consulta la base de dades
    url = request.getfixturevalue("live_server").url
    context = request.getfixturevalue("browser").new_context()
    context.new_page().goto(f"{url}/entrar/", timeout=120_000)
    context.close()
    _warmed.append(url)


@pytest.fixture(autouse=True)
def page_checks(page):
    checks = PageChecks(page)
    yield checks
    problems = checks.final_problems()
    assert not problems, "Problemes al navegador:\n" + "\n".join(problems)


def settle(page):
    """Espera que acabin les animacions de la pàgina (el rebut que surt, el segell…) abans de la
    captura. Totes són finites (D20: l'única contínua seria Oleaje, que s'atura sola en proves)."""
    page.evaluate(
        "() => Promise.all(document.getAnimations()"
        ".filter(a => a.effect?.getTiming().iterations !== Infinity).map(a => a.finished))"
        ".catch(() => null)"
    )


@pytest.fixture
def capture(page, request):
    folder = CAPTURES / request.node.name

    def shoot(name):
        for width in WIDTHS:
            page.set_viewport_size({"width": width, "height": 900})
            settle(page)
            page.screenshot(path=folder / f"{name}-{width}.png", full_page=True)
        page.set_viewport_size({"width": WIDTHS[0], "height": 900})

    return shoot


NARROW = 320  # amplada mínima que demana la definició de fet de les pantalles


# Cap transició ni animació amb final en marxa (les que no acaben mai no compten).
SETTLED_JS = """
() => document.getAnimations().every((animation) => {
  const timing = animation.effect && animation.effect.getComputedTiming();
  return animation.playState !== "running" || !timing || timing.endTime === Infinity;
})
"""


@pytest.fixture
def review(page, request, capture):
    """Com `capture` i, a més, la pantalla a 320 px en clar i en fosc. Falla si a 320 px la
    pàgina es desplaça de costat (algun element no hi cap)."""
    folder = CAPTURES / request.node.name

    def shoot(name):
        capture(name)
        page.set_viewport_size({"width": NARROW, "height": 800})
        for theme in ("light", "dark"):
            page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
            # Els botons tenen transició de color: la captura espera que acabi (auto-espera de
            # Playwright sobre una condició, no un temps fix; T-DX-64).
            page.wait_for_function(SETTLED_JS)
            page.screenshot(path=folder / f"{name}-{NARROW}-{theme}.png", full_page=True)
        overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        page.evaluate("document.documentElement.removeAttribute('data-theme')")
        page.set_viewport_size({"width": WIDTHS[0], "height": 900})
        assert overflow <= 0, f"«{name}» es desplaça de costat a {NARROW} px ({overflow} px)"

    return shoot


def make_admin(username, *roles):
    person = Person.objects.create(
        first_name=username.split(".")[0].title(), last_name="Prova", origin="in_person"
    )
    account = Account.objects.create_admin(
        person, username, PASSWORD, notification_email=f"{username}@example.org"
    )
    TotpDevice.objects.create(
        account=account, secret_encrypted=encrypt(TOTP_KEY), confirmed_at=timezone.now()
    )
    for code in roles:
        AccountRole.objects.create(admin_account=account, role=Role.objects.get(code=code))
    return account


@pytest.fixture
def texts(transactional_db):
    """Textos legals vigents: sense, el formulari d'alta no es pot enviar."""
    publisher = make_admin("administracio.prova", "administrator")
    for kind in TEXT_KINDS:
        consents.publish_text(kind, f"Text de prova: {kind}.", by=publisher)
    return publisher


@pytest.fixture
def secretary(texts):
    return make_admin("secretaria.prova", "secretary")


@pytest.fixture
def builder(texts, secretary):
    return _Builder(secretary=secretary, treasurer=None, admin=texts, password=PASSWORD)


@pytest.fixture
def member(builder):
    """Soci de ple dret amb l'alta aprovada i la quota pagada, pels serveis del 01."""
    return builder.paid_member(
        "Pere",
        "Prova Inventat",
        "pere.prova@example.org",
        builder.full,
        privacy=True,
        membership_terms=True,
    )


def login_admin(page, base_url, username, capture=None):
    """Entrada d'administrador: nom d'usuari i contrasenya, i després el codi TOTP."""
    page.goto(f"{base_url}/{settings.ADMIN_URL_PATH}/entrar/")
    if capture:
        capture("entrada")
    page.get_by_label("Nom d'usuari").fill(username)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    if capture:
        capture("codi")
    page.get_by_label("Codi").fill(pyotp.TOTP(TOTP_KEY).now())
    page.get_by_role("button", name="Verificar").click()
