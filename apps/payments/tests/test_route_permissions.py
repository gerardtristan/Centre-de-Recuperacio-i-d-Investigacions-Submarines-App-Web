"""Permisos de la 04, el 05a i el 05b a cada ruta i a cada servei (T-M04-21, T-M05a-25 i
T-M05b-25; 059, CA-RP-13). Quin permís (i si és de consulta o d'escriptura) demana cada ruta
d'administració, i que un rol sense aquest permís rep «no trobat»; les rutes del compte personal
són accions pròpies (sense permís de rol) i les de convidat i del proveïdor, públiques declarades.
Cada servei públic dels mòduls de diners comprova el seu permís o diu per què no en demana cap.
Una ruta o un servei nou sense declarar fa fallar la prova. Només dades inventades.

Permisos que no tenen codi propi (P-190 i P-243): T8 (excloure una línia) fa servir T4; T10 (la
llista «a revisar»), T1; T11 encara no té pantalla. A7, A8 i B8 són configuració de l'entorn;
A9 no el té ningú. T2, T3 i B7 són al catàleg però encara no tenen cap pantalla ni servei."""

import inspect
import sys
from importlib import import_module
from types import SimpleNamespace

import pytest
from django.http import Http404
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL
from apps.core import permissions
from apps.core.models import Role
from apps.core.permission_catalog import CATALOG
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_access import PUBLIC_ROUTES, _routes
from apps.payments import mandates, refunds, remittances, returns, reviews, sepa_xml
from apps.treasury import reconciliation, services, settlements
from apps.treasury.tests.test_views import client_for

R = Role.Code
MANAGEMENT_ROLES = [code for code in R.values if code not in ("member", "visitor", "guest")]

T1, T4, T5 = "treasury.view", "treasury.reconcile", "treasury.reverse"
T6, T7, T9 = "treasury.transfer", "treasury.cash_count", "treasury.export"
A4, A5, A6 = "payments.mandates.view", "payments.campaign.send", "payments.mandates.revoke"
B3, B4, B5, B6 = "payments.remittances", "payments.returns", "payments.refund", "payments.view"
M14 = "core.charges.record_manual"  # P-12: pagament a mà


def r(code):  # consulta
    return (code, False)


def w(code):  # escriptura: un abast «Cons.» no hi val
    return (code, True)


# Ruta d'administració → mètode → permisos que comprova la vista (tots calen).
ADMIN_ROUTES = {
    "administration:treasury_accounts": {"GET": {r(T1)}},
    "administration:treasury_movements": {"GET": {r(T1)}},
    "administration:treasury_export": {"POST": {r(T9)}},
    "administration:treasury_reconciliation": {"GET": {r(T1)}},
    "administration:treasury_confirm_line": {"POST": {w(T4)}},
    "administration:treasury_match_line": {"GET": {w(T4)}, "POST": {w(T4)}},
    "administration:treasury_undo_reconciliation": {"POST": {w(T4)}},
    "administration:treasury_review": {"GET": {r(T1)}},  # T10, amb T1 (P-190)
    "administration:treasury_exclude_line": {"POST": {w(T4)}},  # T8, amb T4 (P-190)
    "administration:treasury_transfer": {"GET": {w(T6)}, "POST": {w(T6)}},
    "administration:treasury_cash_count": {"GET": {w(T7)}, "POST": {w(T7)}},
    "administration:treasury_reverse": {"GET": {w(T5)}, "POST": {w(T5)}},
    "administration:treasury_settlements": {"GET": {r(T1)}},
    # P10, a més, si el càrrec és una quota (test_manual_payment).
    "administration:treasury_manual_payment": {"GET": {w(M14)}, "POST": {w(M14)}},
    "administration:treasury_settlement_confirm": {"GET": {w(T4)}, "POST": {w(T4)}},
    "administration:treasury_confirm_settlement_line": {"GET": {w(T4)}, "POST": {w(T4)}},
    "administration:payments_list": {"GET": {r(B6)}},
    "administration:payments_review_close": {"GET": {w(B6)}, "POST": {w(B6)}},  # T-M05b-16b
    "administration:payments_mandates": {"GET": {r(A4)}},
    "administration:payments_mandate_revoke": {"GET": {w(A6)}, "POST": {w(A6)}},
    "administration:payments_campaign": {"GET": {r(A4)}, "POST": {r(A4), w(A5)}},
    "administration:payments_remittances": {"GET": {r(B3)}, "POST": {r(B3), w(B3)}},
    "administration:payments_remittance": {"GET": {r(B3)}},
    "administration:payments_remittance_notices": {"POST": {w(B3)}},
    "administration:payments_remittance_file": {"POST": {w(B3)}},
    "administration:payments_remittance_sent": {"POST": {w(B3)}},
    "administration:payments_remittance_settle": {"POST": {w(B3), w(T4)}},
    "administration:payments_returns": {"GET": {r(B4)}, "POST": {r(B4), w(B4)}},
    "administration:payments_return_decision": {"POST": {w(B4)}},
    "administration:payments_returns_file": {"POST": {w(B4)}},
    "administration:payments_returns_file_confirm": {"POST": {w(B4)}},
}

