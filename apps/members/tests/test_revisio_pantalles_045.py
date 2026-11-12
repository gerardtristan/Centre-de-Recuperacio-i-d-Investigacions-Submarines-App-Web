"""T-M01-45: correccions de la revisió de pantalles que es poden provar sense navegador.

Una prova per incidència, amb el número del punt de la fila del pla. Les de teclat, focus i
320 px són a `apps/core/tests/e2e/test_revisio_pantalles_045.py`.

Només dades inventades.
"""

import re

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.members.models import MemberRequest
from apps.members.tests.test_admissions import a_person, a_request
from apps.members.tests.test_member_requests import (
    CHANGE,
    LEAVE,
    account_for,
    admin_client,
    change_request,
    leave_request,
    make_member,
    marta,  # noqa: F401 (fixture)
    personal_client,
)

pytestmark = pytest.mark.django_db

JOIN_LIST = "administration:join_requests"
APPROVE = "administration:join_approve"


# --- Punt 1 (T-M01-14): l'error d'una alta pendent diu de quina sol·licitud és -------------------


def needs_identity_check(first, last, email):
    """Sol·licitud amb el document d'una persona que ja hi és: cal la casella d'identitat."""
    person = a_person(first, last, email=email)
    return a_request(person, warning=[{"match": "document", "person_id": person.pk}])


def test_point_1_the_error_of_a_pending_join_names_the_request(make_admin):  # noqa: F811
    needs_identity_check("Laia", "Dorada", "laia@example.org")
    failing = needs_identity_check("Ona", "Sardina", "ona@example.org")
    client = admin_client(make_admin("secretary"))
    response = client.post(reverse(APPROVE, args=[failing.pk]))  # sense marcar la casella
    (message,) = [str(m) for m in get_messages(response.wsgi_request)]
    assert message == ("Ona Sardina: Cal confirmar que has comprovat la identitat de la persona.")
    failing.refresh_from_db()
    assert failing.status == MemberRequest.Status.PENDING
    page = client.get(reverse(JOIN_LIST)).content.decode()
    assert "Ona Sardina: Cal confirmar" in page and "Laia Dorada: Cal confirmar" not in page


# --- Punt 5 (T-M01-17): títols de les sol·licituds personals ------------------------------------


def h_tags(html, level):
    return [
        re.sub(r"<[^>]+>", "", t).strip()
        for t in re.findall(rf"<h{level}[^>]*>(.*?)</h{level}>", html, re.S)
    ]


def test_point_5_full_member_page_is_titled_type_change():
    """El soci de ple dret no veia «Canvi a ple dret» com a títol d'una pantalla que li explica
    el pas a simpatitzant: la pantalla es diu com l'entrada del menú, «Canvi de tipus»."""
    member = make_member(type_code="full")
    html = main_of(personal_client(account_for(member)).get(reverse(CHANGE)).content.decode())
    assert h_tags(html, 1) == ["Canvi de tipus"]
    assert "Canvi a ple dret" not in html


def test_point_5_pending_titles_have_the_same_shape(marta):  # noqa: F811
    member, account = marta
    change_request(member)
    client = personal_client(account)
    change = h_tags(main_of(client.get(reverse(CHANGE)).content.decode()), 2)
    assert change == ["Ja tens una sol·licitud de canvi de tipus pendent"]
    other = make_member("Pau")
    leave_request(other)
    leave = h_tags(
        main_of(personal_client(account_for(other)).get(reverse(LEAVE)).content.decode()), 2
    )
    assert leave == ["Ja tens una sol·licitud de baixa pendent"]


def test_point_5_create_a_leave_does_not_weigh_like_edit(make_admin):  # noqa: F811
    """«Crea una baixa» és una acció de menys ús i amb conseqüències: botó de text, no com
    «Edita les dades»."""
    member = make_member("Fitxa")
    html = (
        admin_client(make_admin("secretary"))
        .get(reverse("administration:member_detail", args=[member.pk]))
        .content.decode()
    )
    edit = re.search(r'<a class="([^"]+)" href="[^"]+/edita/">Edita les dades</a>', html)
    leave = re.search(r'<a class="([^"]+)" href="[^"]+/baixa/nova/">Crea una baixa</a>', html)
    assert edit.group(1) == "boto boto-petit"
    assert "boto-text" in leave.group(1).split()


# --- Punt 6: el selector de tema i el menú personal en l'ordre en què es veuen -------------------


def test_point_6_theme_selector_comes_before_the_personal_menu_in_tab_order(marta):  # noqa: F811
    _member, account = marta
    html = personal_client(account).get(reverse("core:home")).content.decode()
    assert 0 < html.index('class="selector-tema"') < html.index('class="navegacio-compte"')
