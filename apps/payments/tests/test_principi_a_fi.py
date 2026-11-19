"""Proves de principi a fi dels camins dels diners (T-M05b-18; decisió 092: proveïdor i banc
ficticis). Cada camí passa pels serveis reals, de l'acció de qui paga fins a la tresoreria, i
comprova els saldos (`balances.py`), el registre d'activitat i que cap IBAN sencer no surt del
mandat xifrat (044): ni al registre, ni als correus, ni a les notificacions.

Camins: quota amb targeta i amb Bizum fins al carnet vàlid; transferència amb l'extracte en CSV i
en Norma 43, conciliació i rebut; desfer-la (045) i tornar a pagar; devolució parcial i total;
convidat amb l'enllaç de la 00; mandat → remesa → avís → pain.008 → enviada → liquidada amb la
línia del banc → soci actiu; retorn → alternativa → targeta; liquidació del proveïdor importada i
confirmada amb el trànsit a zero. Només dades inventades."""

import json
from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import audit, charges, guest_links, imports
from apps.core.imports import bank_statement, statement_lines
from apps.core.models import (
    AuditEntry,
    Charge,
    Department,
    LegalText,
    OutgoingEmail,
    Payment,
    Person,
    Role,
)
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards
from apps.members.models import Member
from apps.members.tests.test_cards import add_fee, make_member
from apps.payments import (
    checkout,
    mandates,
    refunds,
    remittances,
    returns,
    sepa_xml,
    settlements,
)
from apps.payments.models import (
    DirectDebitItem,
    PaymentAttempt,
    ProviderEvent,
    Receipt,
    ReceiptCancellation,
)
from apps.payments.providers import fake
from apps.payments.tests.test_preferences import prefer
from apps.payments.tests.test_processing import notify, run_queue
from apps.treasury import reconciliation, references
from apps.treasury import services as treasury
from apps.treasury import settlements as treasury_settlements
from apps.treasury.balances import balance
from apps.treasury.demo_data import _csv, _norma43, iban
from apps.treasury.models import StatementLineState, TreasuryAccount
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
S = PaymentAttempt.Status


def today():
    """Avui en executar la prova, no en carregar el fitxer (P-315b: mitjanit)."""
    return timezone.localdate()


SYSTEM = audit.system("proves")
CREDITOR = "ES00ZZZ00000000"


@pytest.fixture(autouse=True)
def club(settings):
    settings.SEPA_CREDITOR_IDENTIFIER = CREDITOR
    settings.CLUB_IBAN_TRANSFERENCIES = iban(999)
    settings.TRANSFER_REFERENCE_PREFIX = "CRIS"
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(Role.Code.TREASURER)


def account(kind, provider_code=""):
    if kind == "bank":
        return TreasuryAccount.objects.get(name="Banc principal")
    return TreasuryAccount.objects.get(kind=kind, provider_code=provider_code)


def at(acc, day=None):
    """Saldo d'un compte, sempre dels moviments (RN-T02)."""
    return balance(acc, day or today() + timedelta(days=60))


def pending_member(n, *, email=True):
    """Soci aprovat, pendent de la primera quota (90 €), amb el compte personal actiu."""
    member = make_member(
        first=f"Soci{n}", number=n, status=Member.Status.PENDING, document=f"{n:08d}X"
    )
    if email:
        Person.objects.filter(pk=member.person_id).update(contact_email=f"soci{n}@example.org")
    fee = add_fee(member)
    login = Account.objects.create_personal(member.person, f"soci{n}@example.org", PASSWORD)
    login.status = Account.Status.ACTIVE
    login.save()
    return member, fee, login


def card_valid(member) -> bool:
    return cards.validity(cards.load_member(member.pk), cards.active_card(member)).valid


def pay_by_provider(charge, method, payer):
    start = checkout.start_payment(charge, method, payer)
    attempt = PaymentAttempt.objects.get(pk=start.attempt_id)
    notify(attempt, event_id=f"ev-{attempt.pk}")
    run_queue()
    attempt.refresh_from_db()
    return attempt


def actions() -> set:
    return set(AuditEntry.objects.values_list("action", flat=True))


def assert_no_iban(*values):
    """Cap IBAN sencer (ni agrupat de quatre en quatre) fora del mandat xifrat i del fitxer."""
    logged = json.dumps(list(AuditEntry.objects.values()), default=str)
    mails = json.dumps(list(OutgoingEmail.objects.values("subject", "body_text")), default=str)
    events = json.dumps(list(ProviderEvent.objects.values()), default=str)
    for value in values:
        grouped = " ".join(value[i : i + 4] for i in range(0, len(value), 4))
        for text in (logged, mails, events):
            assert value not in text and grouped not in text


def import_statement(data, by):
    """L'extracte del banc fictici per la importació real (previsualitzar i confirmar), que
    recalcula les propostes de la conciliació."""
    return bank_statement.confirm(bank_statement.preview(data, by=by)["token"], by=by)


