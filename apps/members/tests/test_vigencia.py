"""Vigencia (T-DX-13): el compte enrere el calcula el servidor amb la data local, i els dies d'avís
de la quota són els dels recordatoris (VC-02), sense cap valor nou al codi."""

from datetime import timedelta

import pytest
from django.template import Context, Template
from django.test import override_settings

from apps.members.fee_rules import local_today
from apps.members.templatetags.vigencia import vigencia

OFFSETS = (-15, -1, 0, 15, 30)


@override_settings(MEMBER_FEE_REMINDER_OFFSETS=OFFSETS)
@pytest.mark.parametrize(
    ("days", "level", "bar"),
    [
        (90, "ok", 60),
        (40, "ok", 40),
        (15, "avis", 15),
        (3, "avis", 3),
        (0, "avis", 0),
        (-4, "error", 0),
    ],
)
def test_days_level_and_bar_come_from_the_server_date(days, level, bar):
    result = vigencia(local_today() + timedelta(days=days), "quota")
    assert (result["days"], result["level"], result["bar"]) == (days, level, bar)
    assert result["marks"] == [15, 1]  # els recordatoris d'abans del venciment (VC-02)
    assert result["window"] == 60


@override_settings(MEMBER_FEE_REMINDER_OFFSETS=(-90, 0))
def test_a_far_warning_day_stretches_the_scale():
    result = vigencia(local_today() + timedelta(days=100), "quota")
    assert result["window"] == 90 and result["marks"] == [90] and result["level"] == "ok"


def test_a_licence_has_no_warning_days_and_only_turns_red_when_expired():
    soon = vigencia(local_today() + timedelta(days=2), "llicencia")
    assert soon["marks"] == [] and soon["level"] == "ok"
    assert vigencia(local_today() - timedelta(days=1), "llicencia")["level"] == "error"


def test_no_date_shows_nothing():
    assert vigencia(None) == {"show": False}


@override_settings(MEMBER_FEE_REMINDER_OFFSETS=OFFSETS)
@pytest.mark.parametrize(
    ("days", "text"),
    [(1, "Queda 1 dia"), (23, "Queden 23 dies"), (0, "Venç avui"), (-2, "Va vèncer fa 2 dies")],
)
def test_the_text_says_the_same_as_the_ruler(days, text):
    until = local_today() + timedelta(days=days)
    html = Template("{% load vigencia %}{% vigencia until 'quota' %}").render(
        Context({"until": until})
    )
    assert text in html
    assert "style=" not in html
