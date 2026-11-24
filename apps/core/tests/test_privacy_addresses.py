"""RGPD: els mòduls que ho demanen reben les adreces conegudes de la persona, preses abans de
buidar-la (T-M07-15 les farà servir per al butlletí del 07). Només dades inventades."""

import pytest

from apps.accounts.models import Account
from apps.core import privacy
from apps.core.models import Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db


def test_a_module_with_addresses_gets_the_contact_and_account_emails(make_admin, monkeypatch):  # noqa: F811
    person = Person.objects.create(
        first_name="Pau", origin=Person.Origin.WEB, contact_email="pau.contacte@example.org"
    )
    Account.objects.create_personal(person, "pau.compte@example.org")
    calls = {}

    def with_addresses(person, *, by, request=None, known_addresses, contact_email):
        calls["with"] = (person.contact_email, known_addresses, contact_email)

    def without(person, *, by, request=None):  # un mòdul d'abans: sense el paràmetre
        calls["without"] = True

    nothing = lambda person: {}  # noqa: E731
    monkeypatch.setitem(privacy._MODULES, "prova_amb", privacy.Module(
        export=nothing, anonymise=with_addresses, audit_targets=nothing, addresses=True
    ))  # fmt: skip
    monkeypatch.setitem(privacy._MODULES, "prova_sense", privacy.Module(
        export=nothing, anonymise=without, audit_targets=nothing
    ))  # fmt: skip

    privacy.anonymise_person(person, by=make_admin("administrator"))

    known = {"pau.contacte@example.org", "pau.compte@example.org"}
    assert calls["with"] == ("", known, "pau.contacte@example.org")
    assert calls["without"] is True
