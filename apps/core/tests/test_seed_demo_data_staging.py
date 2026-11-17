"""`seed_demo_data` a l'entorn de proves (decisió 090; `config/settings/staging.py`): hi corre
sense DEBUG, contra la base «db» del servidor, i els comptes de prova fan servir el secret TOTP
del servidor, mai el de prova, que continua refusat sense DEBUG (RN-M01-84)."""

from io import StringIO

import pyotp
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import override_settings

from apps.accounts import totp
from apps.accounts.models import Account
from apps.accounts.totp import DEMO_TOTP_SECRET
from apps.core.management.commands.seed_demo_data import ROLE_ACCOUNTS
from apps.core.models import Person

pytestmark = pytest.mark.django_db
# Generat a cada execució: cap secret escrit a la prova.
SERVER_SECRET = pyotp.random_base32(32)


def staging(**extra):
    values = {
        "SETTINGS_MODULE": "config.settings.staging",
        "DEBUG": False,
        "DEMO_DATA_ALLOWED": True,
        "DEMO_DATA_DB_HOSTS": ["db"],
        "STAGING_TOTP_SECRET": SERVER_SECRET,
    }
    return override_settings(**{**values, **extra})


def run(tmp_path):
    out = StringIO()
    call_command("seed_demo_data", "--cluber-file", str(tmp_path / "c.csv"), stdout=out)
    return out.getvalue()


def test_runs_in_staging_with_the_server_secret(tmp_path):
    with staging():
        output = run(tmp_path)
        for login, _name, _role in ROLE_ACCOUNTS:
            device = Account.objects.get(login=login).totp_device
            assert totp.verify_code(device, pyotp.TOTP(SERVER_SECRET).now())
    # Cap secret als registres del servidor.
    assert SERVER_SECRET not in output and DEMO_TOTP_SECRET not in output


def test_the_test_secret_is_still_refused_in_staging(tmp_path):
    with staging():
        run(tmp_path)
        device = Account.objects.get(login=ROLE_ACCOUNTS[0][0]).totp_device
        assert not totp.verify_code(device, pyotp.TOTP(DEMO_TOTP_SECRET).now())


def test_accepts_the_server_database_host(monkeypatch, tmp_path):
    monkeypatch.setitem(connection.settings_dict, "HOST", "db")
    with staging():
        run(tmp_path)
    assert Person.objects.exists()


@pytest.mark.parametrize("secret", ["", DEMO_TOTP_SECRET, "CURT", "no-es-base32-" * 4])
def test_refuses_staging_without_its_own_valid_secret(secret, tmp_path):
    with staging(STAGING_TOTP_SECRET=secret), pytest.raises(CommandError):
        run(tmp_path)
    assert not Account.objects.exists()


@pytest.mark.parametrize(
    "extra",
    [
        # La configuració de producció, encara que algú hi encengués l'interruptor.
        {"SETTINGS_MODULE": "config.settings.prod"},
        # La de proves sense l'interruptor.
        {"DEMO_DATA_ALLOWED": False},
    ],
)
def test_refuses_without_staging_settings_and_switch(extra, tmp_path):
    with staging(**extra), pytest.raises(CommandError):
        run(tmp_path)
    assert not Person.objects.exists()


@pytest.mark.parametrize("host", ["db.example.org", "10.0.0.5"])
def test_refuses_other_database_hosts_in_staging(monkeypatch, host, tmp_path):
    monkeypatch.setitem(connection.settings_dict, "HOST", host)
    with staging(), pytest.raises(CommandError):
        run(tmp_path)
    assert not Person.objects.exists()


def test_development_without_debug_cannot_use_the_staging_hosts(monkeypatch, tmp_path):
    """Fora de l'entorn de proves, «db» no és local."""
    monkeypatch.setitem(connection.settings_dict, "HOST", "db")
    dev = override_settings(SETTINGS_MODULE="config.settings.dev", DEBUG=True)
    with dev, pytest.raises(CommandError):
        run(tmp_path)
