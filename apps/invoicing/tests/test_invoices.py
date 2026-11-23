"""T-M09-19: factura d'un cobrament (subscriptor de `charge.paid`), factura manual i control de
salts (RN-M09-17 i 19; CA-M09-16, 17 i 19; L-M09-06). Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.core import events
from apps.core.models import AuditEntry, Department, Event, OutgoingEmail, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.invoicing import services
from apps.invoicing.models import Invoice, InvoiceLine
from apps.invoicing.providers.fake import FakeInvoicingProvider
from apps.treasury.tests.test_record_income import paid

pytestmark = pytest.mark.django_db
COMPANY = {"customer_name": "Empresa Inventada SL", "customer_tax_id": "B00000000"}


@pytest.fixture(autouse=True)
def fresh():
    FakeInvoicingProvider.reset()
    yield
    FakeInvoicingProvider.reset()


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(services, "enabled_kinds", lambda on=None: {"enrolment"})


def pay(kind="enrolment", amount=6000):
    person = Person.objects.create(first_name="Laia", last_name="Inventada", origin="web")
    general = Department.objects.get(name="General")
    return paid(person, kind=kind, amount=amount, department=general).charge


def deliver_last():
    events.deliver(Event.objects.filter(name=events.CHARGE_PAID).latest("pk").pk)


def test_ca_m09_19_desactivada_per_defecte_no_es_crea_cap_factura():
    assert services.enabled_kinds() == set()
    pay()
    deliver_last()
    assert not Invoice.objects.exists()


def test_ca_m09_16_un_charge_paid_repetit_fa_una_sola_factura(enabled):
    charge = pay()
    deliver_last()
    services.on_charge_paid(Event.objects.latest("pk"))  # el subscriptor, una altra vegada
    invoice = Invoice.objects.get()
    assert (invoice.series, invoice.status, invoice.number) == ("F", "issued", "F-000001")
    assert (invoice.charge, invoice.customer_person, invoice.total_cents) == (
        charge,
        charge.person,
        6000,
    )
    assert InvoiceLine.objects.get().description == "Concepte del càrrec"
    assert invoice.qr_payload.startswith("fake-verifactu:")


def test_un_tipus_no_activat_no_es_factura(enabled):
    pay(kind="fee")
    deliver_last()
    assert not Invoice.objects.exists()


def test_ca_m09_17_un_salt_a_la_serie_queda_al_registre_i_avisa_el_tresorer(
    enabled,
    make_admin,  # noqa: F811
):
    treasurer = make_admin("treasurer")
    treasurer.notification_email = "tresoreria@example.org"
    treasurer.save()
    secretary = make_admin("secretary")  # sense MG2: no rep l'avís
    secretary.notification_email = "secretaria@example.org"
    secretary.save()
    pay()
    deliver_last()
    FakeInvoicingProvider.next_skip = 1
    pay()
    deliver_last()
    assert list(Invoice.objects.values_list("number", flat=True)) == ["F-000001", "F-000003"]
    gap = AuditEntry.objects.get(action=services.SERIES_GAP)
    assert (gap.details["expected"], gap.details["got"]) == (2, 3)
    sent = OutgoingEmail.objects.get(template=services.SERIES_GAP_TEMPLATE)
    assert sent.to_address == "tresoreria@example.org"
    assert "sèrie F s'esperava el número 2" in sent.body_text and "donat el 3." in sent.body_text
    assert "Inventada" not in sent.body_text  # cap dada del client


def test_una_serie_sense_salts_no_avisa(enabled, make_admin):  # noqa: F811
    treasurer = make_admin("treasurer")
    treasurer.notification_email = "tresoreria@example.org"
    treasurer.save()
    for _ in range(2):
        pay()
        deliver_last()
    assert not OutgoingEmail.objects.filter(template=services.SERIES_GAP_TEMPLATE).exists()


def test_un_numero_repetit_o_un_servei_que_no_respon_deixen_la_factura_fallida(enabled):
    pay()
    deliver_last()
    FakeInvoicingProvider.next_repeat = True
    pay()
    deliver_last()
    FakeInvoicingProvider.fail_next = 1
    pay()
    deliver_last()
    failed = Invoice.objects.filter(status="failed")
    assert failed.count() == 2
    assert AuditEntry.objects.filter(action=services.INVOICE_FAILED).count() == 2

    assert services.retry_failed() == 2  # L-M09-06: reintents
    assert sorted(Invoice.objects.values_list("number", flat=True)) == [
        "F-000001",
        "F-000002",
        "F-000003",
    ]


def test_factura_manual_a_una_empresa(enabled, make_admin):  # noqa: F811
    treasurer = make_admin("treasurer")
    invoice = services.issue_manual(
        **COMPANY, lines=[("Lloguer de la sala", 2, 5000), ("Material", 1, 1200)], by=treasurer
    )
    assert (invoice.status, invoice.total_cents, invoice.lines.count()) == ("issued", 11200, 2)
    assert AuditEntry.objects.get(action=services.MANUAL_REQUESTED).actor_account == treasurer


@pytest.mark.parametrize(
    ("customer", "lines"),
    [
        ({**COMPANY, "customer_tax_id": ""}, [("Lloguer", 1, 100)]),
        (COMPANY, []),
        (COMPANY, [("", 1, 100)]),
        (COMPANY, [("Lloguer", 0, 100)]),
        (COMPANY, [("Lloguer", 1, 1.5)]),
        (COMPANY, [("Lloguer", True, 100)]),
    ],
)
def test_factura_manual_amb_dades_que_no_valen(enabled, make_admin, customer, lines):  # noqa: F811
    with pytest.raises(ValidationError):
        services.issue_manual(**customer, lines=lines, by=make_admin("treasurer"))
    assert not Invoice.objects.exists()


def test_factura_manual_demana_mg9_i_la_facturacio_activada(make_admin, monkeypatch):  # noqa: F811
    lines = [("Lloguer", 1, 100)]
    with pytest.raises(services.InvoicingDisabled):
        services.issue_manual(**COMPANY, lines=lines, by=make_admin("treasurer"))
    monkeypatch.setattr(services, "enabled_kinds", lambda on=None: {"enrolment"})
    for role in ("secretary", "board", "president"):
        with pytest.raises(Http404):
            services.issue_manual(**COMPANY, lines=lines, by=make_admin(role))


def test_l_ajust_nomes_admet_tipus_de_carrec():
    services.check_enabled_kinds("")
    services.check_enabled_kinds("ENROLMENT, FEE, LICENCE")
    with pytest.raises(ValidationError):
        services.check_enabled_kinds("ENROLMENT, SHOP")


def test_restriccions_de_la_base_de_dades(enabled):
    pay()
    deliver_last()
    invoice = Invoice.objects.get()
    assert str(invoice) == "F F-000001"
    with pytest.raises(IntegrityError), transaction.atomic():
        Invoice.objects.create(series="F", charge=invoice.charge, base_cents=1, tax_cents=0,
                               total_cents=1)  # fmt: skip
    with pytest.raises(IntegrityError), transaction.atomic():
        Invoice.objects.create(series="F", base_cents=1, tax_cents=0, total_cents=2)
    with pytest.raises(IntegrityError), transaction.atomic():
        Invoice.objects.create(series="R", base_cents=1, tax_cents=0, total_cents=1)
    with pytest.raises(IntegrityError), transaction.atomic():
        Invoice.objects.create(series="F", base_cents=1, tax_cents=0, total_cents=1,
                               status="issued")  # fmt: skip
    assert str(InvoiceLine.objects.get()) == "Concepte del càrrec"
