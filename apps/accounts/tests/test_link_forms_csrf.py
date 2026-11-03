"""Formularis dels enllaços del correu amb la comprovació CSRF activada, com en un navegador
(regressió de la revisió de la T-M01-05 a 50324e9). Les pàgines netes enviaven
«Referrer-Policy: no-referrer»; amb aquesta política el navegador envia «Origin: null» al POST
i Django el rebutja, de manera que ni la verificació ni la recuperació es podien completar.
Només dades inventades.
"""

from types import SimpleNamespace

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts import email_links, tokens
from apps.accounts.models import Account
from conftest import NEW_PASSWORD, PASSWORD

pytestmark = pytest.mark.django_db

ORIGIN = "http://testserver"

FLOWS = {
    "verificacio": (tokens.VERIFY_EMAIL, "accounts:verify_email_link", "accounts:verify_email"),
    "recuperacio": (
        tokens.RESET_PASSWORD,
        "accounts:password_reset_link",
        "accounts:password_reset",
    ),
}


@pytest.fixture(params=FLOWS)
def flow(request, make_person):
    """Un compte del flux, un navegador amb CSRF actiu i l'enllaç ja obert."""
    purpose, link_name, page_name = FLOWS[request.param]
    account = Account.objects.create_personal(make_person(), "anna@example.org", PASSWORD)
    if purpose is tokens.RESET_PASSWORD:
        account.status = Account.Status.ACTIVE
        account.save()
    token = tokens.make_token(account, purpose)
    client = Client(enforce_csrf_checks=True)
    first = client.get(reverse(link_name, args=[token]))
    page = client.get(reverse(page_name))
    data = {}
    if request.param == "recuperacio":
        data = {"new_password1": NEW_PASSWORD, "new_password2": NEW_PASSWORD}
    return SimpleNamespace(
        name=request.param,
        account=account,
        token=token,
        client=client,
        link_name=link_name,
        page_name=page_name,
        first=first,
        page=page,
        data=data,
    )


def csrf_of(response):
    return str(response.context["csrf_token"])


def post(f, *, csrf=None, origin=ORIGIN, **extra):
    data = dict(f.data)
    if csrf is not None:
        data["csrfmiddlewaretoken"] = csrf
    if origin is not None:
        extra["HTTP_ORIGIN"] = origin
    return f.client.post(reverse(f.page_name), data, **extra)


def done(f):
    f.account.refresh_from_db()
    if f.name == "verificacio":
        return f.account.status == Account.Status.ACTIVE
    return f.account.check_password(NEW_PASSWORD)


class TestHeaders:
    def test_link_redirects_to_the_clean_url_without_referrer(self, flow):
        assert flow.first.status_code == 302
        assert flow.first["Location"] == reverse(flow.page_name)
        assert flow.token not in flow.first["Location"]
        assert flow.first["Referrer-Policy"] == "no-referrer"
        assert "no-store" in flow.first["Cache-Control"]

    def test_clean_page_keeps_the_origin_for_the_form(self, flow):
        assert flow.page.status_code == 200
        assert flow.page.context["state"] == "ready"
        assert flow.page["Referrer-Policy"] == "same-origin"
        assert "no-store" in flow.page["Cache-Control"]
        html = flow.page.content.decode()
        assert flow.token not in html
        assert 'name="csrfmiddlewaretoken"' in html


class TestCsrf:
    def test_legitimate_post_with_token_and_same_origin(self, flow):
        response = post(flow, csrf=csrf_of(flow.page))
        assert response.status_code == 200
        assert response.context["state"] == "done"
        assert response["Referrer-Policy"] == "same-origin"
        assert "no-store" in response["Cache-Control"]
        assert done(flow)

    @pytest.mark.parametrize(
        "origin, csrf",
        [
            ("https://atacant.example", "valid"),  # origen aliè
            ("null", "valid"),  # el que enviava el navegador amb «no-referrer»: es rebutja
            (ORIGIN, None),  # sense testimoni CSRF
            (ORIGIN, "x" * 64),  # testimoni CSRF incorrecte
        ],
    )
    def test_rejected_and_the_link_is_not_spent(self, flow, origin, csrf):
        token = csrf_of(flow.page) if csrf == "valid" else csrf
        response = post(flow, csrf=token, origin=origin)
        assert response.status_code == 403
        assert not done(flow)
        # El rebuig no gasta l'enllaç: el POST legítim posterior funciona.
        assert post(flow, csrf=csrf_of(flow.page)).context["state"] == "done"
        assert done(flow)


class TestSingleUse:
    def test_second_post_and_reopened_link_are_invalid(self, flow):
        csrf = csrf_of(flow.page)
        assert post(flow, csrf=csrf).context["state"] == "done"
        session_key = (
            email_links.VERIFY_SESSION_KEY
            if flow.name == "verificacio"
            else email_links.RESET_SESSION_KEY
        )
        assert session_key not in flow.client.session
        assert post(flow, csrf=csrf).context["state"] == "invalid"
        flow.client.get(reverse(flow.link_name, args=[flow.token]))
        assert flow.client.get(reverse(flow.page_name)).context["state"] == "invalid"


class TestBehindHttpsProxy:
    """Com a producció: TLS al proxy (`SECURE_PROXY_SSL_HEADER` de `config/settings/prod.py`).
    Simula les capçaleres del proxy; no prova cap navegador real sobre HTTPS."""

    # El proxy reenvia el protocol i l'amfitrió (sense Host, el client de proves faria servir
    # el port 80 i l'origen esperat seria «https://testserver:80»).
    HTTPS = {"HTTP_X_FORWARDED_PROTO": "https", "HTTP_HOST": "testserver"}

    @pytest.fixture(autouse=True)
    def _proxy(self, settings):
        settings.SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    def test_same_origin_https_post_succeeds(self, flow):
        page = flow.client.get(reverse(flow.page_name), **self.HTTPS)
        assert page["Referrer-Policy"] == "same-origin"
        response = post(flow, csrf=csrf_of(page), origin="https://testserver", **self.HTTPS)
        assert response.status_code == 200
        assert done(flow)

    def test_http_origin_is_rejected_on_https(self, flow):
        page = flow.client.get(reverse(flow.page_name), **self.HTTPS)
        response = post(flow, csrf=csrf_of(page), origin=ORIGIN, **self.HTTPS)
        assert response.status_code == 403
        assert not done(flow)
