"""«La sessió ha caducat» per inactivitat (T-M01-45, punt 6; decisió 081, punt 22; V-01).

El servidor tanca la sessió després del temps d'inactivitat de V-01 (30 minuts a l'administració,
14 dies a l'àrea de socis). El navegador esborra la galeta de sessió al mateix moment, de manera
que, sense res més, la pàgina següent només portaria a l'entrada. La galeta auxiliar
`cris_sessio_previa` només indica que en aquest navegador hi havia hagut una sessió: no porta cap
dada personal ni dona accés a res.

Només dades inventades.
"""

import pytest
from django.conf import settings
from django.contrib.sessions.models import Session
from django.urls import reverse
from django.utils import timezone

from apps.accounts.sessions import (
    ADMIN_IDLE_SECONDS,
    AUTOMATIC_HEADER,
    PERSONAL_IDLE_SECONDS,
    SESSION_HINT_COOKIE,
)

pytestmark = pytest.mark.django_db

EXPIRED = "La sessió ha caducat"
ADMIN_HOME = "administration:home"
PERSONAL_HOME = "core:home"
PROFILE = "members:profile"


def _expire_on_the_server(client):
    """El temps d'inactivitat ha passat: la sessió ja no val a la base de dades."""
    key = client.cookies[settings.SESSION_COOKIE_NAME].value
    Session.objects.filter(session_key=key).update(
        expire_date=timezone.now() - timezone.timedelta(seconds=1)
    )


def _browser_drops_the_session_cookie(client):
    """El navegador esborra la galeta de sessió quan arriba el seu `max-age`, que és el mateix
    temps d'inactivitat."""
    del client.cookies[settings.SESSION_COOKIE_NAME]


@pytest.mark.parametrize(
    ("area", "home", "idle", "login"),
    [
        ("admin", ADMIN_HOME, ADMIN_IDLE_SECONDS, "administration:login"),
        ("personal", PERSONAL_HOME, PERSONAL_IDLE_SECONDS, "accounts:login"),
    ],
)
class TestInactivity:
    @pytest.fixture
    def client_in(self, login_as, admin_account, personal_account, area):
        return login_as(admin_account if area == "admin" else personal_account, area)

    def test_activity_sets_the_hint_cookie_without_personal_data(
        self, client_in, area, home, idle, login
    ):
        response = client_in.get(reverse(home))
        assert response.status_code == 200
        hint = response.cookies[SESSION_HINT_COOKIE]
        assert hint.value == "1"
        assert hint["httponly"] and hint["samesite"] == "Lax" and hint["path"] == "/"
        assert int(hint["max-age"]) > idle
        assert client_in.session.get_expiry_age() == idle

    def test_after_inactivity_the_page_explains_it_and_offers_to_log_in_again(
        self, client_in, area, home, idle, login
    ):
        client_in.get(reverse(home))
        _expire_on_the_server(client_in)
        _browser_drops_the_session_cookie(client_in)

        response = client_in.get(reverse(home))
        assert response.status_code == 401
        html = response.content.decode()
        assert EXPIRED in html
        assert f'href="{reverse(login)}?next=' in html
        assert "no-store" in response["Cache-Control"]
        # La pista s'esborra: la pàgina es veu una sola vegada i no hi ha cap bucle.
        assert response.cookies[SESSION_HINT_COOKIE]["max-age"] == 0
        again = client_in.get(reverse(home))
        assert again.status_code == 302
        assert again["Location"].startswith(reverse(login))

    def test_the_server_enforces_it_even_if_the_browser_keeps_the_cookie(
        self, client_in, area, home, idle, login
    ):
        client_in.get(reverse(home))
        _expire_on_the_server(client_in)
        response = client_in.get(reverse(home))
        assert response.status_code == 401
        assert EXPIRED in response.content.decode()
        assert "_auth_user_id" not in client_in.session

    def test_the_hint_alone_gives_no_access(self, client, area, home, idle, login):
        client.cookies[SESSION_HINT_COOKIE] = "1"
        response = client.get(reverse(home))
        assert response.status_code == 401
        assert EXPIRED in response.content.decode()
        assert "_auth_user_id" not in client.session

    def test_logging_out_deletes_the_hint(self, client_in, area, home, idle, login):
        client_in.get(reverse(home))
        logout = "administration:logout" if area == "admin" else "accounts:logout"
        response = client_in.post(reverse(logout))
        assert response.cookies[SESSION_HINT_COOKIE]["max-age"] == 0
        # Qui surt i torna a entrar a una pàgina protegida va a l'entrada, sense «caducada».
        follow = client_in.get(reverse(home))
        assert follow.status_code == 302

    def test_prefetch_and_automatic_requests_do_not_count_as_activity(
        self, client_in, area, home, idle, login
    ):
        session = client_in.session
        session.set_expiry(60)
        session.save()
        for headers in ({"Sec-Purpose": "prefetch"}, {"Purpose": "prefetch"}, AUTOMATIC_HEADER):
            response = client_in.get(reverse(home), headers=headers)
            assert response.status_code == 200
            assert SESSION_HINT_COOKIE not in response.cookies
            assert client_in.session.get_expiry_age() <= 60
        client_in.get(reverse(home))
        assert client_in.session.get_expiry_age() == idle

    def test_htmx_request_after_inactivity_reloads_the_current_page(
        self, client_in, area, home, idle, login
    ):
        client_in.get(reverse(home))
        _expire_on_the_server(client_in)
        _browser_drops_the_session_cookie(client_in)
        current = f"http://testserver{reverse(home)}"
        response = client_in.post(
            reverse(home), headers={"HX-Request": "true", "HX-Current-URL": current}
        )
        assert response.status_code == 401
        assert response["HX-Redirect"] == reverse(home)
        # La pista es manté: la pàgina sencera que es carrega ara és la que ho explica.
        assert SESSION_HINT_COOKIE not in response.cookies
        assert client_in.get(reverse(home)).status_code == 401


