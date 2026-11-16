"""Tramite (T-DX-10): els passos del pagament surten de l'estat del servidor, i un pas futur no
diu «Pagat» (el text de l'estat pagat només surt quan ho és)."""

import re

import pytest
from django.template.loader import render_to_string


def steps(state):
    html = render_to_string("payments/_tramite.html", {"state": state})
    return re.findall(r'<li class="tramite-pas ([^"]*)"', html), html


@pytest.mark.parametrize(
    ("state", "classes"),
    [
        ("pending", ["es-actual", "", ""]),
        ("in_progress", ["es-fet", "es-actual", ""]),
        ("failed", ["es-fet", "es-avis", ""]),
        ("timed_out", ["es-fet", "es-avis", ""]),
        ("paid", ["es-fet", "es-fet", "es-fet es-final"]),
    ],
)
def test_steps_follow_the_server_state(state, classes):
    found, html = steps(state)
    assert [c.strip() for c in found] == classes
    assert html.count('aria-current="step"') == (0 if state == "paid" else 1)
    assert ("Pagat" in html) is False  # el pas 3 es diu «Pagament completat»


def test_a_charge_that_cannot_be_paid_has_no_steps():
    found, _ = steps("closed")
    assert found == []
