"""Dashboard amb la llavor al navegador (T-M08-14; CA-M08-02): el tresorer obre els panells
general, de socis i d'activitat amb les dades inventades de `seed_demo_data` i cap nom ni correu
de la llavor no surt a la pantalla. Captures a 1280, 390 i 320 px. Dades inventades."""

from io import StringIO

import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from playwright.sync_api import expect

from apps.accounts.models import Account
from apps.core.management.commands.seed_demo_data import ROLE_ACCOUNTS
from apps.core.models import Person

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_dashboard_with_the_seed_shows_no_person(
    page, live_server, transactional_db, review, tmp_path
):
    with override_settings(SETTINGS_MODULE="config.settings.dev", DEBUG=True):
        call_command("seed_demo_data", "--cluber-file", str(tmp_path / "c.csv"), stdout=StringIO())
    cache.clear()
    # Les persones dels comptes de rol de la llavor es diuen com el rol («Cursos»): no compten.
    roles = Account.objects.filter(login__in=[login for login, _, _ in ROLE_ACCOUNTS])
    names = {
        value
        for person in Person.objects.exclude(pk__in=roles.values_list("person", flat=True))
        for value in (person.first_name, person.last_name, person.contact_email)
        if value and len(value) >= 3
    }
    treasurer = make_admin("tresorer.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    for panel, heading, shot in (
        ("general", "Panell General", "dashboard-llavor-general"),
        ("members", "Panell Socis", "dashboard-llavor-socis"),
        ("activity", "Panell Activitat", "dashboard-llavor-activitat"),
    ):
        page.goto(f"{live_server.url}{reverse('administration:dashboard_panel', args=[panel])}")
        expect(page.get_by_role("heading", name=heading)).to_be_visible()
        text = page.locator("main").inner_text()
        assert not [name for name in names if name in text.split()], panel
        review(shot)