def test_a_form_sent_after_inactivity_changes_nothing(login_as, personal_account):
    from apps.members.tests.test_personal_area import make_member

    make_member(personal_account.person, 101)
    client = login_as(personal_account, "personal")
    client.get(reverse(PROFILE))
    _expire_on_the_server(client)
    _browser_drops_the_session_cookie(client)
    phone = personal_account.person.phone
    response = client.post(reverse(PROFILE), {"phone": "611111111", "address": ""})
    assert response.status_code == 401
    personal_account.person.refresh_from_db()
    assert personal_account.person.phone == phone


def test_htmx_with_a_foreign_current_url_goes_to_the_login(client):
    client.cookies[SESSION_HINT_COOKIE] = "1"
    response = client.post(
        reverse(PERSONAL_HOME),
        headers={"HX-Request": "true", "HX-Current-URL": "https://exemple.invalid/socis/"},
    )
    assert response.status_code == 401
    assert response["HX-Redirect"] == reverse("accounts:login")


def test_never_logged_in_goes_straight_to_the_login(client):
    response = client.get(reverse(PERSONAL_HOME))
    assert response.status_code == 302
    assert SESSION_HINT_COOKIE not in response.cookies


def test_no_template_polls_without_marking_the_request_as_automatic():
    """Una petició periòdica d'HTMX (`hx-trigger="every …"`) ha de portar la capçalera de les
    automàtiques; si no, mantindria la sessió oberta indefinidament."""
    import re
    from pathlib import Path

    polling = re.compile(r"hx-trigger=[\"'][^\"']*\bevery\b")
    offenders = []
    for path in Path(settings.BASE_DIR, "templates").rglob("*.html"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if polling.search(line) and "X-CRIS-Automatica" not in line:
                offenders.append(f"{path.name}: {line.strip()}")
    assert offenders == []
