"""T-M09A-13: prova de principi a fi dels ajuts a nivell de servei: convocatòria → elegibilitat
revisada → sol·licitud preparada i presentada → concedida → ingrés de l'ajut a la 04 → despeses
lligades amb els límits → informe del departament amb l'ajut en una línia pròpia. Només dades
inventades."""

import datetime
import uuid

import pytest

from apps.core.models import Department, PrivateFile, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import services as expenses
from apps.expenses.models import ExpenseCategory, OtherIncome, Supplier
from apps.grants import income, justification, services
from apps.grants.models import GrantApplication, GrantCall, GrantCallDocument
from apps.margins import reports
from apps.treasury.models import Movement, TreasuryAccount

pytestmark = pytest.mark.django_db
S = GrantApplication.Status
YEAR = (datetime.date(2027, 1, 1), datetime.date(2027, 12, 31))


def document(person, name):
    return PrivateFile.objects.create(
        storage_key=f"prova-{uuid.uuid4().hex}", kind=PrivateFile.Kind.PAYMENT_PROOF,
        owner=person, content_type="application/pdf", size_bytes=10, download_name=name,
    )  # fmt: skip


def test_t_m09a_13_from_the_call_to_the_linked_expenses(make_admin):  # noqa: F811
    treasurer = make_admin(Role.Code.TREASURER)
    general = Department.objects.get(name=Department.GENERAL)
    call = GrantCall.objects.create(
        body="Diputació Inventada", name="Medi marí", created_by=treasurer, max_resolution_days=90
    )
    for order, name in enumerate(["Memòria del projecte", "Pressupost"]):
        GrantCallDocument.objects.create(call=call, name=name, order=order)

    # Detectada, elegibilitat revisada per una persona, preparada amb els documents i presentada.
    application = services.create_application(
        call, responsible=treasurer.person, department=general, by=treasurer
    )
    assert application.status == S.DETECTED
    services.review_eligibility(
        call, status="eligible", notes="Complim els requisits", by=treasurer
    )
    services.transition(application, S.PREPARING, by=treasurer)
    for row in application.documents.all():
        services.set_document_ready(row, ready=True, by=treasurer)
    services.transition(
        application, S.SUBMITTED, by=treasurer, submitted_on=datetime.date(2027, 2, 1),
        submission_ref="RE-2027-001", amount_requested_cents=300000,
    )  # fmt: skip
    granted = services.transition(
        application, S.GRANTED, by=treasurer, resolved_on=datetime.date(2027, 6, 1),
        resolution_file=document(treasurer.person, "resolucio.pdf"), amount_granted_cents=240000,
    )  # fmt: skip
    assert (granted.status, granted.amount_granted_cents) == (S.GRANTED, 240000)

    # L'ingrés de l'ajut: a la 04, al departament, sense cap activitat (RN-M09-08).
    bank = TreasuryAccount.objects.get(name="Banc principal")
    advance = income.record_income(
        granted, amount_cents=120000, account=bank, value_date=datetime.date(2027, 7, 1),
        by=treasurer,
    )  # fmt: skip
    assert (advance.kind, advance.department, advance.grant_application) == (
        OtherIncome.Kind.GRANT, general, granted,
    )  # fmt: skip
    assert Movement.objects.filter(kind=Movement.Kind.OTHER_INCOME).count() == 1

    # Despeses del departament lligades a l'ajut, amb el límit de la despesa.
    spent = expenses.record_expense(
        by=treasurer, supplier=Supplier.objects.create(name="Nàutica Inventada SL"),
        invoice_number="F-1", invoice_date=datetime.date(2027, 7, 10),
        category=ExpenseCategory.objects.get(name="Embarcació"),
        description="Sortida de mostreig (inventat)", amount_cents=10000, department=general,
    )  # fmt: skip
    link = justification.link_expense(granted, spent, 6000, by=treasurer)
    assert link.amount_cents == 6000
    other = expenses.record_expense(
        by=treasurer, supplier=Supplier.objects.get(name="Nàutica Inventada SL"),
        invoice_number="F-2", invoice_date=datetime.date(2027, 7, 11),
        category=ExpenseCategory.objects.get(name="Aire"), description="Aire (inventat)",
        amount_cents=2000, department=general,
    )  # fmt: skip
    with pytest.raises(justification.OverImputed):  # més que la despesa
        justification.link_expense(granted, other, 2001, by=treasurer)

    # L'informe del departament: l'ajut en una línia pròpia, mai dins el marge d'una activitat.
    expenses.pay(spent, account=bank, value_date=datetime.date(2027, 7, 15), by=treasurer)
    report = reports.department_report(general, *YEAR)
    assert (report.grants_cents, report.activity_margins_cents) == (120000, {})
    assert report.expenses_without_activity_cents == 10000
    assert report.total_cents == 120000 - 10000
