"""Fixtures comunes de les proves. Només dades inventades."""

import time

import pytest

from apps.accounts.models import Account
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core.models import Person

PASSWORD = "contrasenya-de-proves-1954"  # noqa: S105 (dada inventada de proves)


@pytest.fixture
def make_person(db):
    def make(first_name="Anna", last_name="Puig", **fields):
        return Person.objects.create(
            first_name=first_name, last_name=last_name, origin=Person.Origin.WEB, **fields
        )

    return make


@pytest.fixture
def personal_account(make_person):
    account = Account.objects.create_personal(make_person(), "anna@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    return account


@pytest.fixture
def admin_account(make_person):
    return Account.objects.create_admin(
        make_person("Joan", "Vila"), "joan.vila", PASSWORD, notification_email="joan@example.org"
    )


@pytest.fixture
def login_as(client):
    """Obre una sessió com si s'hagués entrat per l'entrada indicada (sense passar pel
    formulari): per a les proves que no són de l'entrada mateixa."""

    def login(account, area):
        client.force_login(account)
        session = client.session
        session[AREA_SESSION_KEY] = area
        session[AUTH_AT_SESSION_KEY] = time.time()
        session.save()
        return client

    return login
