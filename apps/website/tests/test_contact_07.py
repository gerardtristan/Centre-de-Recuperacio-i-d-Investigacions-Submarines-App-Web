"""Contacte (T-M07-11 i T-M07-12; CA-M07-11 i 12, RN-M07-07, 08 i 14). Només dades inventades."""

import time
from datetime import timedelta

import pytest
from django.core import signing
from django.urls import reverse
from django.utils import timezone

from apps.core import business_settings
from apps.core.models import AuditEntry, LegalText, OutgoingEmail, Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import contact, tasks
from apps.website.models import ContactMessage, ContactReason

pytestmark = pytest.mark.django_db
R = Role.Code
URL = "/contacte/"


@pytest.fixture
def enabled():
    Setting.objects.filter(key=contact.ENABLED).update(initial_value=True)


@pytest.fixture
def privacy():
    return LegalText.objects.create(kind="privacy", version=1, content="Política inventada")


def _started(seconds_ago=10):
    return signing.dumps(time.time() - seconds_ago, salt=contact._SALT)


def _data(**extra):
    data = {
        "reason": ContactReason.objects.get(name="Quotes").pk,
        "name": "Nom Inventat",
        "email": "inventat@example.com",
        "body": "Quan es paga la quota?",
        "accept_privacy": "on",
        "web": "",
        "started": _started(),
    }
    return {**data, **extra}


def test_the_initial_reasons_go_to_the_secretary():
    names = list(ContactReason.objects.values_list("name", flat=True))
    assert names == ["Cursos", "Sortides", "Quotes", "Llicències", "Altres"]
    for reason in ContactReason.objects.all():
        assert list(reason.roles.values_list("code", flat=True)) == [R.SECRETARY]


def test_switched_off_the_form_is_not_found(client, privacy):
    assert business_settings.get(contact.ENABLED) is False
    assert client.get(URL).status_code == 404
    assert client.post(URL, _data()).status_code == 404
    assert not ContactMessage.objects.exists()


def test_ca_m07_11_a_message_is_saved_without_ip_and_the_answer_is_generic(
    client, enabled, privacy
):
    response = client.post(URL, _data())
    assert response.status_code == 303
    assert response["Location"] == reverse("website:contact")
    message = ContactMessage.objects.get()
    assert message.reason.name == "Quotes" and message.privacy_text == privacy
    assert not any("ip" in field.name for field in ContactMessage._meta.fields)
    page = client.get(URL).content.decode()
    assert "Missatge enviat" in page and "inventat@example.com" not in page


@pytest.mark.parametrize(
    "robot", [{"web": "http://spam.example"}, {"started": "massa ràpid"}, {"started": "fals"}]
)
def test_ca_m07_11_a_robot_gets_the_same_answer_and_nothing_is_saved(
    client, enabled, privacy, robot
):
    if robot.get("started") == "massa ràpid":
        robot = {"started": _started(1)}
    response = client.post(URL, _data(**robot))
    assert response.status_code == 303 and response["Location"] == reverse("website:contact")
    assert "Missatge enviat" in client.get(URL).content.decode()
    assert not ContactMessage.objects.exists()


def test_ca_m07_11_too_many_requests_from_one_origin_save_nothing(
    client, enabled, privacy, settings
):
    settings.JOIN_FORM_ORIGIN_MAX = 1
    client.post(URL, _data())
    response = client.post(URL, _data(body="Un altre"))
    assert response.status_code == 303
    assert ContactMessage.objects.count() == 1


def test_without_a_privacy_text_nobody_can_write(client, enabled):
    page = client.get(URL).content.decode()
    assert "no es pot escriure al club" in page and "<form" not in page
    client.post(URL, _data())
    assert not ContactMessage.objects.exists()


def test_the_form_has_the_honeypot_and_the_signed_time(client, enabled, privacy):
    page = client.get(URL).content.decode()
    assert 'name="web"' in page and 'name="started"' in page


def _message(reason="Quotes", **fields):
    privacy = LegalText.objects.get_or_create(kind="privacy", version=1, defaults={"content": "P"})
    return ContactMessage.objects.create(
        reason=ContactReason.objects.get(name=reason), name="Nom Inventat",
        email="inventat@example.com", body="Text", privacy_text=privacy[0], **fields,
    )  # fmt: skip


def test_rn_m07_07_the_inbox_only_shows_the_reasons_of_the_account_roles(make_admin):  # noqa: F811
    quotes, courses = _message("Quotes"), _message("Cursos")
    ContactReason.objects.get(name="Cursos").roles.set([Role.objects.get(code=R.TREASURER)])
    assert list(contact.visible_to(make_admin(R.SECRETARY))) == [quotes]
    # L'administrador té WP5, però cap motiu no és del seu rol fins que el reparteix (WP8).
    assert not contact.visible_to(make_admin(R.ADMINISTRATOR)).exists()
    # El tresorer és al rol del motiu, però no té WP5.
    assert not contact.visible_to(make_admin(R.TREASURER)).exists()
    assert courses.pk


def test_closing_needs_a_reason_and_is_recorded(make_admin):  # noqa: F811
    from django.core.exceptions import ValidationError

    secretary, message = make_admin(R.SECRETARY), _message()
    with pytest.raises(ValidationError):
        contact.close(message, actor=secretary, reason=" ")
    contact.close(message, actor=secretary, reason="Resolt per telèfon")
    message.refresh_from_db()
    assert message.status == ContactMessage.Status.CLOSED and message.finished_at
    entry = AuditEntry.objects.get(action=contact.ACTION_CLOSED)
    assert (entry.old_value, entry.new_value, entry.reason) == (
        "new",
        "closed",
        "Resolt per telèfon",
    )
    with pytest.raises(ValidationError):
        contact.close(message, actor=secretary, reason="Un altre cop")


