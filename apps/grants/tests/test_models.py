"""T-M09A-02a: restriccions de la convocatòria (M09-ajuts-6). Només dades inventades."""

from datetime import date

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.grants.models import GrantCall, GrantCallDocument

pytestmark = pytest.mark.django_db


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


def new_call(by, **extra):
    return GrantCall.objects.create(
        **{"body": "Diputació Inventada", "name": "Medi marí", "created_by": by, **extra}
    )


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