def bank_line(amount, by, day):
    batch = imports.open_confirmed(
        "bank_statement", file_sha256=uuid4().hex * 2, by=by, counts={"new_count": 1}
    )
    row = {
        "row": 2,
        "result": "new",
        "value_date": day,
        "amount_cents": amount,
        "concept": "ABONO REMESA",
        "balance_cents": None,
    }
    imports.add_lines(batch, [row])
    return statement_lines(batch).get()


# --- Targeta i Bizum: de la quota pendent al carnet vàlid ------------------------------------


@pytest.mark.parametrize("method", ["card", "bizum"])
def test_fee_by_provider_reaches_treasury_receipt_and_card(method):
    member, fee, login = pending_member(1)
    transit = account("transit", "fake")

    attempt = pay_by_provider(fee.charge, method, login)

    fee.charge.refresh_from_db()
    member.refresh_from_db()
    assert attempt.status == S.PAID and fee.charge.status == Charge.Status.PAID
    assert Payment.objects.get(charge=fee.charge).method == method
    assert at(transit) == 9000
    receipt = Receipt.objects.get(attempt=attempt)
    assert receipt.number.startswith(f"R-{today().year}-")
    assert OutgoingEmail.objects.filter(template="pagament-confirmat", person=member.person)
    assert member.status == Member.Status.ACTIVE and card_valid(member)
    assert {
        "payments.attempt_created",
        "payments.order_created",
        "payments.attempt_status_changed",
        "charges.status_changed",
    } <= actions()


# --- Transferència: extracte, proposta, conciliació, desfer (045) i tornar a pagar ----------


def transfer_statement(fmt, charge):
    text = f"TRANSF {references.transfer_reference(charge)} QUOTA"
    if fmt == "csv":
        return _csv(today(), [(0, text, charge.amount_cents)])
    return _norma43(today(), [(0, text, charge.amount_cents)])


@pytest.mark.parametrize("fmt", ["csv", "norma43"])
def test_transfer_statement_reconcile_and_receipt(fmt, treasurer):
    member, fee, login = pending_member(2)
    bank = account("bank")
    start = checkout.start_payment(fee.charge, "transfer", login)
    assert start.club_iban == iban(999) and start.reference

    batch = import_statement(transfer_statement(fmt, fee.charge), treasurer)
    (line,) = statement_lines(batch)
    assert StatementLineState.objects.get(statement_line=line).status == "proposed"
    reconciliation.confirm(line, by=treasurer)

    fee.charge.refresh_from_db()
    member.refresh_from_db()
    assert fee.charge.status == Charge.Status.PAID and member.status == Member.Status.ACTIVE
    attempt = PaymentAttempt.objects.get(pk=start.attempt_id)
    assert attempt.status == S.PAID and Receipt.objects.filter(attempt=attempt).exists()
    assert at(bank) == 9000
    assert reconciliation.CONFIRMED in actions()
    assert_no_iban(iban(999))


def test_undo_a_reconciled_transfer_then_pay_again_by_card(treasurer):
    member, fee, login = pending_member(3)
    bank, transit = account("bank"), account("transit", "fake")
    checkout.start_payment(fee.charge, "transfer", login)
    batch = import_statement(transfer_statement("csv", fee.charge), treasurer)
    confirmed = reconciliation.confirm(statement_lines(batch).get(), by=treasurer)
    first = Receipt.objects.get()

    reconciliation.undo(confirmed, reason="Era d'un altre soci (dada de prova).", by=treasurer)

    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.PENDING
    assert ReceiptCancellation.objects.filter(receipt=first).exists()
    assert at(bank) == 0  # l'ingrés i el contramoviment

    again = pay_by_provider(fee.charge, "card", login)
    fee.charge.refresh_from_db()
    assert again.status == S.PAID and fee.charge.status == Charge.Status.PAID
    assert Receipt.objects.filter(attempt=again).exclude(pk=first.pk).exists()
    assert (at(bank), at(transit)) == (0, 9000)


# --- Devolucions pel proveïdor: parcial i total --------------------------------------------


def test_partial_then_total_refund(treasurer):
    member, fee, login = pending_member(4)
    transit = account("transit", "fake")
    pay_by_provider(fee.charge, "card", login)
    payment = Payment.objects.get(charge=fee.charge)

    refunds.refund(payment, 3000, reason="Part no feta (prova).", key=uuid4(), by=treasurer)
    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.PAID and at(transit) == 6000

    refunds.refund(payment, 6000, reason="La resta (prova).", key=uuid4(), by=treasurer)
    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.CANCELLED and at(transit) == 0
    assert ReceiptCancellation.objects.filter(receipt__attempt__charge=fee.charge).exists()
    assert refunds.REFUNDED in actions()


# --- Convidat amb l'enllaç de la 00 --------------------------------------------------------


