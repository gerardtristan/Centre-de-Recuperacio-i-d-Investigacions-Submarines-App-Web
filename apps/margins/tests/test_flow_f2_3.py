"""Prova de flux sencer de la llesca F2-3 a nivell de servei (pla d'acceleració, fase 2): activitat
en un lloc amb preu estàndard → preu propi amb nota → cost de material previst copiat de
l'estàndard del 03 → inscripcions pagades a la 04 → despeses amb factura i departament, pagades i
repartides → marge previst → activitat feta → tancament amb `MarginSnapshot`. Només dades
inventades; proveïdor i banc ficticis (092)."""

import pytest
from django.core.exceptions import ValidationError

from apps.activities import enrolment, states
from apps.activities.models import Activity, Enrolment
from apps.activities.tests.helpers import (
    BEFORE_DEADLINE,
    PUBLISHED,
    a_member,
    a_place,
    an_outing,
    moment,
)
from apps.activities.tests.test_material_cost import with_typical_material
from apps.core import audit, charges, events
from apps.core.models import Event, Payment, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import allocation
from apps.expenses import services as expenses
from apps.expenses.models import Expense, ExpenseCategory, Supplier
from apps.expenses.tests.test_expenses import data, invoice
from apps.margins import calc, closing
from apps.margins import services as margins
from apps.treasury import services as treasury
from apps.treasury.models import TreasuryAccount

pytestmark = pytest.mark.django_db
SYSTEM = audit.system("proves-f2-3")
PARTICIPANTS, PRICE, FEE = 10, 6000, 30


def pay(row):
    """El cobrament amb targeta del proveïdor fictici: càrrec pagat, esdeveniment `charge.paid`
    lliurat al 02 i ingrés i comissió a la 04."""
    charges.record_payment(row.charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM)
    events.deliver(Event.objects.get(name=events.CHARGE_PAID, payload__charge=row.charge_id).pk)
    payment = Payment.objects.get(charge=row.charge)
    treasury.record_income(payment, origin="provider", by=SYSTEM)
    treasury.record_fee(payment, FEE, by=SYSTEM)


def paid_expense(treasurer, category, amount, document):
    supplier = Supplier.objects.create(name=f"Proveïdor inventat {category}")
    spent = expenses.record_expense(
        by=treasurer, **data(supplier, category=ExpenseCategory.objects.get(name=category),
                             amount_cents=amount, invoice_number=f"F-{category}")
    )  # fmt: skip
    # Adjuntar el fitxer és de la T-M09-25: aquí, directe a la fila.
    Expense.objects.filter(pk=spent.pk).update(invoice_file=document)
    bank = TreasuryAccount.objects.get(name="Banc principal")
    return expenses.pay(spent, account=bank, value_date=spent.invoice_date, by=treasurer)


def test_f2_3_from_the_place_price_to_the_frozen_margin(make_admin):  # noqa: F811
    manager, treasurer = make_admin(Role.Code.COURSES_MANAGER), make_admin(Role.Code.TREASURER)
    with_typical_material(cost_per_day=175)  # sortida de dos dies: 350 per participant
    place = a_place(manager, prices=(4500, 6000))

    # Preu propi diferent de l'estàndard del lloc: sense nota, es rebutja (CA-M02-43).
    own_prices = {"place": place, "price_member_cents": PRICE, "price_non_member_cents": 7500}
    with pytest.raises(ValidationError):
        an_outing(manager, **own_prices)
    activity = an_outing(manager, price_override_note="Inclou el dinar (inventat).", **own_prices)
    activity.refresh_from_db()
    assert (activity.standard_price_member_cents, activity.price_member_cents) == (4500, PRICE)
    # Cost de material previst copiat de l'estàndard del 03 (RN-M02-43).
    assert (activity.standard_material_cost_cents, activity.material_cost_cents) == (350, 350)

    states.publish(activity, by=manager, now=PUBLISHED)
    for i in range(PARTICIPANTS):
        account = a_member(f"Sòcia {i}")
        row = enrolment.enrol(
            activity, account.person, channel="account", actor=account, now=BEFORE_DEADLINE
        )
        assert (row.status, row.price_cents) == (Enrolment.Status.PENDING_PAYMENT, PRICE)
        pay(row)
    # El subscriptor de `charge.paid` (T-M02-10) ha confirmat cada inscripció.
    assert (
        Enrolment.objects.filter(activity=activity, status=Enrolment.Status.CONFIRMED).count()
        == PARTICIPANTS
    )

    document = invoice(treasurer.person)  # una factura inventada per a totes dues
    boat = paid_expense(treasurer, "Embarcació", 25000, document)
    air = paid_expense(treasurer, "Aire", 12000, document)
    for spent in (boat, air):
        allocation.allocate(spent, [activity], "equal", by=treasurer)

    forecast = margins.activity_margin(activity)
    assert forecast.income_enrolments_cents == PARTICIPANTS * PRICE == 60000
    assert forecast.breakdown["costs_by_category"] == {"Embarcació": 25000, "Aire": 12000}
    assert forecast.material_cost_cents == PARTICIPANTS * 350
    assert forecast.margin_cents == 60000 - 37000 - 3500 == 19500

    states.mark_done(activity, by=manager, now=moment(2027, 6, 16, 12))
    snapshot = closing.close_activity(activity, by=treasurer)
    activity.refresh_from_db()
    assert activity.status == Activity.Status.CLOSED
    # Real: ingressos de la 04 menys repartiments i comissions. El cost de material real del 03
    # arriba amb la T-M03-13: fins llavors el real no el resta (`material_source = none`).
    assert snapshot.margin_cents == 60000 - 37000 - PARTICIPANTS * FEE == 22700
    assert (snapshot.participants, snapshot.margin_pct_tenths) == (PARTICIPANTS, 378)
    assert margins.activity_margin(activity, calc.REAL).margin_cents == snapshot.margin_cents
