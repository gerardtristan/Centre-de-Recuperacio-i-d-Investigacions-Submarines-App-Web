"""Prova de principi a fi del dashboard amb la llavor (T-M08-14; CA-M08-02 i CA-M08-04;
RN-M08-01). Amb les dades inventades de `seed_demo_data`, cada rol de la llavor amb DB1 obre els
cinc panells amb cada període: cap nom, cognom, correu, document, telèfon ni número de soci de cap
persona de la llavor surt a l'HTML; i les xifres del panell són les que tornen els serveis dels
mòduls (01, 02, 03 i 09) per al mateix període."""

import re
from io import StringIO

import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.activities import stats as activity_stats
from apps.core.management.commands.seed_demo_data import ROLE_ACCOUNTS
from apps.core.models import Department, Person
from apps.core.tests.test_guest_links import admin_client
from apps.dashboard import panels, views
from apps.dashboard.indicators import PANELS
from apps.equipment import stock
from apps.margins.reports import department_report
from apps.members import services as members
from apps.members.models import Member

pytestmark = pytest.mark.django_db
DEV = override_settings(SETTINGS_MODULE="config.settings.dev", DEBUG=True)
ROLE_LOGINS = [login for login, _, _ in ROLE_ACCOUNTS]
DB1_ACCOUNTS = ["admin-demo", "secretaria-demo", "tresorer-demo", "president-demo", "cursos-demo"]


@pytest.fixture
def seeded(tmp_path):
    with DEV:
        call_command("seed_demo_data", "--cluber-file", str(tmp_path / "c.csv"), stdout=StringIO())
    cache.clear()
    yield
    cache.clear()


def _personal_values(viewer) -> set[str]:
    """Tot el que identifica una persona de la llavor, tret del compte que mira (la seva
    capçalera el pot portar) i del nom de les persones dels comptes de rol de la llavor, que és
    el nom del rol («Cursos», «Tresorer»…) i surt als menús; els seus noms d'usuari sí que es
    comproven. Els números de soci es busquen amb la forma «núm.», perquè sols es confondrien
    amb les xifres del panell."""
    role_people = Account.objects.filter(login__in=ROLE_LOGINS).values_list("person", flat=True)
    values = set()
    for person in Person.objects.exclude(pk=viewer.person_id).exclude(pk__in=role_people):
        values |= {person.first_name, person.last_name, person.contact_email,
                   person.id_document_number, person.phone}  # fmt: skip
    values |= {account.login for account in Account.objects.exclude(pk=viewer.pk)}
    return {value for value in values if value and len(value) >= 3}


def _leaks(html, values) -> list[str]:
    found = [value for value in values if re.search(rf"(?<!\w){re.escape(value)}(?!\w)", html)]
    numbers = Member.objects.exclude(member_number=None).values_list("member_number", flat=True)
    found += [f"núm. {n}" for n in numbers if re.search(rf"núm\.?\s*{n}(?!\d)", html)]
    return found


def test_ca_m08_02_no_personal_data_of_the_seed_in_any_panel_or_period(seeded):
    for login in DB1_ACCOUNTS:
        viewer = Account.objects.get(login=login)
        client, values = admin_client(viewer), _personal_values(viewer)
        assert values, "la llavor ha de tenir persones"
        for panel in PANELS:
            for period in views.PERIODS:
                url = reverse("administration:dashboard_panel", args=[panel])
                response = client.get(url, {"periode": period})
                assert response.status_code == 200, (login, panel, period)
                html = response.content.decode()
                assert not _leaks(html, values), (login, panel, period, _leaks(html, values))


def test_ca_m08_04_the_seed_figures_are_the_module_figures(seeded):
    today = timezone.localdate()
    starts_on, ends_on = views.bounds("year", today)
    general = panels.panel("general", starts_on, ends_on)
    economic = panels.panel("economic", starts_on, ends_on)
    activity = panels.panel("activity", starts_on, ends_on)
    by_state = members.stats(today).by_type_and_status
    assert general["active_members"].value.value == sum(
        n for (_, state), n in by_state.items() if state == Member.Status.ACTIVE
    )
    assert general["unpaid_members"].value.value == sum(
        n for (_, state), n in by_state.items() if state == Member.Status.UNPAID
    )
    module = activity_stats.stats(starts_on, ends_on)
    assert general["free_places"].value.value == module.free_places
    assert activity["occupancy"].value.value == module.occupancy_percent
    assert activity["equipment_in_use"].value.value == stock.in_use_count(today)
    reports = [department_report(d, starts_on, ends_on) for d in Department.objects.all()]
    assert economic["activity_margin"].value.value == sum(r.margins_total_cents for r in reports)
    (income,) = economic["department_income"].breakdowns
    assert income.total.value == sum(r.grants_cents + r.other_income_cents for r in reports)
    assert general["active_members"].value.value > 0  # la llavor té socis actius
