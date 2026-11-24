"""Panells general, de socis i d'activitat (T-M08-05, T-M08-07; CA-M08-03, CA-M08-04, CA-M08-09;
RN-M08-01, RN-M08-02, RN-M08-11). Les lectures dels mòduls se substitueixen per valors coneguts:
cada xifra del panell ha de ser la que torna el servei (una prova per indicador)."""

import datetime
from types import SimpleNamespace

import pytest
from django.utils import timezone

from apps.activities.stats import ActivityStats
from apps.dashboard import panels, privacy
from apps.members.services import MemberStats

ACTIVE, UNPAID, LEFT = "active", "unpaid", "left"
NOW = timezone.make_aware(datetime.datetime(2027, 3, 15, 12))
Q1 = (datetime.date(2027, 1, 1), datetime.date(2027, 3, 31))
YEAR = (datetime.date(2027, 1, 1), datetime.date(2027, 12, 31))
ACTIVITY = ActivityStats(
    places=40, confirmed=10, attended=6, expected=8,
    weekly={datetime.date(2027, 3, 8): 5, datetime.date(2027, 3, 15): 1}, free_places=7,
)  # fmt: skip


class Counted:
    def __init__(self, n):
        self.n = n

    def count(self):
        return self.n


@pytest.fixture
def services(monkeypatch):
    """Serveis de lectura amb valors coneguts. `calls` guarda les crides a `members.stats`."""
    calls = []
    by_day = {
        datetime.date(2027, 1, 1): MemberStats({("full", ACTIVE): 100}, 1, 0),
        datetime.date(2027, 1, 31): MemberStats({("full", ACTIVE): 101}, 4, 1),
        datetime.date(2027, 2, 28): MemberStats({("full", ACTIVE): 103}, 3, 2),
        datetime.date(2027, 3, 1): MemberStats({("full", ACTIVE): 103}, 0, 0),
        datetime.date(2027, 3, 15): MemberStats(
            {("full", ACTIVE): 120, ("supporter", ACTIVE): 40, ("youth", ACTIVE): 2,
             ("family", ACTIVE): 1, ("full", UNPAID): 5, ("youth", UNPAID): 1,
             ("full", LEFT): 9},
            2, 1,
        ),
    }  # fmt: skip

    def stats(on):
        calls.append(on)
        return by_day[on]

    monkeypatch.setattr(panels.members, "stats", stats)
    monkeypatch.setattr(panels.activity_stats, "stats", lambda s, e, now: ACTIVITY)
    monkeypatch.setattr(panels, "expiring", lambda days, today: Counted(days))
    monkeypatch.setattr(panels.equipment_reviews, "due_items", lambda today: Counted(4))
    monkeypatch.setattr(panels.equipment_stock, "in_use_count", lambda on: 11)
    monkeypatch.setattr(
        panels.grants_calendar, "calendar", lambda start, end: [object()] * (end - start).days
    )
    monkeypatch.setattr(panels.campaigns, "open_campaign_now", lambda: None)
    real_get = panels.business_settings.get
    monkeypatch.setattr(panels.activity_stats, "low_occupancy_count", lambda pct, today: pct // 10)
    values = {panels.TO_RENEW_DAYS: 30, panels.DEADLINE_DAYS: [30, 14, 7], panels.LOW_OCCUPANCY: 50}
    monkeypatch.setattr(
        panels.business_settings, "get", lambda key, at=None: values.get(key) or real_get(key, at)
    )
    monkeypatch.setattr(privacy, "min_group_size", lambda at=None: 3)
    return SimpleNamespace(calls=calls)


def num(block):
    return block.value.value if isinstance(block.value, privacy.Cell) else block.value


def values(blocks):
    return {code: num(block) for code, block in blocks.items() if not block.breakdowns}


def shown(breakdown, min_size=3):
    return {key: cell.label(min_size) for key, cell in breakdown.cells.items()}


def test_ca_m08_04_general_panel_reads_each_service(services):
    blocks = panels.panel("general", *Q1, now=NOW)
    assert values(blocks) == {
        "active_members": 120 + 40 + 2 + 1,  # members.stats el darrer dia (avui)
        "new_members": 4 + 3 + 2,  # altes de gener, febrer i març fins avui
        "unpaid_members": 6,
        "free_places": 7,  # activities.stats
        "low_occupancy": 5,  # activities.low_occupancy_count amb el llindar de l'ajust
        "licences_to_renew": 30,  # licences.expiring amb els dies de VC-41
        "equipment_to_review": 4,  # equipment.reviews.due_items
        "grants_closing": 30,  # grants.calendar d'avui al tram més llarg de VC-36
    }
    assert not any(block.error for block in blocks.values())


def test_ca_m08_04_members_panel_reads_each_service(services):
    blocks = panels.panel("members", *Q1, now=NOW)
    # Sense campanya oberta, el bloc dels mandats no surt.
    assert list(blocks) == [
        "unpaid_members", "licences_to_renew", "joins_and_leaves", "active_by_type", "retention",
    ]  # fmt: skip
    assert num(blocks["unpaid_members"]) == 6
    assert num(blocks["retention"]) == round(100 - 100 * (1 + 2 + 1) / 100)  # 96
    joined, left = blocks["joins_and_leaves"].breakdowns
    assert (joined.label, left.label) == ("joined", "left")
    assert {k: c.value for k, c in joined.cells.items()} == {
        datetime.date(2027, 1, 1): 4, datetime.date(2027, 2, 1): 3, datetime.date(2027, 3, 1): 2,
    }  # fmt: skip
    assert shown(left) == {
        datetime.date(2027, 1, 1): "menys de 3",
        datetime.date(2027, 2, 1): "menys de 3",
        datetime.date(2027, 3, 1): "menys de 3",
    }


def test_ca_m08_03_active_by_type_hides_small_groups(services):
    (breakdown,) = panels.panel("members", *Q1, now=NOW)["active_by_type"].breakdowns
    assert shown(breakdown) == {
        "full": "120", "supporter": "40", "youth": "menys de 3", "family": "menys de 3",
    }  # fmt: skip
    assert breakdown.total.label(3) == "163"


def test_each_member_date_is_read_once(services):
    panels.panel("general", *Q1, now=NOW)
    panels.panel("members", *Q1, now=NOW)
    assert sorted(services.calls) == sorted(
        [datetime.date(2027, 1, 31), datetime.date(2027, 2, 28), datetime.date(2027, 3, 15)] * 2
        + [datetime.date(2027, 1, 1)]
    )


def test_future_months_are_not_read_and_the_last_day_is_today(services):
    blocks = panels.panel("general", *YEAR, now=NOW)
    assert num(blocks["active_members"]) == 163 and num(blocks["new_members"]) == 9


def test_signed_mandates_only_with_an_open_campaign(services, monkeypatch):
    campaign = object()
    monkeypatch.setattr(panels.campaigns, "open_campaign_now", lambda: campaign)
    monkeypatch.setattr(panels.campaigns, "mandates_signed", lambda c: 12 if c is campaign else 0)
    assert num(panels.panel("members", *Q1, now=NOW)["signed_mandates"]) == 12


def test_ca_m08_04_activity_panel_reads_each_service(services):
    blocks = panels.panel("activity", *Q1, now=NOW)
    assert values(blocks) == {"occupancy": 25, "attendance": 75, "equipment_in_use": 11}
    (weekly,) = blocks["weekly_enrolments"].breakdowns
    assert shown(weekly) == {datetime.date(2027, 3, 8): "amagat",
                             datetime.date(2027, 3, 15): "menys de 3"}  # fmt: skip
    assert weekly.total.value == 6


def test_ca_m08_09_a_failing_service_only_breaks_its_block(services, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("servei caigut")

    monkeypatch.setattr(panels.equipment_reviews, "due_items", broken)
    blocks = panels.panel("general", *Q1, now=NOW)
    assert blocks["equipment_to_review"].error and blocks["equipment_to_review"].value is None
    assert num(blocks["active_members"]) == 163


def test_ca_m08_09_no_history_module_no_conference_block(services):
    assert "conference_attendees" not in panels.panel("communication", *Q1, now=NOW)


def test_retention_without_active_members_or_in_the_future_has_no_value(services, monkeypatch):
    monkeypatch.setattr(panels.members, "stats", lambda on: MemberStats({}, 0, 0))
    assert panels.panel("members", *Q1, now=NOW)["retention"].value is None
    later = (datetime.date(2027, 4, 1), datetime.date(2027, 6, 30))
    assert panels.panel("members", *later, now=NOW)["retention"].value is None


def test_a_period_must_start_on_the_first_day_of_a_month():
    with pytest.raises(ValueError):
        list(panels._months(datetime.date(2027, 1, 2), datetime.date(2027, 2, 28)))
    assert list(panels._months(datetime.date(2027, 12, 1), datetime.date(2027, 12, 31))) == [
        (datetime.date(2027, 12, 1), datetime.date(2027, 12, 31))
    ]


def test_breakdowns_of_non_people_indicators_are_not_hidden(services):
    reads = panels.Reads(*Q1, now=NOW)
    breakdown = reads.breakdown("equipment_in_use", {"a": 1, "b": 20})
    assert shown(breakdown) == {"a": "1", "b": "20"} and breakdown.total.value == 21


@pytest.mark.django_db
def test_rn_m08_01_real_services_on_an_empty_database_only_return_numbers():
    """Amb els serveis de debò: cap error i només xifres, cap dada de cap persona."""
    for name in ("general", "members", "activity"):
        for block in panels.panel(name, *Q1, now=NOW).values():
            assert not block.error, block.code
            assert block.value is None or isinstance(block.value.value, int)
            for breakdown in block.breakdowns:
                assert all(isinstance(c.value, int) for c in breakdown.cells.values())


MARCH = (datetime.date(2027, 3, 1), datetime.date(2027, 3, 31))


def test_rn_m08_02_a_single_count_of_people_below_the_minimum_is_hidden(services):
    """Període d'un mes amb 2 altes: el desglossament les amaga i la xifra sola també."""
    general = panels.panel("general", *MARCH, now=NOW)
    assert general["new_members"].value.label(3) == "menys de 3"
    assert general["active_members"].value.label(3) == "163"
    assert general["free_places"].value.label(3) == "7"  # places, no persones
    joined, _ = panels.panel("members", *MARCH, now=NOW)["joins_and_leaves"].breakdowns
    assert joined.total.label(3) == "menys de 3"


def test_rn_m08_02_a_retention_from_fewer_than_n_leaves_is_hidden(services):
    """1 baixa al març sobre 103 actius: el 99 % deixaria deduir la baixa (P-644)."""
    block = panels.panel("members", *MARCH, now=NOW)["retention"]
    assert num(block) == 99 and block.value.label(3) == "amagat"
    q1 = panels.panel("members", *Q1, now=NOW)["retention"]  # 4 baixes: es veu
    assert q1.value.label(3) == "96"


def test_rn_m08_02_rates_counted_on_fewer_than_n_people_are_hidden(services, monkeypatch):
    few = ActivityStats(places=40, confirmed=2, attended=1, expected=2, weekly={}, free_places=0)
    monkeypatch.setattr(panels.activity_stats, "stats", lambda s, e, now: few)
    blocks = panels.panel("activity", *Q1, now=NOW)
    assert blocks["occupancy"].value.label(3) == "amagat"
    assert blocks["attendance"].value.label(3) == "amagat"


def test_equipment_in_use_only_for_the_current_period(services):
    """L'estoc del 03 compta l'estat d'avui de les peces: un període passat no surt (P-644)."""
    past = (datetime.date(2026, 10, 1), datetime.date(2026, 12, 31))
    assert "equipment_in_use" not in panels.panel("activity", *past, now=NOW)
    assert num(panels.panel("activity", *Q1, now=NOW)["equipment_in_use"]) == 11


def test_ca_m08_04_communication_panel_reads_the_website_service(services, monkeypatch):
    """T-M08-08: subscriptors confirmats (persones: grups petits) i missatges pendents."""
    monkeypatch.setattr(
        panels.website, "counts",
        lambda: {"confirmed_subscribers": 2, "pending_contact_messages": 1},
    )  # fmt: skip
    blocks = panels.panel("communication", *Q1, now=NOW)
    assert list(blocks) == ["confirmed_subscribers", "pending_contact_messages"]
    assert blocks["confirmed_subscribers"].value.label(3) == "menys de 3"
    assert blocks["pending_contact_messages"].value.label(3) == "1"  # no són persones
