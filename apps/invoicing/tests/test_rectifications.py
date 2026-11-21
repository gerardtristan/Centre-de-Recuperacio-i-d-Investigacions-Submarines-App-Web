"""T-M09-20: rectificatives des de les devolucions (RN-M09-18; CA-M09-18; L-M09-08). Només dades
inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.invoicing import services
from apps.invoicing.models import Invoice
from apps.invoicing.tests.test_invoices import COMPANY, deliver_last, enabled, fresh, pay  # noqa: F401
from apps.treasury import services as treasury
from apps.treasury.models import Movement
from apps.treasury.tests.test_record_income import SYSTEM, record

pytestmark = pytest.mark.django_db


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


@pytest.fixture
def invoiced(enabled):  # noqa: F811
    charge = pay()
    deliver_last()
    payment = charge.payments.get()
    record(payment)
    return Invoice.objects.get(charge=charge), payment


def refund(payment, amount):
    return treasury.record_refund(payment, amount, reason="Baixa de la sortida", by=SYSTEM)


def test_ca_m09_18_rectificativa_parcial_lligada_a_la_factura(invoiced, treasurer):
    invoice, payment = invoiced
    rectification = services.issue_rectification(
        invoice, refund(payment, 2000), reason="Devolució parcial", by=treasurer
    )
    assert (rectification.series, rectification.status, rectification.number) == (
        "R",
        "issued",
        "R-000001",
    )
    assert (rectification.rectifies, rectification.total_cents) == (invoice, 2000)
    assert rectification.customer_person == invoice.customer_person
    second = services.issue_rectification(
        invoice, refund(payment, 4000), reason="La resta", by=treasurer
    )
    assert second.number == "R-000002"
    assert sum(invoice.rectifications.values_list("total_cents", flat=True)) == 6000


def test_una_devolucio_te_una_sola_rectificativa(invoiced, treasurer):
    invoice, payment = invoiced
    movement = refund(payment, 2000)
    services.issue_rectification(invoice, movement, reason="Devolució", by=treasurer)
    with pytest.raises(services.AlreadyRectified):
        services.issue_rectification(invoice, movement, reason="Una altra vegada", by=treasurer)


def test_no_passa_de_l_import_de_la_factura(invoiced, treasurer):
    invoice, payment = invoiced
    Invoice.objects.filter(pk=invoice.pk).update(base_cents=1000, total_cents=1000)
    with pytest.raises(services.AlreadyRectified):
        services.issue_rectification(invoice, refund(payment, 2000), reason="Massa", by=treasurer)


def test_l_m09_08_una_devolucio_sense_factura_o_d_un_altre_cobrament(invoiced, treasurer):
    invoice, payment = invoiced
    other = pay()
    other_payment = other.payments.get()
    record(other_payment)
    with pytest.raises(ValidationError):
        services.issue_rectification(
            invoice, refund(other_payment, 1000), reason="Una altra", by=treasurer
        )
    income = Movement.objects.filter(payment=payment, kind=Movement.Kind.INCOME).get()
    with pytest.raises(ValidationError):
        services.issue_rectification(invoice, income, reason="No és devolució", by=treasurer)
    with pytest.raises(ValidationError):
        services.issue_rectification(invoice, refund(payment, 1000), reason=" ", by=treasurer)


def test_nomes_es_rectifica_una_ordinaria_emesa_d_un_cobrament(invoiced, treasurer):
    invoice, payment = invoiced
    movement = refund(payment, 1000)
    Invoice.objects.filter(pk=invoice.pk).update(status="failed")
    with pytest.raises(ValidationError):
        services.issue_rectification(invoice, movement, reason="Fallida", by=treasurer)
    manual = services.issue_manual(**COMPANY, lines=[("Lloguer", 1, 6000)], by=treasurer)
    with pytest.raises(ValidationError):
        services.issue_rectification(manual, movement, reason="Sense cobrament", by=treasurer)


@pytest.mark.parametrize("role", ["secretary", "board", "president"])
def test_rectificar_demana_mg9(invoiced, make_admin, role):  # noqa: F811
    invoice, payment = invoiced
    with pytest.raises(Http404):
        services.issue_rectification(
            invoice, refund(payment, 1000), reason="Devolució", by=make_admin(role)
        )
