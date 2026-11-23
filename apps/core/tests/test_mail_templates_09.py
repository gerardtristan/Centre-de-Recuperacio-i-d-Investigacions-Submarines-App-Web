"""Plantilles del nucli per al 09 (T-M09-13 i S-M09-13): l'avís de marge baix i el de reobertura
d'un període. Només el nom de l'activitat, el període, els imports i el motiu: cap dada personal.
Només dades inventades."""

import pytest

from apps.core import mail

pytestmark = pytest.mark.django_db


def test_low_margin_notice():
    email = mail.queue_email(
        "avis-marge-baix", to="tresoreria@example.org",
        context={"activity": "Sortida inventada", "margin": "−10,00 €", "threshold": "0,00 €"},
    )  # fmt: skip
    assert "Sortida inventada" in email.subject
    assert "−10,00 €" in email.body_text and "0,00 €" in email.body_text


def test_period_reopened_notice():
    email = mail.queue_email(
        "avis-reobertura-periode", to="junta@example.org",
        context={"period": "2027", "reason": "Un moviment del banc arribat tard (inventat)."},
    )  # fmt: skip
    assert "2027" in email.subject
    assert "Un moviment del banc arribat tard (inventat)." in email.body_text
