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
from apps.core import consents
from apps.core.crypto import encrypt
from apps.core.models import AccountRole, Person, Role
from apps.members.demo_data import _Builder
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
        yield
        delete_committed_rows(tables, start)


class PageChecks:
    def __init__(self, page):
        self.problems = []
        self.expected = set()  # (estat, camí) que la prova espera
        page.on("console", self._console)
        page.on("pageerror", lambda error: self.problems.append(f"JavaScript: {error}"))
        page.on("requestfailed", self._failed)
        page.on("response", self._response)

    def expect(self, status, path):
        self.expected.add((status, path))

    def _console(self, message):
        if message.type == "error":
            self.problems.append(f"consola: {message.text}")

    def _failed(self, request):
        self.problems.append(f"petició fallida: {request.method} {request.url} ({request.failure})")

    def _response(self, response):
        if response.status >= 400 and (response.status, urlparse(response.url).path) not in (
            self.expected
        ):
            self.problems.append(f"{response.status} {response.request.method} {response.url}")


@pytest.fixture(autouse=True)
def page_checks(page):
    checks = PageChecks(page)
    yield checks
    assert not checks.problems, "Problemes al navegador:\n" + "\n".join(checks.problems)


@pytest.fixture
def capture(page, request):
    folder = CAPTURES / request.node.name

    def shoot(name):
        for width in WIDTHS:
            page.set_viewport_size({"width": width, "height": 900})
            page.screenshot(path=folder / f"{name}-{width}.png", full_page=True)
        page.set_viewport_size({"width": WIDTHS[0], "height": 900})

    return shoot


NARROW = 320  # amplada mínima que demana la definició de fet de les pantalles


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