def test_closing_out_of_scope_is_not_found(make_admin):  # noqa: F811
    with pytest.raises(ContactMessage.DoesNotExist):
        contact.close(_message(), actor=make_admin(R.ADMINISTRATOR), reason="Fora d'abast")
    with pytest.raises(ContactMessage.DoesNotExist):
        contact.close(_message(), actor=make_admin(R.TREASURER), reason="Sense permís")


def test_ca_m07_12_finished_messages_past_the_term_are_deleted_once_with_a_trace():
    now = timezone.now()
    old = _message(status="closed", finished_at=now - timedelta(days=200))
    recent = _message(status="closed", finished_at=now - timedelta(days=100))
    new_but_old = _message()
    ContactMessage.objects.filter(pk=new_but_old.pk).update(created_at=now - timedelta(days=400))

    assert contact.purge_finished(now) == 1
    assert set(ContactMessage.objects.all()) == {recent, new_but_old}
    entry = AuditEntry.objects.get(action=contact.ACTION_DELETED)
    assert entry.target_id == str(old.pk)
    assert "Text" not in str(entry.details) and "inventat" not in str(entry.details)
    assert contact.purge_finished(now) == 0
    assert AuditEntry.objects.filter(action=contact.ACTION_DELETED).count() == 1


def test_ca_m07_12_the_term_is_the_setting():
    Setting.objects.filter(key=contact.RETENTION_MONTHS).update(initial_value=1)
    _message(status="closed", finished_at=timezone.now() - timedelta(days=40))
    assert contact.purge_finished() == 1


def test_the_purge_runs_every_day():
    periodic = tasks.app.periodic_registry.periodic_tasks[("website.purge_contact_messages", "")]
    assert periodic.cron == "35 3 * * *"


def test_a_visitor_who_fixes_an_error_quickly_is_not_taken_for_a_robot(client, enabled, privacy):
    """Revisió de la #580: el formulari amb errors torna amb la mateixa hora d'obertura, i
    corregir-lo en menys de 3 segons no perd el missatge."""
    import re

    page = client.post(URL, _data(body="")).content.decode()
    started = re.search(r'name="started" value="([^"]+)"', page).group(1)
    client.post(URL, _data(started=started))
    assert ContactMessage.objects.count() == 1


@pytest.mark.parametrize("method", ["head", "put"])
def test_switched_off_any_method_is_not_found(client, method):
    assert getattr(client, method)(URL).status_code == 404


# --- Correus (T-M07-13b) ---------------------------------------------------------------------


def _with_email(account, address):
    account.notification_email = address
    account.save(update_fields=["notification_email"])
    return account


def test_ca_m07_11_only_the_accounts_of_the_reason_get_the_notice_without_the_visitor_data(
    client,
    enabled,
    privacy,
    make_admin,  # noqa: F811
):
    _with_email(make_admin(R.SECRETARY), "secretaria@example.com")
    _with_email(make_admin(R.ADMINISTRATOR), "admin@example.com")  # WP5, cap motiu seu
    _with_email(make_admin(R.TREASURER), "tresorer@example.com")  # sense WP5
    client.post(URL, _data())
    email = OutgoingEmail.objects.get()
    assert (email.to_address, email.template) == ("secretaria@example.com", contact.NOTICE_TEMPLATE)
    assert "Quotes" in email.subject
    for private in ("Nom Inventat", "inventat@example.com", "Quan es paga"):
        assert private not in email.subject + email.body_text


def test_a_robot_message_notifies_nobody(client, enabled, privacy, make_admin):  # noqa: F811
    _with_email(make_admin(R.SECRETARY), "secretaria@example.com")
    client.post(URL, _data(web="http://spam.example"))
    assert not OutgoingEmail.objects.exists()


def test_replying_queues_the_answer_to_the_visitor_and_is_recorded(make_admin):  # noqa: F811
    from django.core.exceptions import ValidationError

    secretary, message = make_admin(R.SECRETARY), _message()
    with pytest.raises(ValidationError):
        contact.reply(message, actor=secretary, answer=" ")
    contact.reply(message, actor=secretary, answer="Es paga al gener (inventat).")
    message.refresh_from_db()
    assert (message.status, message.answered_by, message.finished_at is not None) == (
        ContactMessage.Status.ANSWERED, secretary, True,
    )  # fmt: skip
    email = OutgoingEmail.objects.get()
    assert (email.to_address, email.template) == ("inventat@example.com", contact.REPLY_TEMPLATE)
    assert "Es paga al gener" in email.body_text
    entry = AuditEntry.objects.get(action=contact.ACTION_ANSWERED)
    assert (entry.old_value, entry.new_value) == ("new", "answered")
    with pytest.raises(ValidationError):
        contact.reply(message, actor=secretary, answer="Un altre cop")


def test_replying_out_of_scope_is_not_found(make_admin):  # noqa: F811
    for account in (make_admin(R.ADMINISTRATOR), make_admin(R.TREASURER)):
        with pytest.raises(ContactMessage.DoesNotExist):
            contact.reply(_message(), actor=account, answer="Fora d'abast")
    assert not OutgoingEmail.objects.exists()
