"""Taula d'estats finals del cobrament amb la targeta guardada (T-M05b-15c). Una fila per cada
manera com pot acabar una quota amb la targeta guardada: què rep el soci, si el tresorer ho sap
(amb la quota i el càrrec), si queda «a revisar» i si l'endemà es torna a provar. Invariant: cap
quota no queda pendent sense un reintent previst, l'avís al tresorer o «a revisar». Proveïdor
fals; només dades inventades. La taula, amb l'enllaç a cada prova, és al cos de la PR i a
`docs/estat/M05b.md`."""

import pytest
from django.db import connection
from django.utils import timezone

from apps.core.models import AuditEntry, Charge, OutgoingEmail, Person
from apps.members.models import Member
from apps.members.tests.test_cards import add_fee, make_member, pay
from apps.payments import checkout, processing
from apps.payments.models import PaymentAttempt, SavedCard
from apps.payments.providers import base, fake
from apps.payments.tests import test_guest_payment
from apps.payments.tests.test_processing import no_wait, notify, run_queue
from apps.payments.tests.test_saved_card_charge import (  # noqa: F401 (fixtures)
    account,
    clean_orders,
    fee,
    make_admin,
    member,
    saved,
    treasurer,
)

pytestmark = pytest.mark.django_db
S = PaymentAttempt.Status


def _attempt(annual_fee):
    return PaymentAttempt.objects.filter(charge=annual_fee.charge).latest("pk")


def _run(*_):
    checkout.charge_due_saved_cards()


def _notified(status):
    def scenario(ctx):
        _run()
        notify(_attempt(ctx["fee"]), status)
        run_queue()

    return scenario


def _wrap_open(effect):
    def scenario(ctx):
        real = checkout._open_saved_card_attempt

        def then(*args, **kwargs):
            opened = real(*args, **kwargs)
            effect(ctx)
            return opened

        ctx["monkeypatch"].setattr(checkout, "_open_saved_card_attempt", then)
        _run()

    return scenario


def _provider_down(ctx):
    def down(*args, **kwargs):
        raise base.ProviderError("temps esgotat")

    ctx["monkeypatch"].setattr(fake.FakeProvider, "_charge_saved_card", down)
    _run()


def _give_up(ctx):
    _provider_down(ctx)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE payments_paymentattempt SET created_at = created_at - interval '25 hours'"
        )
    no_wait(ctx["monkeypatch"])
    processing.safety_net()


def _unexpected_order(ctx):
    real = fake.FakeProvider._charge_saved_card

    def other(self, charge, card, key):
        order = real(self, charge, card, key)
        return base.ProviderOrder("fake-una-altra", order.pay_url, None)

    ctx["monkeypatch"].setattr(fake.FakeProvider, "_charge_saved_card", other)
    _run()


def _card(**changes):
    def scenario(ctx):
        SavedCard.objects.filter(pk=ctx["saved"].pk).update(**changes)
        _run()

    return scenario


def _member_left(ctx):
    Member.objects.filter(pk=ctx["member"].pk).update(status=Member.Status.LEFT)
    _run()


def _member_pending(ctx):  # també una readmesa: la quota que l'activa, des de la pantalla
    Member.objects.filter(pk=ctx["member"].pk).update(status=Member.Status.PENDING)
    _run()


def _other_person(ctx):
    other = make_member(first="Pau", number=1288, document="87654321X")
    SavedCard.objects.filter(pk=ctx["saved"].pk).update(person=other.person)
    _run()


def _transfer_waiting(ctx):
    ctx["settings"].CLUB_IBAN_TRANSFERENCIES = test_guest_payment.IBAN
    checkout.start_payment(ctx["fee"].charge, "transfer", ctx["account"])
    _run()


def _arrears(ctx):
    ctx["fee"] = add_fee(ctx["member"], period=2025)  # fora de la finestra de cobrament (P-302)
    pay(ctx["first_fee"])
    _run()


def _authentication(ctx):
    fake.FakeProvider().require_authentication(ctx["saved"].provider_card_id)
    _run()


def _amount_changed(ctx):
    Charge.objects.filter(pk=ctx["fee"].charge_id).update(amount_cents=8000)


# fila: (escenari, alternativa al soci, tresorer avisat, «a revisar», es torna a provar l'endemà)
ROWS = {
    "pagat": (_notified(base.PAID), False, False, False, False),
    "denegat": (_notified(base.DENIED), True, True, False, False),
    "ordre caducada": (_notified(base.EXPIRED), True, True, False, False),
    "autenticació": (_authentication, True, True, False, False),
    "ja no pendent": (_wrap_open(lambda ctx: pay(ctx["fee"])), False, False, False, False),
    "import canviat": (_wrap_open(_amount_changed), False, True, True, True),
    "error del proveïdor": (_provider_down, False, True, True, False),
    "xarxa de seguretat": (_give_up, False, True, True, False),
    "ordre inesperada": (_unexpected_order, False, True, True, False),
    "targeta que ja no serveix": (_card(status="removed"), True, True, True, True),
    "ja no és sòcia": (_member_left, False, True, True, True),
    "sòcia pendent (P-309: no)": (_member_pending, False, True, True, True),
    "un altre proveïdor": (_card(provider_code="altre"), False, True, True, True),
    "targeta d'una altra persona": (_other_person, False, True, True, True),
    "transferència en espera": (_transfer_waiting, False, True, True, True),
    "arreus (P-302)": (_arrears, True, False, True, False),  # «a revisar», sense correu
}


@pytest.mark.parametrize("row", list(ROWS))
def test_every_terminal_state(row, saved, fee, member, account, treasurer, monkeypatch, settings):  # noqa: F811
    scenario, alternative, told, review, retried = ROWS[row]
    ctx = {"saved": saved, "fee": fee, "first_fee": fee, "member": member, "account": account,
           "monkeypatch": monkeypatch, "settings": settings}  # fmt: skip
    scenario(ctx)
    fee = ctx["fee"]
    charge = Charge.objects.get(pk=fee.charge_id)

    assert OutgoingEmail.objects.filter(template="alternativa-pagament").exists() == alternative
    notices = OutgoingEmail.objects.filter(template=processing.TREASURER_TEMPLATE)
    assert notices.exists() == told
    if told:  # sempre amb la quota i el càrrec
        assert f"quota {fee.pk}, càrrec {charge.pk}" in notices.first().body_text
    reviewed = AuditEntry.objects.filter(action=processing.TO_REVIEW).exists() or (
        PaymentAttempt.objects.filter(charge=charge, status=S.TO_REVIEW).exists()
    )
    assert reviewed == review
    due = checkout.due_saved_card_charges(timezone.localdate())
    assert any(c.pk == charge.pk for c, _card in due) == retried
    # Invariant: cap quota pendent sense reintent previst, ni avís, ni «a revisar».
    assert charge.status != Charge.Status.PENDING or retried or told or reviewed
    assert Person.objects.filter(pk=member.person_id).exists()
