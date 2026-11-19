"""Navegació de l'àrea del soci (T-DX-59): les etiquetes `preview_url` (l'entrada «Activitats» només
si la pantalla existeix i qui mira la pot veure) i `has_pending_fee` («Paga ara» només amb una quota
pròpia pendent, en una consulta)."""

import re

import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL
from apps.members.tests.test_cards import account_for, add_fee, make_member, pay

pytestmark = pytest.mark.django_db


def preview_url(name, user):
    request = RequestFactory().get("/")
    request.user = user
    template = Template("{% load member_nav %}{% preview_url name as url %}[{{ url }}]")
    return template.render(Context({"request": request, "name": name}))


def pending(user):
    return Template("{% load member_nav %}{% has_pending_fee %}").render(Context({"user": user}))


def test_preview_url_needs_the_route_and_the_setting(settings, personal_account):
    settings.SHOW_UNDER_CONSTRUCTION = True
    assert preview_url("previews:index", personal_account) == f"[{reverse('previews:index')}]"
    assert preview_url("previews:no-existeix", personal_account) == "[]"
    settings.SHOW_UNDER_CONSTRUCTION = False  # producció: un soci mai no hi arriba
    assert preview_url("previews:index", personal_account) == "[]"


def test_has_pending_fee_reads_only_the_session_member_in_one_query(
    django_assert_num_queries, admin_account
):
    member = make_member()
    other = make_member("Berta", number=1288, document="87654321X")
    account = account_for(member)
    add_fee(other)  # la quota pendent d'un altre soci no compta
    with django_assert_num_queries(1):
        assert pending(account) == "False"
    fee = add_fee(member)
    assert pending(account) == "True"
    pay(fee)
    assert pending(account) == "False"
    assert pending(admin_account) == "False"  # el compte d'administrador no és la porta del soci


def test_the_bar_puts_more_in_the_centre_without_activities(login_as, settings):
    settings.SHOW_UNDER_CONSTRUCTION = (
        False  # el soci no veu «Activitats» (en construcció, T-DX-63)
    )
    member = make_member()
    client = login_as(account_for(member), AREA_PERSONAL)
    html = client.get(reverse("core:home")).content.decode()
    bar = html[html.index('<ul class="ramillete-barra">') : html.index('class="ramillete-lateral"')]
    tabs = re.findall(r'ramillete-pestanya"[^>]*>.*?</svg>([^<]+)</a>|(ramillete-boto)"', bar, re.S)
    assert [label or "Més" for label, _ in tabs] == ["Inici", "Perfil", "Més", "Carnet", "Quotes"]
    assert "Activitats" not in html
    # Sense quota, ni «Paga ara» ni «Demana un carnet nou» (la regla de la pàgina del carnet), i
    # sense cap de les dues, la fletxa del QR no hi és.
    assert "Paga ara" not in html and "Demana un carnet nou" not in html
    assert "ramillete-qr-mes" not in html and "Mostra el QR" in html
    fee = add_fee(member)
    html = client.get(reverse("core:home")).content.decode()
    assert "Paga ara" in html and "Demana un carnet nou" not in html
    pay(fee)
    html = client.get(reverse("core:home")).content.decode()
    assert "Paga ara" not in html and "Demana un carnet nou" in html


def test_the_bar_shows_activities_when_the_preview_is_visible(login_as, settings):
    settings.SHOW_UNDER_CONSTRUCTION = (
        True  # «Activitats» en construcció (T-DX-63) ocupa el lloc de «Perfil»
    )
    client = login_as(account_for(make_member()), AREA_PERSONAL)
    html = client.get(reverse("core:home")).content.decode()
    bar = html[html.index('<ul class="ramillete-barra">') : html.index('class="ramillete-lateral"')]
    tabs = re.findall(r'ramillete-pestanya"[^>]*>.*?</svg>([^<]+)</a>|(ramillete-boto)"', bar, re.S)
    assert [label or "Més" for label, _ in tabs] == [
        "Inici",
        "Activitats",
        "Més",
        "Carnet",
        "Quotes",
    ]


def test_a_personal_account_without_member_sees_only_its_own_entries(login_as, personal_account):
    html = login_as(personal_account, AREA_PERSONAL).get(reverse("core:home")).content.decode()
    nav = re.search(r'<nav class="ramillete".*?</nav>', html, re.S).group(0)
    assert "Mostra el QR" not in nav and reverse("members:fees") not in nav
    for name in ("core:home", "members:profile", "accounts:security"):
        assert reverse(name) in nav
