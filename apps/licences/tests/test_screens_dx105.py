"""T-DX-105 (Vigencia al 06): al llistat de llicències de l'administració, una llicència «Per
renovar» porta els dies que queden a la cel·la «Caduca» (només amb el camp C6, com la data). Només
dades inventades."""

import datetime

from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.models import Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.members.fee_rules import local_today

EXT = {"origin": "external", "price_kind": None, "price_cents": None, "status": "active"}


def test_to_renew_shows_the_days_left(login_as, make_admin, make_licence, make_person):  # noqa: F811
    today = local_today()
    make_licence(
        person=make_person("Anna", "Vila"),
        starts_on=today - datetime.timedelta(days=300),
        expires_on=today + datetime.timedelta(days=10),
        **EXT,
    )
    make_licence(
        person=make_person("Pere", "Roca"),
        starts_on=today - datetime.timedelta(days=10),
        expires_on=today + datetime.timedelta(days=300),
        **EXT,
    )
    client = login_as(make_admin(Role.Code.SECRETARY), AREA_ADMIN)
    html = main_of(client.get(reverse("administration:licences")).content.decode())
    assert html.count('class="vigencia vigencia-avis"') == 1  # només la «Per renovar»
    assert "Queden 10 dies" in html
