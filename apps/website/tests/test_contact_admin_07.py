"""Safata i motius de contacte a l'administració (WP5 i WP8; P-M07-D, RN-M07-07 i 14; CA-M07-02 i
18). Només dades inventades."""

import pytest
from django.urls import reverse

from apps.core.models import AuditEntry, OutgoingEmail, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website import admin_views, contact
from apps.website.models import ContactMessage, ContactReason
from apps.website.tests.test_contact_07 import _message

pytestmark = pytest.mark.django_db
R = Role.Code
INBOX = reverse("administration:website_contact")
REASONS = reverse("administration:website_contact_reasons")


def _url(name, pk):
    return reverse(f"administration:website_contact_{name}", args=[pk])


def test_ca_m07_02_without_a_session_or_without_wp5_nothing_is_shown(client, make_admin):  # noqa: F811
    message = _message()
    assert client.get(INBOX).status_code != 200
    treasurer = admin_client(make_admin(R.TREASURER))
    for url in (INBOX, _url("message", message.pk), REASONS):
        assert treasurer.get(url).status_code == 404
    response = treasurer.post(_url("close", message.pk), {"reason": "Prova"})
    assert response.status_code == 404
    message.refresh_from_db()
    assert message.status == ContactMessage.Status.NEW


def test_rn_m07_07_the_inbox_lists_only_the_reasons_of_the_account(make_admin):  # noqa: F811
    _message("Quotes")
    courses = _message("Cursos")
    ContactReason.objects.get(name="Cursos").roles.set([Role.objects.get(code=R.ADMINISTRATOR)])
    secretary = admin_client(make_admin(R.SECRETARY))
    page = secretary.get(INBOX).content.decode()
    assert "Quotes" in page and _url("message", courses.pk) not in page
    assert "Cursos" not in page  # ni a la llista ni al filtre
    assert secretary.get(_url("message", courses.pk)).status_code == 404


def test_the_filter_by_reason_ignores_a_reason_out_of_scope(make_admin):  # noqa: F811
    quotes = _message("Quotes")
    secretary = admin_client(make_admin(R.SECRETARY))
    other = ContactReason.objects.create(name="Fora d'abast")
    page = secretary.get(INBOX, {"motiu": other.pk}).content.decode()
    assert _url("message", quotes.pk) in page


def test_reply_from_the_screen_sends_the_answer_and_closes_the_message(make_admin):  # noqa: F811
    message = _message()
    secretary = admin_client(make_admin(R.SECRETARY))
    page = secretary.get(_url("message", message.pk)).content.decode()
    assert "inventat@example.com" in page and "Envia la resposta" in page
    assert str(contact.CLOSE_REASON_HELP) in page
    response = secretary.post(_url("reply", message.pk), {"answer": "Resposta inventada."})
    assert response.status_code == 302 and response["Location"] == INBOX
    message.refresh_from_db()
    assert message.status == ContactMessage.Status.ANSWERED
    assert OutgoingEmail.objects.get().to_address == "inventat@example.com"
    # Ja respost: no hi ha cap formulari i una segona resposta es rebutja.
    assert "Envia la resposta" not in secretary.get(_url("message", message.pk)).content.decode()
    response = secretary.post(_url("reply", message.pk), {"answer": "Una altra"}, follow=True)
    assert "ja està respost o tancat" in response.content.decode()
    assert OutgoingEmail.objects.count() == 1


def test_closing_from_the_screen_needs_a_reason(make_admin):  # noqa: F811
    message = _message()
    secretary = admin_client(make_admin(R.SECRETARY))
    response = secretary.post(_url("close", message.pk), {"reason": ""})
    assert response.status_code == 200 and "Hi ha 1 error" in response.content.decode()
    response = secretary.post(_url("close", message.pk), {"reason": "Resolt per telèfon"})
    assert response.status_code == 302
    message.refresh_from_db()
    assert (message.status, message.closed_reason) == ("closed", "Resolt per telèfon")


def test_ca_m07_18_wp8_only_the_administrator_manages_the_reasons(make_admin):  # noqa: F811
    secretary = admin_client(make_admin(R.SECRETARY))
    assert secretary.get(REASONS).status_code == 404
    data = {"name": "Inventat", "order": 9, "roles": [], "active": "on"}
    url = reverse("administration:website_contact_reason_add")
    assert secretary.post(url, data).status_code == 404
    assert not ContactReason.objects.filter(name="Inventat").exists()
    admin = admin_client(make_admin(R.ADMINISTRATOR))
    assert "Quotes" in admin.get(REASONS).content.decode()


def test_a_reason_is_created_reassigned_and_deactivated_with_a_trace(make_admin):  # noqa: F811
    admin = admin_client(make_admin(R.ADMINISTRATOR))
    treasurer = Role.objects.get(code=R.TREASURER)
    data = {"name": "Botiga inventada", "order": 7, "roles": [treasurer.pk], "active": "on"}
    response = admin.post(reverse("administration:website_contact_reason_add"), data)
    assert response.status_code == 302
    reason = ContactReason.objects.get(name="Botiga inventada")
    assert list(reason.roles.all()) == [treasurer] and reason.active
    response = admin.post(
        _url("reason_edit", reason.pk), {**data, "name": "Botiga", "roles": [], "active": ""}
    )  # desactivar: no surt al formulari públic, però no s'esborra
    assert response.status_code == 302
    reason.refresh_from_db()
    assert not reason.active and not reason.roles.exists()
    entries = AuditEntry.objects.filter(action=admin_views.ACTION_REASON).order_by("pk")
    assert entries.count() == 2
    assert entries[0].details["before"] == {}
    assert entries[1].details["before"] == {
        "name": "Botiga inventada", "order": 7, "active": True, "roles": [R.TREASURER],
    }  # fmt: skip
    assert entries[1].details["after"] == {
        "name": "Botiga", "order": 7, "active": False, "roles": [],
    }  # fmt: skip
