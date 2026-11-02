"""Ordre de dades inventades: es nega fora de desenvolupament i proves, i no deixa cap secret."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import override_settings

from apps.accounts.models import Account, TotpDevice
from apps.core import audit
from apps.core.management.commands.seed_demo_data import ADMIN_LOGIN, demo_people
from apps.core.models import AuditEntry, Charge, Consent, Person, Role
from apps.core.roles import operational_admins

pytestmark = pytest.mark.django_db
DEV = override_settings(SETTINGS_MODULE="config.settings.dev", DEBUG=True)


def run(*args):
    out = StringIO()
    call_command("seed_demo_data", *args, stdout=out)
    return out.getvalue()


@pytest.mark.parametrize(
    ("module", "debug"),
    [
        ("config.settings.prod", True),
        ("config.settings.prod", False),
        ("config.settings.dev", False),
        (None, True),
    ],
)
def test_refuses_outside_development(module, debug):
    with override_settings(SETTINGS_MODULE=module, DEBUG=debug), pytest.raises(CommandError):
        run()
    assert not Person.objects.exists()


@pytest.mark.parametrize("host", ["db.example.org", "10.0.0.5"])
def test_refuses_a_database_that_is_not_local(monkeypatch, host):
    monkeypatch.setitem(connection.settings_dict, "HOST", host)
    with DEV, pytest.raises(CommandError):
        run()
    assert not Person.objects.exists()


def test_refuses_a_database_with_data(make_person):
    make_person()
    with DEV, pytest.raises(CommandError):
        run()
    assert Person.objects.count() == 1


def test_same_seed_same_people():
    assert demo_people(1954) == demo_people(1954)
    assert demo_people(1954) != demo_people(7)


@DEV
def test_creates_the_people_of_the_seed():
    run("--seed", "7")
    created = Person.objects.exclude(accounts__login=ADMIN_LOGIN).order_by("id_document_number")
    expected = sorted(demo_people(7), key=lambda p: p["id_document_number"])
    assert [(p.first_name, p.last_name, p.contact_email) for p in created] == [
        (p["first_name"], p["last_name"], p["contact_email"]) for p in expected
    ]


@DEV
def test_only_invented_data():
    run()
    for person in Person.objects.exclude(contact_email=""):
        assert person.contact_email.endswith("@example.org")
        assert person.id_document_number.startswith("PROVA")
    assert all(p.phone == "" and p.address == "" for p in Person.objects.all())


@DEV
def test_admin_has_the_role_but_is_not_operational():
    output = run()
    admin = Account.objects.get(login=ADMIN_LOGIN)
    assert not admin.has_usable_password()
    assert not TotpDevice.objects.filter(account=admin).exists()
    assert admin.role_assignments.filter(role__code=Role.Code.ADMINISTRATOR).exists()
    assert admin not in operational_admins()
    entry = AuditEntry.objects.get(action=audit.Action.ROLE_ASSIGNED, target_id=str(admin.pk))
    assert (entry.actor_kind, entry.actor_origin) == ("system", "seed_demo_data")
    # Cap secret a la sortida: ni QR, ni URI del TOTP, ni contrasenya.
    assert "otpauth" not in output and "<svg" not in output
    assert "changepassword" in output


@DEV
def test_covers_the_states_shown_in_captures():
    run()
    assert set(Charge.objects.values_list("status", flat=True)) == {
        Charge.Status.PENDING,
        Charge.Status.PAID,
        Charge.Status.CANCELLED,
    }
    assert set(Consent.objects.values_list("action", flat=True)) == {
        Consent.Action.GRANTED,
        Consent.Action.WITHDRAWN,
    }
    assert set(Consent.objects.values_list("channel", flat=True)) == {
        Consent.Channel.WEB,
        Consent.Channel.IN_PERSON,
    }
