"""T-M09A-05: calendari dels ajuts (HU-M09A-03; AJ3), servei i pantalla. Només dades
inventades."""

from datetime import date

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.models import Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.grants import calendar as c
from apps.grants import requirements as r
from apps.grants.tests.test_justification import granted  # noqa: F401 (fixture)
from apps.grants.tests.test_requirements import record
from apps.grants.tests.test_resolution import submitted  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db
PAGE = reverse("administration:grants_calendar")


def kinds(events):
    return [(e.day, e.kind) for e in events]


def test_tancament_i_resposta_prevista(submitted, call):  # noqa: F811
    call.closes_on = date(2027, 1, 31)
    call.save()
    events = c.calendar(date(2027, 1, 1), date(2027, 12, 31))
    assert kinds(events) == [(date(2027, 1, 31), "close"), (date(2027, 5, 2), "response")]
    assert events[1].application == submitted and events[0].application is None
    assert events[0].call == "Medi marí" and events[0].body == "Diputació Inventada"
    assert c.calendar(date(2027, 2, 1), date(2027, 4, 30)) == []


def test_justificacio_amb_proroga_i_requeriments_oberts(granted, call, treasurer):  # noqa: F811
    call.justification_due_on = date(2028, 3, 31)
    call.save()
    requirement = record(granted, treasurer)  # data límit 15/10/2027
    year = (date(2027, 1, 1), date(2028, 12, 31))
    assert kinds(c.calendar(*year)) == [
        (date(2027, 10, 15), "requirement"),
        (date(2028, 3, 31), "justify"),
    ]
    r.set_justification_extension(
        granted, extended_to=date(2028, 6, 30), reason="Pròrroga inventada", by=treasurer
    )
    r.answer_requirement(requirement, answered_on=date(2027, 10, 10), by=treasurer)
    assert kinds(c.calendar(*year)) == [(date(2028, 6, 30), "justify")]


def test_la_pantalla_mostra_el_mes_i_les_properes(login_as, submitted, make_admin):  # noqa: F811
    client = login_as(make_admin(Role.Code.BOARD), AREA_ADMIN)
    html = main_of(client.get(PAGE, {"mes": "2027-05"}).content.decode())
    assert "Calendari d'ajuts" in html and "Maig 2027" in html
    assert "Resposta prevista" in html and f"Núm. {submitted.pk} · Presentada" in html
    assert "?mes=2027-04" in html and "?mes=2027-06" in html
    html = main_of(client.get(PAGE, {"mes": "no-és-un-mes"}).content.decode())
    assert "Mes anterior" in html  # un mes que no val torna al d'avui


def test_sense_aj3_no_es_troba(login_as, make_admin):  # noqa: F811
    assert login_as(make_admin(Role.Code.SECRETARY), AREA_ADMIN).get(PAGE).status_code == 404
