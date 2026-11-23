"""Plantilles del nucli per als avisos dels ajuts (T-M09A-06 i T-M09A-15): tancament de la
convocatòria, resposta prevista, justificació i requeriment d'esmena. Només l'organisme, la convocatòria, les
dates i la referència de la sol·licitud: cap dada personal. Només dades inventades."""

import pytest

from apps.core import mail

pytestmark = pytest.mark.django_db
GRANT = {"call": "Convocatòria inventada", "body": "Organisme inventat", "application_id": 7}


def test_closing_notice():
    email = mail.queue_email(
        "avis-ajut-tancament", to="tresoreria@example.org",
        context={**GRANT, "closes_on": "30/04/2027", "days": 14},
    )  # fmt: skip
    assert "Convocatòria inventada" in email.subject and "14" in email.subject
    assert "30/04/2027" in email.body_text and "sol·licitud 7" in email.body_text


def test_response_notice():
    email = mail.queue_email(
        "avis-ajut-resposta", to="tresoreria@example.org",
        context={**GRANT, "submitted_on": "01/02/2027", "expected_on": "02/05/2027"},
    )  # fmt: skip
    assert "Convocatòria inventada" in email.subject
    assert "01/02/2027" in email.body_text and "02/05/2027" in email.body_text


def test_justification_notice():
    email = mail.queue_email(
        "avis-ajut-justificacio", to="tresoreria@example.org",
        context={**GRANT, "due_on": "31/03/2028", "days": 30},
    )  # fmt: skip
    assert "Convocatòria inventada" in email.subject and "30" in email.subject
    assert "31/03/2028" in email.body_text and "sol·licitud 7" in email.body_text


@pytest.mark.parametrize("days", [0, 7])
def test_requirement_notice_first_and_before_the_deadline(days):
    email = mail.queue_email(
        "avis-ajut-requeriment", to="tresoreria@example.org",
        context={**GRANT, "due_on": "15/06/2027", "days": days},
    )  # fmt: skip
    assert "15/06/2027" in email.body_text and "Organisme inventat" in email.body_text
    assert ("d'aquí a 7 dies" in email.subject) == bool(days)
