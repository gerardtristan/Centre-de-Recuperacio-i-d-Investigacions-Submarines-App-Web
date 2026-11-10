"""Sol·licitud d'esborrat des del perfil (peça mínima de la T-M01-22, 074 punt 20; P-M01-F pas 3;
RN-M01-57, CA-M01-46). Només dades inventades.
"""

import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils.html import escape

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL, WRONG_CODE, WRONG_PASSWORD
from apps.accounts.tests.test_personal_totp import code_for, with_totp
from apps.core import audit
from apps.core.models import AuditEntry, ErasureRequest
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

ERASE = "members:erase"
NOT_IT = "no-es-aquesta"  # una contrasenya que no és la del compte


@pytest.fixture
def session(login_as, personal_account):
    return login_as(personal_account, AREA_PERSONAL)


def send(client, **data):
    return client.post(reverse(ERASE), {"confirm": "on", **data})


def failed_count(account):
    account.refresh_from_db()
    return account.failed_login_count


class TestCaM0146:
    def test_ca_m01_46_without_password_creates_nothing_and_counts(self, session, personal_account):
        """CA-M01-46: sense contrasenya, cap sol·licitud, «Contrasenya incorrecta» al camp i
        l'intent compta per a V-01 i queda al registre."""
        response = send(session)
        assert response.status_code == 200
        assert response.context["form"].errors["password"] == [str(WRONG_PASSWORD)]
        assert not ErasureRequest.objects.exists()
        assert failed_count(personal_account) == 1
        assert AuditEntry.objects.filter(
            action=audit.Action.LOGIN_FAILED, target_id=str(personal_account.pk)
        ).exists()

    def test_ca_m01_46_wrong_password_creates_nothing_and_counts(self, session, personal_account):
        response = send(session, password=NOT_IT)
        assert response.context["form"].errors["password"] == [str(WRONG_PASSWORD)]
        assert escape(str(WRONG_PASSWORD)) in response.content.decode()
        assert not ErasureRequest.objects.exists()
        assert failed_count(personal_account) == 1

    def test_ca_m01_46_right_password_creates_the_request(self, session, personal_account):
        response = send(session, password=PASSWORD)
        assert response.status_code == 302
        assert response["Location"] == reverse(ERASE)
        created = ErasureRequest.objects.get()
        assert created.person == personal_account.person
        assert created.requested_by == personal_account
        assert created.status == ErasureRequest.Status.PENDING
        assert created.channel == ErasureRequest.Channel.WEB
        entry = AuditEntry.objects.get(action=audit.Action.ERASURE_REQUESTED)
        assert entry.actor_account == personal_account
        assert entry.target_id == str(created.pk)

    def test_ca_m01_46_with_totp_needs_the_code_too(self, session, personal_account):
        device = with_totp(personal_account)
        page = session.get(reverse(ERASE))
        assert "code" in page.context["form"].fields
        response = send(session, password=PASSWORD)
        assert response.context["form"].errors["code"] == [str(WRONG_CODE)]
        assert not ErasureRequest.objects.exists()
        assert failed_count(personal_account) == 1
        assert send(session, password=PASSWORD, code=code_for(device)).status_code == 302
        assert ErasureRequest.objects.count() == 1

    def test_without_totp_the_code_field_is_not_shown(self, session):
        assert "code" not in session.get(reverse(ERASE)).context["form"].fields

    def test_confirmation_box_is_required_and_no_attempt_is_counted(
        self, session, personal_account
    ):
        response = session.post(reverse(ERASE), {"password": PASSWORD})
        assert "confirm" in response.context["form"].errors
        assert not ErasureRequest.objects.exists()
        assert failed_count(personal_account) == 0


class TestOnePending:
    def test_second_request_shows_the_pending_one(self, session, personal_account):
        send(session, password=PASSWORD)
        page = session.get(reverse(ERASE))
        assert page.context["pending"] is not None
        assert page.context["form"] is None
        send(session, password=PASSWORD)
        assert ErasureRequest.objects.count() == 1
        assert AuditEntry.objects.filter(action=audit.Action.ERASURE_REQUESTED).count() == 1

    def test_database_allows_only_one_pending_per_person(self, personal_account):
        person = personal_account.person
        ErasureRequest.objects.create(person=person, requested_by=personal_account, channel="web")
        with pytest.raises(IntegrityError), transaction.atomic():
            ErasureRequest.objects.create(
                person=person, requested_by=personal_account, channel="web"
            )


class TestAccess:
    def test_without_session_goes_to_login(self, client):
        response = client.get(reverse(ERASE))
        assert response.status_code == 302
        assert response["Location"].startswith(reverse("accounts:login"))
        assert client.post(reverse(ERASE), {"confirm": "on"}).status_code == 302
        assert not ErasureRequest.objects.exists()

    def test_admin_session_cannot_use_it(self, login_as, admin_account):
        client = login_as(admin_account, AREA_ADMIN)
        response = client.post(reverse(ERASE), {"confirm": "on", "password": PASSWORD})
        assert response.status_code != 200
        assert not ErasureRequest.objects.exists()

    def test_profile_links_to_it(self, session):
        assert reverse(ERASE) in session.get(reverse("members:profile")).content.decode()
