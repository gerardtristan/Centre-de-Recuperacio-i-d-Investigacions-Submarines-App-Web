"""Deposito (T-DX-16): el panell de revisió d'altes diu quantes n'hi ha per revisar, i a cada alta
«Aprova l'alta» i «Rebutja…» van a la mateixa fila d'accions."""

import re

import pytest
from django.urls import reverse

from apps.members.tests.test_admissions import (  # noqa: F401 (fixtures)
    LIST,
    a_person,
    a_request,
    admin_client,
    make_admin,
    secretary,
)

pytestmark = pytest.mark.django_db


def counter(html):
    found = re.search(r'<ul class="deposito-comptadors".*?</ul>', html, re.S)
    return found.group(0) if found else ""


def test_no_pending_join_shows_zero_without_the_warning_colour(secretary):  # noqa: F811
    html = admin_client(secretary).get(reverse(LIST)).content.decode()
    assert "<b>0</b>" in counter(html) and "es-pendent" not in counter(html)


def test_pending_joins_are_counted_and_actions_share_a_row(secretary):  # noqa: F811
    a_request(a_person("Pol", "Rius", email="pol@example.org"))
    a_request(a_person("Aina", "Mas", email="aina@example.org"))
    html = admin_client(secretary).get(reverse(LIST)).content.decode()
    assert "es-pendent" in counter(html) and "<b>2</b>" in counter(html)
    assert "altes per revisar" in counter(html)
    rows = re.findall(r'<div class="deposito-accions">(.*?)</details>', html, re.S)
    assert len(rows) == 2
    assert all("Aprova l&#x27;alta" in row or "Aprova l'alta" in row for row in rows)
    assert all("Rebutja…" in row for row in rows)
