"""Concurrència amb PostgreSQL real: peticions alhora, cadascuna amb la seva connexió.

Fan servir `committed_db` (vegeu `conftest.py`): les dades es confirmen de debò perquè els
altres fils les vegin, i s'esborren en acabar. Només dades inventades.
"""

from apps.accounts import email_links, tokens
from apps.accounts.models import Account
from apps.core import audit
from apps.core.models import AuditEntry, Person
from conftest import PASSWORD, run_together


def make_pending(email="anna@example.org"):
    person = Person.objects.create(first_name="Anna", last_name="Puig", origin=Person.Origin.WEB)
    return Account.objects.create_personal(person, email, PASSWORD)


def test_two_simultaneous_confirmations_verify_once(committed_db):
    account = make_pending()
    token = tokens.make_token(account, tokens.VERIFY_EMAIL)

    results = run_together([lambda: email_links.confirm_email(token)] * 2)

    assert sum(result is not None for result in results) == 1
    account.refresh_from_db()
    assert account.status == Account.Status.ACTIVE
    assert AuditEntry.objects.filter(action=audit.Action.EMAIL_VERIFIED).count() == 1
