"""Sessions separades per entrada i caducitat (spec 00, RN-14, CA-07.7; V-01).

Només dades inventades.
"""

import time

import pytest
from django.urls import reverse

from apps.accounts.sessions import (
    ADMIN_IDLE_SECONDS,
    AUTH_AT_SESSION_KEY,
    PERSONAL_IDLE_SECONDS,
)

pytestmark = pytest.mark.django_db


def test_admin_session_cannot_use_the_personal_area(admin_account, login_as):
    # RN-14: el compte d'administrador no entra a l'àrea de socis.
    client = login_as(admin_account, "admin")
    response = client.get(reverse("core:home"))
    assert response["Location"].startswith(reverse("accounts:login"))


def test_personal_session_cannot_use_the_admin_area(personal_account, login_as):
    client = login_as(personal_account, "personal")
    response = client.get(reverse("administration:home"))
    assert response["Location"].startswith(reverse("administration:login"))


def test_admin_account_with_a_personal_marker_is_rejected(admin_account, login_as):
    # Encara que la sessió digui «personal», el compte ha de ser del tipus de l'entrada.
    client = login_as(admin_account, "personal")
    assert client.get(reverse("core:home")).status_code == 302


def test_session_without_area_is_rejected(client, personal_account):
    client.force_login(personal_account)
    assert client.get(reverse("core:home")).status_code == 302


def test_admin_idle_timeout_is_thirty_minutes(admin_account, login_as):
    client = login_as(admin_account, "admin")
    client.get(reverse("administration:home"))
    assert client.session.get_expiry_age() == ADMIN_IDLE_SECONDS


def test_personal_idle_timeout_is_fourteen_days(personal_account, login_as):
    client = login_as(personal_account, "personal")
    client.get(reverse("core:home"))
    assert client.session.get_expiry_age() == PERSONAL_IDLE_SECONDS


def test_admin_session_ends_after_eight_hours(admin_account, login_as):
    # V-01: com a màxim 8 hores; després cal tornar a entrar amb TOTP (CA-07.7).
    client = login_as(admin_account, "admin")
    session = client.session
    session[AUTH_AT_SESSION_KEY] = time.time() - 8 * 60 * 60 - 1
    session.save()
    response = client.get(reverse("administration:home"))
    # T-M01-38: «La sessió ha caducat» (401), amb el botó cap a l'entrada d'administració.
    assert response.status_code == 401
    assert f'href="{reverse("administration:login")}?next=' in response.content.decode()
    assert "_auth_user_id" not in client.session


def test_disabled_account_loses_its_session(personal_account, login_as):
    client = login_as(personal_account, "personal")
    personal_account.status = personal_account.Status.DISABLED
    personal_account.save()
    assert client.get(reverse("core:home")).status_code == 302


def test_login_changes_the_session_key(client, personal_account):
    # Fixació de sessió: la clau d'abans d'entrar no serveix després.
    client.get(reverse("accounts:login"))
    session = client.session
    session["marca"] = "abans"
    session.save()
    before = session.session_key
    client.post(
        reverse("accounts:login"),
        {"login": "anna@example.org", "password": "contrasenya-de-proves-1954"},
    )
    assert client.session.session_key != before
