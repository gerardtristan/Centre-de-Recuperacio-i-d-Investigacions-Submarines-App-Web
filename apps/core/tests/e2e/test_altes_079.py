"""Alta aprovada i invitació del compte personal al navegador (T-M01-14; 079, RN-M01-87 i 88;
CA-M01-90 i CA-M01-93). Cada pantalla es desa a 1280, 390 i 320 px (clar i fosc) i es comprova
que a 320 px no es desplaça de costat. El formulari de la invitació s'omple només amb el teclat.
"""

import datetime
import re

import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.accounts.models import Account
from apps.core.models import OutgoingEmail, Person
from apps.members.models import Member, MemberRequest
from conftest import PASSWORD

from .conftest import login_admin

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH


def pending_join(builder, first, last, email, **fields):
    person = Person.objects.create(
        first_name=first, last_name=last, origin=Person.Origin.WEB, contact_email=email
    )
    if "guardian_first_name" not in fields:
        Person.objects.filter(pk=person.pk).update(
            id_document_type="dni", id_document_number="12345678Z"
        )
    return MemberRequest.objects.create(
        kind=MemberRequest.Kind.JOIN,
        person=person,
        requested_type=builder.supporter,
        channel=MemberRequest.Channel.WEB,
        **fields,
    )


def test_approval_sends_the_invitation_and_the_person_creates_the_account(
    page, live_server, builder, secretary, review
):
    join = pending_join(
        builder,
        "Laia",
        "Dorada Rap",
        "laia.dorada@example.org",
        birth_date=datetime.date(1990, 5, 20),
    )
    login_admin(page, live_server.url, secretary.login)
    page.goto(f"{live_server.url}/{ADMIN}/socis/altes/")
    expect(page.get_by_role("heading", name="Altes pendents")).to_be_visible()
    review("altes-pendents")
    page.get_by_role("button", name="Aprova l'alta").click()
    expect(page.get_by_text("Se li ha enviat el correu d'accés")).to_be_visible()
    review("alta-aprovada")

    member = Member.objects.get(person=join.person)
    page.goto(f"{live_server.url}/{ADMIN}/socis/{member.pk}/")
    expect(page.get_by_role("button", name="Envia la invitació del compte")).to_be_visible()
    review("fitxa-amb-invitacio")
    page.context.clear_cookies()  # la persona obre el correu en un altre navegador

    email = OutgoingEmail.objects.get(template="invitacio-compte")
    link = re.search(r"http\S+/compte/invitacio/\S+", email.body_text).group(0)
    path = link.split("/compte/invitacio/")[1]
    page.goto(f"{live_server.url}/compte/invitacio/{path}")
    expect(page).to_have_url(f"{live_server.url}/compte/invitacio/")  # sense el testimoni
    expect(page.get_by_role("heading", name="Crear el compte")).to_be_visible()
    review("invitacio")

    # Només amb el teclat: els dos camps i el botó.
    page.get_by_label("Contrasenya nova").focus()
    page.keyboard.type(PASSWORD)
    page.keyboard.press("Tab")
    page.keyboard.type(PASSWORD)
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Crear el compte")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Compte creat")).to_be_visible()
    review("compte-creat")
    account = Account.objects.get(kind=Account.Kind.PERSONAL, person=join.person)
    assert account.status == Account.Status.ACTIVE

    page.goto(f"{live_server.url}/compte/invitacio/{path}")  # el mateix enllaç, una altra vegada
    expect(page.get_by_text("Aquest enllaç no és vàlid o ha caducat.")).to_be_visible()
    review("invitacio-no-valida")

    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill("laia.dorada@example.org")
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page.get_by_role("button", name="Sortir")).to_be_visible()


def test_minor_without_document_shows_the_possible_duplicate(
    page, live_server, builder, secretary, review
):
    birth = datetime.date(2015, 5, 5)
    guardian = {
        "guardian_first_name": "Marta",
        "guardian_last_name": "Petit Inventat",
        "guardian_id_document_type": "dni",
        "guardian_id_document_number": "55555555K",
        "guardian_email": "marta.petit@example.org",
        "guardian_phone": "600000001",
    }
    other = Person.objects.create(
        first_name="Nil", last_name="Petit Inventat", origin=Person.Origin.WEB, birth_date=birth
    )
    Member.objects.create(
        person=other,
        member_number=77,
        type=builder.supporter,
        status=Member.Status.ACTIVE,
        joined_on=datetime.date(2024, 1, 1),
    )
    pending_join(builder, "Nil", "Petit Inventat", "", birth_date=birth, **guardian)

    login_admin(page, live_server.url, secretary.login)
    page.goto(f"{live_server.url}/{ADMIN}/socis/altes/")
    expect(page.get_by_text("Possible duplicat d'un menor sense document")).to_be_visible()
    expect(page.get_by_text("soci número 77")).to_be_visible()
    review("menor-possible-duplicat")
    page.get_by_label("He comprovat el document del pare").check()
    page.get_by_label("He revisat les persones amb el mateix nom").check()
    page.get_by_role("button", name="Aprova l'alta").click()
    expect(page.get_by_text("No se li ha enviat cap correu d'accés")).to_be_visible()
    review("menor-aprovat")