# Compte personal: accions pròpies (M05a-4 i M05b-4), sense cap permís de rol; l'objecte el
# comprova cada vista (proves a test_payment_screen, test_mandate_signing i test_fee_method).
OWN_ROUTES = {
    "payments:mandate": "A2",
    "payments:mandate_revoke": "A2",
    "payments:fee_method": "A1",
    "payments:saved_card": "A3",
    "payments:charge": "B1",
    "payments:pay_card": "B1",
    "payments:pay_bizum": "B1",
    "payments:pay_transfer": "B1",
    "payments:attempt_status": "B2",
    "payments:receipt": "B2",
}

PUBLIC_MONEY_ROUTES = {
    "payments:provider_notification",
    "payments:fake_pay",
    "payments:guest_charge",
    "payments:guest_pay_card",
    "payments:guest_pay_bizum",
    "payments:guest_pay_transfer",
    "payments:guest_status",
    "payments:guest_receipt",
}

MONEY_ROUTES = {
    name: kwargs
    for name, view, kwargs in _routes()
    if view.__module__.startswith(("apps.treasury.", "apps.payments."))
}


def test_every_money_route_is_declared():
    assert set(MONEY_ROUTES) == set(ADMIN_ROUTES) | set(OWN_ROUTES) | PUBLIC_MONEY_ROUTES
    assert PUBLIC_MONEY_ROUTES <= PUBLIC_ROUTES
    assert not (set(ADMIN_ROUTES) | set(OWN_ROUTES)) & PUBLIC_ROUTES


@pytest.fixture
def checked(monkeypatch):
    """Els permisos que comprova `require_perm` (la vista), no els de la interfície."""
    calls = set()
    real = permissions.has_perm

    def recording(account, code, obj=None, *, write=False, permissions=None):
        if sys._getframe(1).f_code.co_name == "require_perm":
            calls.add((code, write))
        return real(account, code, obj, write=write, permissions=permissions)

    monkeypatch.setattr(permissions, "has_perm", recording)
    return calls


def _call(client, name, method):
    url = reverse(name, kwargs=MONEY_ROUTES[name])
    return client.get(url) if method == "GET" else client.post(url)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("name", "method"), [(n, m) for n, methods in ADMIN_ROUTES.items() for m in methods]
)
def test_each_admin_route_checks_its_permissions(make_admin, checked, name, method):  # noqa: F811
    # Amb tots els permisos, la vista arriba a buscar l'objecte: s'hi veuen totes les comprovacions.
    _call(client_for(make_admin(R.TREASURER, R.ADMINISTRATOR)), name, method)
    assert checked == ADMIN_ROUTES[name][method]


@pytest.mark.django_db
@pytest.mark.parametrize("name", sorted(OWN_ROUTES))
def test_own_routes_need_no_role_permission(personal_account, checked, name):
    _call(client_for(personal_account, AREA_PERSONAL), name, "GET")
    assert checked == set()


CELLS = [(name, role) for name in ADMIN_ROUTES for role in MANAGEMENT_ROLES]


@pytest.mark.django_db
@pytest.mark.parametrize(("name", "role"), CELLS, ids=[f"{n}-{role}" for n, role in CELLS])
def test_admin_route_cell(make_admin, name, role):  # noqa: F811
    # CA-RP-13: sense algun dels permisos, «no trobat»; amb tots, la pantalla s'obre.
    account = make_admin(role)
    client = client_for(account)
    for method, needed in ADMIN_ROUTES[name].items():
        allowed = all(permissions.has_perm(account, code, write=wr) for code, wr in needed)
        status = _call(client, name, method).status_code
        if not allowed:
            assert status == 404, method
        elif method == "GET" and not MONEY_ROUTES[name]:
            assert status != 404


# --- Serveis -----------------------------------------------------------------------------
# Servei → (permís d'escriptura, crida amb arguments buits): la comprovació va abans de tocar res.
MEMBER = SimpleNamespace(pk=0, person_id=0)
SERVICE_CHECKS = {
    services.reverse: (T5, lambda by: services.reverse(None, reason="x", by=by)),
    services.record_transfer: (
        T6,
        lambda by: services.record_transfer(None, None, 1, value_date=None, concept="x", by=by),
    ),
    services.record_cash_count: (
        T7,
        lambda by: services.record_cash_count(None, 0, counted_on=None, by=by),
    ),
    services.record_manual_payment: (
        M14,
        lambda by: services.record_manual_payment(None, account=None, reason="x", by=by),
    ),
    settlements.confirm: (T4, lambda by: settlements.confirm(None, by=by)),
    settlements.confirm_line: (T4, lambda by: settlements.confirm_line(None, 0, by=by)),
    reconciliation.confirm: (T4, lambda by: reconciliation.confirm(None, by=by)),
    reconciliation.undo: (T4, lambda by: reconciliation.undo(None, reason="x", by=by)),
    reconciliation.exclude: (T4, lambda by: reconciliation.exclude(None, reason="x", by=by)),
    reconciliation.match: (T4, lambda by: reconciliation.match(None, [], by=by)),
    reconciliation.check_match: (T4, lambda by: reconciliation.check_match(None, [], by=by)),
    remittances.build_remittance: (B3, lambda by: remittances.build_remittance("x", None, by)),
    remittances.mark_remittance_sent: (
        B3,
        lambda by: remittances.mark_remittance_sent(None, file_deleted=True, by=by),
    ),
    remittances.settle_remittance: (
        B3,
        lambda by: remittances.settle_remittance(None, None, by=by),
    ),
    sepa_xml.remittance_file: (B3, lambda by: sepa_xml.remittance_file(None, by)),
    refunds.refund: (B5, lambda by: refunds.refund(None, 1, reason="x", key=None, by=by)),
    refunds.discard: (B5, lambda by: refunds.discard(None, reason="x", by=by)),
    returns.register_return: (B4, lambda by: returns.register_return(None, "AM04", by=by)),
    returns.confirm: (B4, lambda by: returns.confirm(None, returns.RETRY, by=by)),
    # A6, o el soci mateix des del compte personal (A2).
    mandates.revoke_mandate: (A6, lambda by: mandates.revoke_mandate(MEMBER, by=by)),
    reviews.close: (B6, lambda by: reviews.close(None, note="x", by=by)),
}

