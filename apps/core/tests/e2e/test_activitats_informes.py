"""Informes d'activitats al navegador (T-M02-24b): la persona responsable de cursos obre
l'ocupació des del menú, i d'aquí els participants i l'horari per imprimir. Pantalles a 1280, 390
i 320 px (clar i fosc). Només dades inventades."""

import re

import pytest
from django.db import transaction
from playwright.sync_api import expect

from apps.activities import enrolment, sessions
from apps.activities.models import Session
from apps.activities.tests.helpers import (
    BEFORE_DEADLINE,
    a_member,
    a_place,
    an_open_course,
    moment,
)

from .conftest import login_admin, make_admin, menu_entry

pytestmark = pytest.mark.e2e


def test_the_manager_prints_the_reports(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    course = an_open_course(manager, title="Curs inventat d'informes", max_places=6)
    sessions.add_session(
        course, by=manager, kind=Session.Kind.POOL, starts_at=moment(2027, 6, 14, 9),
        ends_at=moment(2027, 6, 14, 11), place=a_place(manager),
    )  # fmt: skip
    account = a_member("Alumna")
    with transaction.atomic():
        enrolment.enrol(course, account.person, channel="account", actor=account,
                        now=BEFORE_DEADLINE)  # fmt: skip

    login_admin(page, live_server.url, manager.login)
    menu_entry(page, "Informes d'activitats").click()
    expect(page.get_by_role("heading", name="Informes d'activitats")).to_be_visible()
    review("informes-ocupacio")
    page.get_by_role("link", name=re.compile(r"^Participants")).click()
    expect(page.get_by_role("rowheader", name="Alumna Prova")).to_be_visible()
    review("informes-participants")
    page.get_by_role("link", name="Torna als informes").click()
    page.get_by_role("link", name=re.compile(r"^Horari")).click()
    expect(page.get_by_role("heading", name="Curs inventat d'informes")).to_be_visible()
    review("informes-horari")
