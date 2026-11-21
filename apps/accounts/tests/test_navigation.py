"""T-M01-46: navegació comuna de l'administració i de l'àrea personal.

- Criteri d'acceptació: per a cada rol de la configuració inicial, cap entrada del menú surt
  sense el permís de la ruta (i totes les que el compte pot obrir hi surten). El que s'espera
  surt de la matriu carregada a la base de dades i del que respon cada vista, no d'una taula
  escrita aquí.
- El menú, el compte actiu, l'estat del TOTP i «Surt» (POST amb CSRF) són a totes les pantalles
  de l'administració; «Surt», també al menú de l'àrea personal.
- Sense sessió d'administració no hi ha menú ni cap consulta; amb sessió, es calcula una vegada.

Només dades inventades.
"""

import re
import time

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import Client, RequestFactory
from django.urls import reverse

from apps.accounts.navigation import (
    ENTRIES,
    admin_nav_for,
    admin_navigation,
    need_met,
    route_needs,
)
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.accounts.sessions import ADMIN_MAX_AGE_SECONDS, AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core import consents
from apps.core.models import Role, RolePermission
from apps.core.permissions import has_perm
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.under_construction import PERMISSION as UNDER_CONSTRUCTION
from apps.members.permissions import ROUTES
from apps.members.tests.test_route_permissions import a_member

ROLES = [code for code in Role.Code.values if code not in ("member", "visitor", "guest")]
ENTRY_NAMES = [name for name, _label, _children in ENTRIES]
SIDEBAR = re.compile(r'<aside id="barra-lateral".*?</aside>', re.S)
LOGOUT_FORM = re.compile(r'<form method="post" action="([^"]+)">(.*?)</form>', re.S)


@pytest.fixture(autouse=True)
def texts(make_admin):  # noqa: F811
    """Textos legals vigents: sense, «Alta presencial» respon 503 en lloc del formulari."""
    publisher = make_admin("administrator", username="publica.textos")
    for kind in ("privacy", "membership_terms", "guardian_authorization"):
        consents.publish_text(kind, f"Text de prova: {kind}.", by=publisher)


def sidebar(response):
    match = SIDEBAR.search(response.content.decode())
    return match.group(0) if match else ""


def menu_links(response):
    nav = re.search(r'<nav class="lateral-nav".*?</nav>', sidebar(response), re.S)
    return re.findall(r'<a href="([^"]+)"', nav.group(0)) if nav else []


def admin_request(account, *, auth_at=None):
    request = RequestFactory().get("/")
    request.user = account
    request.session = {
        AREA_SESSION_KEY: AREA_ADMIN if account.is_authenticated else None,
        AUTH_AT_SESSION_KEY: auth_at or time.time(),
    }
    request.resolver_match = None
    return request


# --- Criteri d'acceptació: cap entrada sense el permís ------------------------------------------


@pytest.mark.parametrize("who", [*ROLES, None])
def test_no_menu_entry_without_the_permission_of_its_route(login_as, make_admin, who):  # noqa: F811
    """Per a cada rol (i un compte sense cap rol): una entrada surt si, i només si, el compte
    té el permís que la ruta declara, i la vista hi respon igual (200 amb entrada, «no trobat»
    sense)."""
    account = make_admin(*([who] if who else []))
    client = login_as(account, AREA_ADMIN)
    shown = menu_links(client.get(reverse("administration:home")))
    assert len(shown) == len(set(shown))
    for name in ENTRY_NAMES:
        url = reverse(name)
        if name in ROUTES:  # rutes del 01: el permís declarat a apps/members/permissions.py
            declared = all(has_perm(account, code, write=w) for code, w in ROUTES[name]["GET"])
        else:  # rutes de la 00: n'hi ha prou amb un dels grups
            declared = any(
                all(need_met(account, need) for need in group) for group in route_needs(name)
            )
        assert (url in shown) == declared, name
        assert client.get(url).status_code == (200 if declared else 404), name
    assert set(shown) <= {reverse(name) for name in ENTRY_NAMES}


def test_account_without_roles_only_sees_the_home_entry(login_as, make_admin):  # noqa: F811
    response = login_as(make_admin(), AREA_ADMIN).get(reverse("administration:home"))
    assert menu_links(response) == [reverse("administration:home")]


def test_every_menu_route_has_no_parameters_and_a_declared_permission():
    for name in ENTRY_NAMES:
        assert reverse(name) and route_needs(name), name


# --- A totes les pantalles: menú, compte actiu, TOTP i «Surt» ----------------------------------


def test_every_admin_screen_carries_the_menu_the_account_and_the_logout(login_as, make_admin):  # noqa: F811
    account = make_admin(
        "administrator", "treasurer", username="marta.adm"
    )  # M9 només el té el tresorer
    RolePermission.objects.create(  # DX1 no el té cap rol d'entrada (P-90; T-DX-50)
        role=Role.objects.get(code="administrator"), permission_code=UNDER_CONSTRUCTION, scope="all"
    )
    client = login_as(account, AREA_ADMIN)
    member = a_member("Fitxa")
    children = {
        "administration:members_list": reverse(
            "administration:member_detail", kwargs={"pk": member.pk}
        ),
        "administration:accounts": reverse(
            "administration:reset_credentials", kwargs={"pk": account.pk}
        ),
    }
    for name in ENTRY_NAMES:
        for url in filter(None, [reverse(name), children.get(name)]):
            response = client.get(url)
            assert response.status_code == 200, url
            html = sidebar(response)
            assert len(menu_links(response)) == len(ENTRY_NAMES), url
            # Entrada actual: una sola, la d'aquesta pantalla (o la de la pantalla d'on penja).
            assert re.findall(r'<a href="([^"]+)" aria-current="page"', html) == [reverse(name)]
            assert '<span class="codi">marta.adm</span>' in html
            assert "TOTP actiu" in html
            ((action, form),) = LOGOUT_FORM.findall(html)
            assert action == reverse("administration:logout")
            assert 'name="csrfmiddlewaretoken"' in form
            assert re.search(r'<button class="boto[^"]*" type="submit">Surt</button>', form)