# Serveis sense permís de rol propi, i per què.
UNCHECKED = {
    services.register_movement_guard: "registre de guardes en arrencar",
    services.closed_until: "consulta",
    services.manual_payment_accounts: "consulta",
    services.member_number: "consulta",
    services.record_income: "el sistema, amb un pagament confirmat (notificació, T4 o B3)",
    services.record_fee: "liquidació (T4) o notificació del proveïdor",
    services.record_refund: "`refunds.refund` (B5)",
    services.record_return: "`charges.mark_returned` (B4)",
    services.create_transit_account: "el sistema",
    services.transfer_legs: "`settlements.confirm` (T4)",
    services.record_expense: "només el 09, que en comprovarà el permís",
    services.record_other_income: "només el 09, que en comprovarà el permís",
    settlements.record_settlement: "importació de liquidacions (sistema) o remesa (B3)",
    settlements.fee_split: "càlcul",
    settlements.split: "càlcul",
    reconciliation.refresh: "càlcul de propostes (sistema)",
    reconciliation.has_live_reconciliations: "senyal de la importació",
    reconciliation.on_statement_changed: "senyal de la importació",
    reconciliation.to_review: "consulta (la vista demana T1)",
    reconciliation.pending_charges: "consulta (la vista demana T4)",
    reconciliation.match_problem: "consulta (la vista demana T4)",
    reconciliation.settlement_choices: "consulta (la vista i `confirm_line` demanen T4)",
    remittances.earliest_collection_date: "consulta",
    remittances.preview: "consulta (la vista demana B3)",
    remittances.send_prenotifications: "`build_remittance` i la vista, amb B3",
    remittances.candidate_lines: "consulta (la vista demana B3)",
    returns.max_attempts: "consulta",
    returns.can_retry: "consulta",
    returns.codes: "consulta (P-291)",
    returns.normalise_codes: "forma canònica d'un valor dels ajustos",
    returns.check_codes: "validació: la crida `business_settings.change`, amb el seu permís",
    returns.send_alternative: "correu: `register_return` (B4) o la targeta guardada (sistema)",
    mandates.validate_iban: "validació",
    mandates.next_reference: "càlcul",
    mandates.create_mandate: "el soci mateix des del compte personal (A2)",
    mandates.mail_member: "correu",
    sepa_xml.sepa_text: "format",
    sepa_xml.build: "intern de `remittance_file`",
    sepa_xml.check: "intern de `remittance_file`",
}

MONEY_MODULES = [
    services,
    settlements,
    reconciliation,
    remittances,
    refunds,
    returns,
    mandates,
    reviews,
]


@pytest.mark.parametrize("module", [*MONEY_MODULES, sepa_xml], ids=lambda m: m.__name__)
def test_every_money_service_is_declared(module):
    public = {
        f
        for _, f in inspect.getmembers(import_module(module.__name__), inspect.isfunction)
        if f.__module__ == module.__name__ and not f.__name__.startswith("_")
    }
    declared = {f for f in [*SERVICE_CHECKS, *UNCHECKED] if f.__module__ == module.__name__}
    assert public == declared


# Els rols que el tenen ja els proven les proves de cada servei.
DENIED = [
    (s, role)
    for s, (code, _) in SERVICE_CHECKS.items()
    for role in MANAGEMENT_ROLES
    if role not in CATALOG[code].initial
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("service", "role"), DENIED, ids=[f"{s.__module__}.{s.__name__}-{role}" for s, role in DENIED]
)
def test_service_refuses_a_role_without_the_permission(make_admin, service, role):  # noqa: F811
    with pytest.raises(Http404):
        SERVICE_CHECKS[service][1](make_admin(role))


@pytest.mark.django_db
def test_a_member_cannot_revoke_someone_elses_mandate(personal_account):
    with pytest.raises(Http404):
        mandates.revoke_mandate(MEMBER, by=personal_account)
