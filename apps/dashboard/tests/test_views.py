"""Pantalla del dashboard (T-M08-09; CA-M08-01, 06, 08, 12 i 14; RN-M08-08 i 09). Només dades
inventades."""

import datetime

import pytest
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.core.models import Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.dashboard import panels, views

pytestmark = pytest.mark.django_db
R = Role.Code
URL = reverse("administration:dashboard")
D = datetime.date


@pytest.fixture(autouse=True)
def empty_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.parametrize(
    ("role", "status"),
    [
        (R.INSTRUCTOR, 404),
        (R.BOARD, 404),  # S-M08-03: la junta no té DB1 a la matriu inicial
        (R.SECRETARY, 200),
        (R.COURSES_MANAGER, 200),
        (R.EQUIPMENT_MANAGER, 200),
        (R.TREASURER, 200),
        (R.HISTORY_DEPARTMENT, 200),
        (R.ADMINISTRATOR, 200),
        (R.PRESIDENT, 200),
    ],
)
def test_ca_m08_01_and_12_only_db1_opens_the_dashboard(make_admin, role, status):  # noqa: F811
    client = admin_client(make_admin(role))
    assert client.get(URL).status_code == status
    assert client.get(reverse("administration:dashboard_panel", args=["economic"])).status_code == (
        status
    )


def test_without_a_session_the_dashboard_is_not_shown(client):
    assert client.get(URL).status_code != 200


def test_an_unknown_panel_is_not_found(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.ADMINISTRATOR))
    assert client.get(reverse("administration:dashboard_panel", args=["persones"])).status_code == (
        404
    )


@pytest.mark.parametrize(
    ("period", "today", "expected"),
    [
        ("quarter", D(2027, 2, 10), (D(2027, 1, 1), D(2027, 3, 31))),  # CA-M08-08
        ("quarter", D(2027, 11, 30), (D(2027, 10, 1), D(2027, 12, 31))),
        ("month", D(2028, 2, 10), (D(2028, 2, 1), D(2028, 2, 29))),
        ("year", D(2027, 6, 1), (D(2027, 1, 1), D(2027, 12, 31))),
        ("last_12_months", D(2027, 3, 15), (D(2026, 4, 1), D(2027, 3, 31))),
        ("last_12_months", D(2027, 12, 5), (D(2027, 1, 1), D(2027, 12, 31))),
    ],
)
def test_ca_m08_08_each_period_is_whole_months_from_day_one(period, today, expected):
    assert views.bounds(period, today) == expected


def test_ca_m08_08_an_invalid_period_shows_the_default_without_error(make_admin, monkeypatch):  # noqa: F811
    seen = []
    monkeypatch.setattr(panels, "panel", lambda name, s, e, now=None: seen.append((s, e)) or {})
    client = admin_client(make_admin(R.ADMINISTRATOR))
    for value in ("dimarts", "", "1-2027"):
        assert client.get(URL, {"periode": value}).status_code == 200
    year = timezone.localdate().year
    assert set(seen) == {(D(year, 1, 1), D(year, 12, 31))}  # un sol càlcul, a la memòria cau


def test_ca_m08_06_a_block_links_to_the_detail_only_with_the_module_permission(make_admin):  # noqa: F811
    licences = reverse("administration:licences")
    secretary = admin_client(make_admin(R.SECRETARY))  # DB1 i LC4
    history = admin_client(make_admin(R.HISTORY_DEPARTMENT))  # DB1 sense LC4
    assert f'href="{licences}"' in main_of(secretary.get(URL).content.decode())
    page = main_of(history.get(URL).content.decode())
    assert "Llicències per renovar" in page and f'href="{licences}"' not in page
    assert history.get(licences).status_code == 404


def test_rn_m08_09_the_figures_are_shared_for_a_while_but_the_links_are_per_account(
    make_admin,  # noqa: F811
    monkeypatch,
):
    calls = []
    real = panels.panel
    monkeypatch.setattr(panels, "panel", lambda *a, **k: calls.append(a) or real(*a, **k))
    admin_client(make_admin(R.SECRETARY)).get(URL)
    admin_client(make_admin(R.TREASURER)).get(URL)
    assert len(calls) == 1


def test_rn_m08_11_a_failing_block_says_so_and_the_rest_is_shown(make_admin, monkeypatch):  # noqa: F811
    def broken(reads):
        raise RuntimeError("inventat")

    monkeypatch.setitem(panels.READS, "unpaid_members", broken)
    page = admin_client(make_admin(R.ADMINISTRATOR)).get(URL).content.decode()
    assert "pogut calcular" in page and "Socis actius" in page


def test_ca_m08_14_opening_every_panel_writes_nothing(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.ADMINISTRATOR))
    client.get(URL)  # la sessió ja és desada
    with CaptureQueriesContext(connection) as queries:
        for panel in ("general", "economic", "activity", "members", "communication"):
            url = reverse("administration:dashboard_panel", args=[panel])
            assert client.get(url).status_code == 200
    writes = [
        q["sql"]
        for q in queries
        if q["sql"].split(" ", 1)[0] in {"INSERT", "UPDATE", "DELETE"}
        and "django_session" not in q["sql"]
    ]
    assert writes == []


def test_rn_m08_08_the_default_period_comes_from_the_setting(make_admin, monkeypatch):  # noqa: F811
    from apps.core.models import Setting

    Setting.objects.filter(key=views.DEFAULT_PERIOD).update(initial_value="month")
    seen = []
    monkeypatch.setattr(panels, "panel", lambda name, s, e, now=None: seen.append((s, e)) or {})
    admin_client(make_admin(R.ADMINISTRATOR)).get(URL, {"periode": "no-val"})
    assert seen == [views.bounds("month", timezone.localdate())]


def test_ca_m08_13_each_account_sees_its_own_order_and_hidden_blocks(make_admin):  # noqa: F811
    from apps.dashboard import layout

    secretary, treasurer = make_admin(R.SECRETARY), make_admin(R.TREASURER)
    layout.save(secretary, ["unpaid_members", "active_members"], ["new_members"])
    page = main_of(admin_client(secretary).get(URL).content.decode())
    assert page.index("Socis impagats") < page.index("Socis actius")
    assert "Altes del període" not in page
    other = main_of(admin_client(treasurer).get(URL).content.decode())
    assert other.index("Socis actius") < other.index("Socis impagats")
    assert "Altes del període" in other
