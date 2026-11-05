"""T-M01-38: plantilla base, fulls d'estil i pantalles de comptes.

Proves del «Feta quan» que es poden automatitzar: cap recurs extern, JavaScript en fitxers
propis, etiquetes dels camps (B8 bàsica), una sola còpia dels tokens, fonts amb llicència i
els textos aprovats de l'accés denegat i de la sessió caducada. El contrast, el teclat, el
focus i els 320 px es comproven al navegador (diari de la T-M01-38).
"""

import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.test import Client
from django.urls import reverse
from django.views.defaults import permission_denied

ROOT = Path(settings.BASE_DIR)
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"

# Etiquetes que carreguen un recurs; un enllaç <a> no carrega res.
EXTERNAL_LOAD = re.compile(
    r"<(?:script|link|img|iframe|source|video|audio|embed|object)\b[^>]*"
    r"\b(?:src|href|srcset|data)\s*=\s*[\"']?\s*(?:https?:)?//",
    re.IGNORECASE,
)
EXTERNAL_CSS = re.compile(r"(?:url\(\s*[\"']?\s*(?:https?:)?//|@import)", re.IGNORECASE)


def page_templates():
    # Els correus no són pàgines: s'obren al client de correu i no carreguen res de la web.
    return sorted(p for p in TEMPLATES.rglob("*.html") if "emails" not in p.parts)


@pytest.mark.parametrize("path", page_templates(), ids=lambda p: p.name)
def test_no_template_loads_external_resources(path):
    text = path.read_text(encoding="utf-8")
    assert not EXTERNAL_LOAD.search(text)
    # El JavaScript va en fitxers propis (066): cap <script> sense src.
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", text)


@pytest.mark.parametrize("path", sorted(STATIC.glob("css/*.css")), ids=lambda p: p.name)
def test_no_stylesheet_loads_external_resources(path):
    assert not EXTERNAL_CSS.search(path.read_text(encoding="utf-8"))


def test_the_wireframe_key_is_not_in_the_platform():
    # La clau TOTP inventada del wireframe no pot arribar al funcionament real.
    for path in [*page_templates(), *STATIC.rglob("*.css"), *STATIC.rglob("*.js")]:
        assert "ABCDEFGHIJKLMNOP" not in path.read_text(encoding="utf-8", errors="ignore")


def test_tokens_have_a_single_copy():
    skip = {".venv", "staticfiles", "node_modules", ".git"}
    copies = [p for p in ROOT.rglob("tokens.css") if not skip & set(p.parts)]
    assert copies == [STATIC / "css" / "tokens.css"]
    for wireframe in (ROOT / "design" / "wireframes").glob("*.html"):
        text = wireframe.read_text(encoding="utf-8")
        assert 'href="../../static/css/tokens.css"' in text
        assert "fonts.googleapis.com" not in text


def test_fonts_are_local_woff2_with_their_licence():
    css = (STATIC / "css" / "fonts.css").read_text(encoding="utf-8")
    files = re.findall(r'url\("\.\./fonts/([^"]+)"\)', css)
    assert len(files) == 7
    for name in files:
        path = STATIC / "fonts" / name
        assert path.read_bytes()[:4] == b"wOF2"
        assert any((path.parent / licence).exists() for licence in ("OFL.txt", "LICENSE.md"))


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts, self.labels, self.inputs = [], set(), []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script":
            self.scripts.append(attrs)
        elif tag == "label" and attrs.get("for"):
            self.labels.add(attrs["for"])
        elif tag in ("input", "textarea", "select") and attrs.get("type") != "hidden":
            self.inputs.append(attrs)


PUBLIC_PAGES = ["accounts:login", "administration:login", "accounts:password_reset_request"]


@pytest.mark.parametrize("name", PUBLIC_PAGES)
def test_pages_load_the_theme_before_painting_and_label_every_field(db, name):
    response = Client().get(reverse(name))
    assert response.status_code == 200
    page = Page()
    page.feed(response.content.decode())
    theme = [s for s in page.scripts if s.get("src", "").endswith("js/tema.js")]
    assert theme
    assert "defer" not in theme[0]
    # B8 bàsica: cada camp visible té una etiqueta (els del tema la tenen dins del <label>).
    for field in page.inputs:
        if field.get("name") == "tema":
            continue
        assert field.get("id") in page.labels, field


def test_fields_are_at_least_16px():
    # Els camps hereten la lletra del cos (--t-m, 16 px) i cap regla de pàgina no la redueix.
    tokens = (STATIC / "css" / "tokens.css").read_text(encoding="utf-8")
    assert "--t-m: 1rem;" in tokens
    assert re.search(r"\.camp input, \.camp select, \.camp textarea \{[^}]*font: inherit;", tokens)
    pages = (STATIC / "css" / "comptes.css").read_text(encoding="utf-8")
    assert not re.search(r"\.camp (?:input|select|textarea)[^{]*\{[^}]*font-size", pages)


def test_access_denied_text(rf):
    request = rf.get("/")
    request.resolver_match = None
    response = permission_denied(request, PermissionDenied())
    text = response.content.decode()
    assert response.status_code == 403
    assert "No tens permís per veure aquesta pàgina" in text
    assert "parla-ho amb un administrador del club." in text


class TestSessionExpired:
    def test_dead_session_cookie_shows_the_page(self, db):
        client = Client()
        client.cookies[settings.SESSION_COOKIE_NAME] = "sessio-que-ja-no-existeix"
        response = client.get(reverse("core:home"))
        assert response.status_code == 401
        text = response.content.decode()
        assert "La sessió ha caducat" in text
        assert "Per seguretat, torna a entrar." in text
        assert f'href="{reverse("accounts:login")}?next=' in text
        assert "no-cache" in response["Cache-Control"]

    def test_without_a_previous_session_it_still_redirects(self, db):
        response = Client().get(reverse("administration:home"))
        assert response.status_code == 302
        assert response["Location"].startswith(reverse("administration:login"))

    def test_htmx_requests_keep_the_redirect_header(self, db):
        client = Client()
        client.cookies[settings.SESSION_COOKIE_NAME] = "sessio-que-ja-no-existeix"
        response = client.get(reverse("core:home"), headers={"HX-Request": "true"})
        assert response.status_code == 401
        assert response["HX-Redirect"] == reverse("accounts:login")
