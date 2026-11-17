"""Seguiment d'errors (checklist E4, R11): sense dades personals i només cap a hosts permesos.

Cap prova no fa servir la xarxa: els hosts són `.invalid` i cap esdeveniment no s'envia."""

import json

import pytest
from django.core.exceptions import ImproperlyConfigured

from apps.core import error_tracking
from conftest import run_with_production_settings

ALLOWED = "errors.example.invalid"
DSN = f"https://clau-publica@{ALLOWED}/1"  # gitleaks:allow (DSN inventat; host .invalid)
GUEST_SEGMENT = "Tq3ZxK8wLm2PvR7nYb4c"  # testimoni inventat d'un enllaç de convidat
# Diu si l'SDK s'ha activat i amb quines opcions. La llista es fixa abans de `setup`, perquè la
# configuració es carrega amb la que vol la prova (al codi és buida fins a la P-294).
CODE = (
    "import json, django, sentry_sdk; from apps.core import error_tracking as e; "
    "e.ERROR_TRACKING_ALLOWED_HOSTS = {allowed!r}; django.setup(); c = sentry_sdk.get_client(); "
    "keys = ['send_default_pii', 'include_local_variables', 'max_request_body_size', "
    "'traces_sample_rate', 'environment']; "
    "print(json.dumps({{'active': c.is_active(), "
    "'options': {{k: c.options[k] for k in keys}} if c.is_active() else {{}}}}))"
)


def _production(extra_env, allowed=()):
    return run_with_production_settings(CODE.format(allowed=tuple(allowed)), extra_env)


def test_without_dsn_nothing_is_initialised():
    done = _production({})
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout.splitlines()[-1]) == {"active": False, "options": {}}


def test_production_refuses_a_dsn_whose_host_is_not_allowed():
    done = _production({"ERROR_TRACKING_DSN": DSN})
    assert done.returncode != 0
    assert "ERROR_TRACKING_ALLOWED_HOSTS" in done.stderr


def test_production_initialises_with_an_allowed_host_and_without_personal_data():
    done = _production({"ERROR_TRACKING_DSN": DSN}, allowed=("altre.invalid", ALLOWED))
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout.splitlines()[-1]) == {
        "active": True,
        "options": {
            "send_default_pii": False,
            "include_local_variables": False,
            "max_request_body_size": "never",
            "traces_sample_rate": 0,
            "environment": "production",
        },
    }


def test_the_allowlist_is_code_not_environment():
    """Qui posa el DSN no pot posar també el host permès: la llista és al codi."""
    done = _production({"ERROR_TRACKING_DSN": DSN, "ERROR_TRACKING_ALLOWED_HOSTS": ALLOWED})
    assert done.returncode != 0


def test_p294_only_the_club_glitchtip_is_allowed():
    """P-294: GlitchTip autoallotjat al VPS del club; cap altre servei, tampoc un de Sentry."""
    assert error_tracking.ERROR_TRACKING_ALLOWED_HOSTS == ("errors.cris1954.cat",)
    allowed = error_tracking.ERROR_TRACKING_ALLOWED_HOSTS
    assert error_tracking.dsn_host_allowed("https://clau@errors.cris1954.cat/1", allowed)
    for dsn in (
        "http://clau@errors.cris1954.cat/1",
        "https://clau@o1.ingest.de.sentry.io/1",
        "https://clau@app.glitchtip.com/1",
        "https://clau@errors.cris1954.cat.altre.invalid/1",
    ):
        assert not error_tracking.dsn_host_allowed(dsn, allowed), dsn


@pytest.mark.parametrize(
    ("dsn", "allowed"),
    [
        (DSN, ()),
        (DSN, ("sentry.invalid",)),
        (f"https://clau@{ALLOWED}.altre.invalid/1", (ALLOWED,)),
        ("no-es-un-dsn", (ALLOWED,)),
        (f"http://clau@{ALLOWED}/1", (ALLOWED,)),  # sense TLS
    ],
)
def test_init_rejects_hosts_outside_the_allowlist(monkeypatch, dsn, allowed):
    monkeypatch.setattr(error_tracking, "ERROR_TRACKING_ALLOWED_HOSTS", allowed)
    with pytest.raises(ImproperlyConfigured):
        error_tracking.init(dsn, "production")


def test_host_comparison_ignores_case_and_spaces():
    assert error_tracking.dsn_host_allowed(DSN.upper(), [f" {ALLOWED} "])


