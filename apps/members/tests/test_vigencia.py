"""Vigencia (T-DX-13): el compte enrere el calcula el servidor amb la data local, i els dies d'avís
de la quota són els dels recordatoris (VC-02), sense cap valor nou al codi."""

from datetime import timedelta

import pytest
from django.template import Context, Template

from apps.core.models import Setting
from apps.members import settings as values
from apps.members.fee_rules import local_today
from apps.members.templatetags.vigencia import in_fee_warning_window, vigencia

pytestmark = pytest.mark.django_db


def offsets(value):
    Setting.objects.filter(key=values.FEE_REMINDER_OFFSETS).update(initial_value=value)


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


def test_a_far_warning_day_stretches_the_scale():
    offsets([-90, 0])
    result = vigencia(local_today() + timedelta(days=100), "quota")
    assert result["window"] == 90 and result["marks"] == [90] and result["level"] == "ok"


def test_a_licence_warns_from_the_to_renew_days_setting():
    # T-DX-105: el dia d'avís de la llicència és l'ajust «Per renovar» (VC-41), el mateix que fa
    # sortir l'estat «Per renovar» al 06. Cap valor nou al codi.
    Setting.objects.filter(key="licences.to_renew_days").update(initial_value=20)
    far = vigencia(local_today() + timedelta(days=30), "llicencia")
    assert far["marks"] == [20] and far["level"] == "ok"
    assert vigencia(local_today() + timedelta(days=20), "llicencia")["level"] == "avis"
    assert vigencia(local_today() - timedelta(days=1), "llicencia")["level"] == "error"


def test_no_date_shows_nothing():
    assert vigencia(None) == {"show": False}


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


def test_the_home_countdown_window_is_the_first_reminder_day():
    """T-DX-60: a l'inici, el compte enrere de la quota només des del primer dia d'avís (VC-02)."""
    today = local_today()
    assert in_fee_warning_window(today + timedelta(days=15))  # per defecte, 15 dies abans
    assert not in_fee_warning_window(today + timedelta(days=16))
    assert in_fee_warning_window(today - timedelta(days=1))
    offsets([-30, 0])
    assert in_fee_warning_window(today + timedelta(days=30))
    offsets([15, 30])  # cap avís abans del venciment: mai
    assert not in_fee_warning_window(today)
    assert not in_fee_warning_window(None)