def test_menu_shows_when_the_account_has_no_totp(make_admin):  # noqa: F811
    """No pot passar amb una sessió oberta per l'entrada (RN-21), però l'estat surt de la dada."""
    nav = admin_nav_for(admin_request(make_admin("secretary", totp=False)))
    assert nav.totp_active is False


def test_logout_from_the_menu_is_a_post_with_csrf(make_admin):  # noqa: F811
    client = Client(enforce_csrf_checks=True)
    client.force_login(make_admin("secretary"))
    session = client.session
    session[AREA_SESSION_KEY] = AREA_ADMIN
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    home = reverse("administration:home")
    logout = reverse("administration:logout")
    ((action, form),) = LOGOUT_FORM.findall(sidebar(client.get(home)))
    token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', form).group(1)
    assert client.get(logout).status_code == 405
    assert client.post(logout).status_code == 403  # sense el testimoni CSRF
    assert client.get(home).status_code == 200  # la sessió continua oberta
    response = client.post(action, {"csrfmiddlewaretoken": token})
    assert response.status_code == 302 and response["Location"] == reverse("administration:login")
    assert client.get(home).status_code == 302


def test_admin_home_lists_the_same_entries_as_the_menu(login_as, make_admin):  # noqa: F811
    """L'inici de l'administració fa servir el mateix menú: cap llista d'enllaços a part, i cap
    botó sense estil (T-M01-45, punt 4)."""
    response = login_as(make_admin("treasurer"), AREA_ADMIN).get(reverse("administration:home"))
    html = response.content.decode()
    main = re.search(r"<main.*</main>", html, re.S).group(0)
    in_menu = menu_links(response)
    assert re.findall(r'<a href="([^"]+)"', main) == in_menu[1:]  # tot menys «Inici»
    assert "Sortir" not in html
    assert not re.search(r"<button(?![^>]*class=\"boto)", html)


# --- Sense sessió d'administració: ni menú ni consultes -----------------------------------------


@pytest.mark.django_db
def test_no_menu_and_no_query_without_an_admin_session(
    client, personal_account, django_assert_num_queries
):
    anonymous = admin_request(AnonymousUser())
    personal = admin_request(personal_account)
    personal.session[AREA_SESSION_KEY] = AREA_PERSONAL
    with django_assert_num_queries(0):
        assert not admin_navigation(anonymous)["admin_nav"]
        assert not admin_navigation(personal)["admin_nav"]
    for name in ("administration:login", "accounts:login"):
        html = client.get(reverse(name)).content.decode()
        assert "barra-lateral" not in html and "boto-menu" not in html


def test_personal_session_never_gets_the_admin_menu(login_as, personal_account):
    html = login_as(personal_account, AREA_PERSONAL).get(reverse("core:home")).content.decode()
    assert "barra-lateral" not in html and "menu-admin.js" not in html


def test_admin_session_older_than_the_maximum_gets_no_menu(login_as, make_admin):  # noqa: F811
    """Passades les 8 hores (V-01), una adreça que no existeix no ensenya el menú."""
    client = login_as(make_admin("administrator"), AREA_ADMIN)
    session = client.session
    session[AUTH_AT_SESSION_KEY] = time.time() - ADMIN_MAX_AGE_SECONDS - 1
    session.save()
    response = client.get("/no-existeix/")
    assert response.status_code == 404
    html = response.content.decode()
    assert "barra-lateral" not in html and 'class="zona-soci"' in html


def test_menu_is_computed_once_per_request_and_only_when_used(
    make_admin,  # noqa: F811
    django_assert_num_queries,
):
    request = admin_request(make_admin("secretary"))
    with django_assert_num_queries(0):
        context = admin_navigation(request)  # un fragment que no el dibuixa no consulta res
    first = context["admin_nav"]
    assert first.entries  # ara sí: rols, matriu i TOTP
    with django_assert_num_queries(0):
        again = admin_navigation(request)["admin_nav"]
        assert again.entries == first.entries and again.username == first.username


# --- Àrea personal ------------------------------------------------------------------------------


def test_personal_menu_has_the_logout_as_a_post_with_csrf(login_as, personal_account):
    client = login_as(personal_account, AREA_PERSONAL)
    for name in ("core:home", "members:profile", "accounts:security"):
        html = client.get(reverse(name)).content.decode()
        # Capçalera (sense JavaScript i fins a 1023 px) i panell de Ramillete (des de 1024 px).
        for nav_class in ("navegacio-compte", "ramillete"):
            nav = re.search(rf'<nav class="{nav_class}".*?</nav>', html, re.S).group(0)
            ((action, form),) = LOGOUT_FORM.findall(nav)
            assert action == reverse("accounts:logout")
            assert 'name="csrfmiddlewaretoken"' in form
            assert re.search(
                r'<button class="boto[^"]*" type="submit">(<svg.*?</svg>)?Surt</button>', form
            )
        # Un «Surt» per mida (el CSS en deixa veure un per pantalla) i un sol text a tot arreu.
        assert html.count("Surt</button>") == 2 and "Sortir" not in html


def test_personal_logout_closes_the_session(login_as, personal_account):
    client = login_as(personal_account, AREA_PERSONAL)
    response = client.post(reverse("accounts:logout"))
    assert response.status_code == 302 and response["Location"] == reverse("accounts:login")
    assert client.get(reverse("core:home")).status_code == 302
