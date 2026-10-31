"""La interfície serveix HTMX des del VPS, mai des d'un CDN (decisió 046)."""

import re

from django.conf import settings
from django.contrib.staticfiles import finders
from django.urls import reverse


def test_htmx_is_served_locally(client):
    html = client.get(reverse("accounts:login")).content.decode()
    assert f"{settings.STATIC_URL}vendor/htmx/htmx.min.js" in html
    assert finders.find("vendor/htmx/htmx.min.js")


def test_no_external_scripts(client):
    html = client.get(reverse("accounts:login")).content.decode()
    assert not re.search(r"<script[^>]+src=[\"'](https?:)?//", html)


def test_page_language_is_catalan(client):
    html = client.get(reverse("accounts:login")).content.decode()
    assert '<html lang="ca">' in html