def _event():
    # Valors inventats.
    return {
        "event_id": "0" * 32,
        "message": "Error amb soci@example.invalid",
        "request": {
            "url": "https://cris1954.cat/convidat/testimoni-secret/",
            "method": "POST",
            "query_string": "correu=soci@example.invalid",
            "data": {"iban": "ES0000000000000000000000"},
            "cookies": {"sessionid": "galeta"},
            "headers": {"Cookie": "sessionid=galeta", "User-Agent": "Navegador/1.0"},
            "env": {"REMOTE_ADDR": "192.0.2.10"},
        },
        "user": {"id": 7, "email": "soci@example.invalid", "ip_address": "192.0.2.10"},
        "extra": {"persona": "Nom Inventat"},
        "logentry": {"message": "login_failed ip=%s", "params": ["192.0.2.10"]},
        "exception": {
            "values": [
                {
                    "type": "ValueError",
                    "value": (
                        "IBAN ES00 0000 0000 0000 0000 0000, targeta 4000 0000 0000 0002, "
                        "DNI 00000000T, NIE X0000000T, telèfon +34 600 000 000, "
                        "correu soci@example.invalid, ip 192.0.2.10, ip6 2001:db8::1:2"
                    ),
                    "stacktrace": {"frames": [{"function": "f", "vars": {"iban": "ES00"}}]},
                }
            ]
        },
    }


def test_before_send_drops_request_body_cookies_user_and_extra():
    event = error_tracking.before_send(_event(), None)
    assert event["request"] == {"method": "POST", "headers": {"User-Agent": "Navegador/1.0"}}
    assert "user" not in event and "extra" not in event
    assert event["event_id"] == "0" * 32
    assert "vars" not in event["exception"]["values"][0]["stacktrace"]["frames"][0]
    assert event["logentry"] == {"message": "login_failed ip=%s"}


def test_before_send_leaves_events_without_a_request_alone():
    assert "request" not in error_tracking.before_send({"message": "Cua"}, None)


def test_before_send_masks_personal_data_in_messages():
    event = error_tracking.before_send(_event(), None)
    value = event["exception"]["values"][0]["value"]
    for secret in ("ES00", "4000", "00000000T", "X0000000T", "600", "@", "192.0", "2001:db8"):
        assert secret not in value, secret
    assert value.startswith("IBAN [tapat], targeta [tapat]")
    assert event["message"] == "Error amb [tapat]"
    assert "soci" not in json.dumps(event) and "192.0.2.10" not in json.dumps(event)


def test_mask_keeps_ordinary_text():
    assert error_tracking.mask("Intent 42 no trobat a les 12:30:45") == (
        "Intent 42 no trobat a les 12:30:45"
    )
    assert error_tracking.mask(None) is None


def test_breadcrumbs_drop_sql_and_their_data():
    sql = {"category": "query", "message": "SELECT"}
    assert error_tracking.before_breadcrumb(sql, None) is None
    crumb = error_tracking.before_breadcrumb(
        {"category": "cris.security", "message": "ip=192.0.2.10", "data": {"url": "/?a=b"}}, None
    )
    assert crumb == {"category": "cris.security", "message": "ip=[tapat]"}


def test_init_passes_the_filters_to_the_sdk(monkeypatch):
    """El mateix camí en el procés de les proves (la cobertura no mira els subprocessos)."""
    import sentry_sdk

    calls = []
    monkeypatch.setattr(sentry_sdk, "init", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(error_tracking, "ERROR_TRACKING_ALLOWED_HOSTS", (ALLOWED,))
    error_tracking.init(DSN, "proves")
    (options,) = calls
    assert options["before_send"] is error_tracking.before_send
    assert options["before_breadcrumb"] is error_tracking.before_breadcrumb
    assert options["send_default_pii"] is False and options["traces_sample_rate"] == 0


@pytest.mark.parametrize(
    "text",
    [
        "+34600000000",
        "+34 600000000",
        "+34-600-000-000",
        "tel:+34700000000",
        "00000000-T",
        "00000000 T",
        "X0000000-T",
        "fe80::1",
        "ip=::1",
        "iban_ES0000000000000000000000",
        "iban_GB00XXXX00000000000000",
        "id:GB00XXXX00000000000000",
    ],
)
def test_mask_covers_glued_and_separated_forms(text):
    """Revisió de la #183: formes que el primer patró deixava passar senceres o a mitges."""
    masked = error_tracking.mask(text)
    assert not any(part in masked for part in ("0000", "::1", "fe80", "ES00", "GB00")), masked


def test_transaction_hides_tokens_but_keeps_route_patterns():
    raw = error_tracking.before_send({"transaction": f"/convidat/{GUEST_SEGMENT}/pagar/"}, None)
    assert GUEST_SEGMENT not in raw["transaction"] and raw["transaction"].startswith("/convidat/")
    route = "/gestio/socis/<int:pk>/quota/<slug:codi>/"
    assert error_tracking.before_send({"transaction": route}, None)["transaction"] == route
    email = error_tracking.before_send({"transaction": "/u/soci@example.invalid/"}, None)
    assert "soci@" not in email["transaction"]