def test_guest_pays_with_the_link():
    person = Person.objects.create(
        first_name="Mar", last_name="Convidada", origin="web", contact_email="mar@example.org"
    )
    charge = charges.create_charge(
        person, kind=Charge.Kind.ENROLMENT, amount_cents=12000, concept="Curs (prova)",
        origin="proves", department=Department.objects.get(name=Department.GENERAL), by=SYSTEM,
    )  # fmt: skip
    link = guest_links.create(person, charge, by=SYSTEM)

    attempt = pay_by_provider(charge, "card", link)

    charge.refresh_from_db()
    assert attempt.status == S.PAID and attempt.guest_link == link and not attempt.started_by
    assert charge.status == Charge.Status.PAID
    assert Payment.objects.get(charge=charge).charge.person == person  # RN-33 de la 00
    assert at(account("transit", "fake")) == 12000
    assert AuditEntry.objects.filter(
        action="payments.attempt_created", actor_kind="guest", actor_person=person
    ).exists()


# --- Domiciliació: mandat, remesa, avís, fitxer, enviada i liquidada ------------------------


def debit_member(n, treasurer):
    member, fee, login = pending_member(n)
    text = LegalText.objects.get_or_create(
        kind="sepa_mandate", version=1, defaults={"content": "Text de prova."}
    )[0]
    mandate = mandates.create_mandate(
        member, iban=iban(n), holder_name="Titular Prova", holder_is_member=True,
        legal_text=text, account=login, creditor_identifier=CREDITOR,
        evidence={"channel": "web"},
    )  # fmt: skip
    prefer(member, login, "direct_debit", mandate=mandate)
    return member, fee, login


def settled_remittance(treasurer):
    first = debit_member(11, treasurer)
    second = debit_member(12, treasurer)
    remittance = remittances.build_remittance(
        "2026-12", remittances.earliest_collection_date(), treasurer
    )
    assert remittance.status == "notified"  # l'avís previ, per la cua
    assert OutgoingEmail.objects.filter(template="avis-previ-remesa").count() == 2
    content = sepa_xml.remittance_file(remittance, treasurer)
    assert iban(11).encode() in content  # el fitxer sí, i no es desa (RN-M05b-12)
    remittances.mark_remittance_sent(remittance, file_deleted=True, by=treasurer)
    line = bank_line(remittance.total_cents, treasurer, remittance.collection_date)
    remittances.settle_remittance(remittance, line, by=treasurer)
    remittance.refresh_from_db()
    return remittance, first, second


def test_mandate_to_settled_remittance_and_active_member(treasurer):
    remittance, (member, fee, _login), _second = settled_remittance(treasurer)

    member.refresh_from_db()
    fee.charge.refresh_from_db()
    assert remittance.status == "settled" and fee.charge.status == Charge.Status.PAID
    assert member.status == Member.Status.ACTIVE and card_valid(member)
    sepa = account("transit", treasury.SEPA_REMITTANCE)
    assert at(sepa) == 0 and at(account("bank")) == 18000
    assert {"payments.remittance.sent", "payments.remittance.settled"} <= actions()
    assert treasury_settlements.CONFIRMED in actions()
    assert_no_iban(iban(11), iban(12))


def test_return_alternative_then_card(treasurer):
    remittance, (member, fee, login), _second = settled_remittance(treasurer)
    item = DirectDebitItem.objects.get(attempt__charge=fee.charge)

    proposal = returns.register_return(item, "MS02", by=treasurer)
    assert proposal == returns.ALTERNATIVE
    assert returns.confirm(item, returns.ALTERNATIVE, by=treasurer)
    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.PENDING
    mail = OutgoingEmail.objects.get(template=returns.ALTERNATIVE_TEMPLATE)
    assert f"/socis/pagaments/{fee.charge.pk}/" in mail.body_text

    again = pay_by_provider(fee.charge, "card", login)
    fee.charge.refresh_from_db()
    assert again.status == S.PAID and fee.charge.status == Charge.Status.PAID
    assert at(account("transit", "fake")) == 9000
    assert {"payments.return.registered", "payments.return.confirmed"} <= actions()
    assert_no_iban(iban(11), iban(12))


def test_a_return_after_settlement_leaves_the_sepa_transit_at_zero(treasurer):
    """P-286 (opció C): el retorn d'una remesa ja liquidada el carrega el banc, i el trànsit
    «Remeses SEPA», ja traspassat, queda a zero."""
    _remittance, (_member, fee, _login), _second = settled_remittance(treasurer)
    item = DirectDebitItem.objects.get(attempt__charge=fee.charge)
    returns.register_return(item, "MS02", by=treasurer)
    assert at(account("transit", treasury.SEPA_REMITTANCE)) == 0


# --- Liquidació del proveïdor: importada, confirmada i el trànsit a zero --------------------


def test_provider_settlement_import_and_confirm(treasurer):
    paid = []
    for n in (21, 22):
        _member, fee, login = pending_member(n)
        paid.append(pay_by_provider(fee.charge, "card", login))
    transit, bank = account("transit", "fake"), account("bank")
    assert at(transit) == 18000

    fake.FakeProvider().settle(
        [(attempt.provider_order_id, attempt.amount_cents) for attempt in paid],
        fees_cents=120,
        settled_on=today(),
        external_id="LIQ-PROVA",
    )
    (settlement,) = settlements.import_settlements()
    treasury_settlements.confirm(settlement, by=treasurer)

    assert at(transit) == 0 and at(bank) == 18000 - 120
    assert {treasury_settlements.RECORDED, treasury_settlements.CONFIRMED} <= actions()
