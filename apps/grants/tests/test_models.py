"""T-M09A-02: restriccions dels models d'ajuts (M09-ajuts-6). Només dades inventades."""

from datetime import date

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.models import AppendOnlyError, Department
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.grants.models import (
    ApplicationDocument,
    ApplicationTransition,
    GrantApplication,
    GrantCall,
    GrantCallDocument,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


def new_call(by, **extra):
    return GrantCall.objects.create(
        **{"body": "Diputació Inventada", "name": "Medi marí", "created_by": by, **extra}
    )


def new_application(call, by, **extra):
    fields = {
        "call": call,
        "responsible": by.person,
        "department": Department.objects.get(name="General"),
        "created_by": by,
    }
    return GrantApplication.objects.create(**{**fields, **extra})


def rejects(create):
    with pytest.raises(IntegrityError), transaction.atomic():
        create()


def test_una_convocatoria_neix_pendent_de_revisar_i_sense_saber_si_accepta_copies(treasurer):
    call = new_call(treasurer, edition_label="2027")
    assert (call.eligibility_status, call.accepts_masked_proofs) == ("pending", "unknown")
    assert str(call) == "Diputació Inventada: Medi marí 2027"


@pytest.mark.parametrize(
    "extra",
    [
        {"opens_on": date(2027, 3, 1), "closes_on": date(2027, 2, 1)},
        {"eligible_expenses_from": date(2027, 3, 1), "eligible_expenses_to": date(2027, 2, 1)},
        {"eligibility_status": "maybe"},
        {"accepts_masked_proofs": "maybe"},
        {"eligibility_status": "eligible"},  # sense qui, quan ni notes (RN-M09A-03)
    ],
)
def test_restriccions_de_la_convocatoria(treasurer, extra):
    rejects(lambda: new_call(treasurer, **extra))


def test_una_revisio_completa_s_accepta(treasurer):
    call = new_call(
        treasurer,
        opens_on=date(2027, 1, 1),
        closes_on=date(2027, 1, 1),
        eligibility_status="not_eligible",
        eligibility_reviewed_by=treasurer,
        eligibility_reviewed_at=timezone.now(),
        eligibility_notes="Només per a entitats esportives",
    )
    assert call.eligibility_status == "not_eligible"


def test_documents_requerits_unics_i_amb_nom(treasurer):
    call = new_call(treasurer)
    document = GrantCallDocument.objects.create(call=call, name="Memòria del projecte")
    assert str(document) == "Memòria del projecte"
    rejects(lambda: GrantCallDocument.objects.create(call=call, name="Memòria del projecte"))
    rejects(lambda: GrantCallDocument.objects.create(call=call, name=""))


def test_una_sollicitud_neix_detectada(treasurer):
    application = new_application(new_call(treasurer), treasurer)
    assert application.status == "detected"
    assert str(application) == "Diputació Inventada: Medi marí (Detectada)"


@pytest.mark.parametrize(
    "extra",
    [
        {"status": "won"},
        {"status": "submitted"},  # sense data, registre ni import (RN-M09A-02)
        {"status": "granted", "submitted_on": date(2027, 2, 1), "amount_requested_cents": 1},
        {
            "status": "justified",  # sense data d'enviament (RN-M09A-12)
            "submitted_on": date(2027, 2, 1),
            "submission_ref": "RE-1",
            "amount_requested_cents": 300000,
        },
    ],
)
def test_restriccions_de_la_sollicitud(treasurer, extra):
    call = new_call(treasurer)
    rejects(lambda: new_application(call, treasurer, **extra))


def test_presentada_amb_les_dades_s_accepta(treasurer):
    application = new_application(
        new_call(treasurer),
        treasurer,
        status="submitted",
        submitted_on=date(2027, 2, 1),
        submission_ref="RE-2027-001",
        amount_requested_cents=300000,
    )
    assert application.status == "submitted"


def test_documents_de_la_sollicitud_unics(treasurer):
    application = new_application(new_call(treasurer), treasurer)
    document = ApplicationDocument.objects.create(application=application, name="Pressupost")
    assert (document.ready, str(document)) == (False, "Pressupost")
    rejects(lambda: ApplicationDocument.objects.create(application=application, name="Pressupost"))


def test_les_transicions_nomes_s_afegeixen(treasurer):
    application = new_application(new_call(treasurer), treasurer)
    transition = ApplicationTransition.objects.create(
        application=application, from_status="detected", to_status="preparing", actor=treasurer
    )
    with pytest.raises(AppendOnlyError):
        transition.save()
    with pytest.raises(AppendOnlyError):
        ApplicationTransition.objects.filter(pk=transition.pk).update(reason="canviat")
