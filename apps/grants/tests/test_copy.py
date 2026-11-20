"""T-M09A-11: còpia de sol·licitud i de convocatòria (P-M09A-G; RN-M09A-14; CA-M09A-11). Només
dades inventades."""

from datetime import date

import pytest
from django.http import Http404

from apps.grants import services
from apps.grants.models import GrantApplication, GrantCall
from apps.grants.tests.test_resolution import deny, submitted  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db
S = GrantApplication.Status


def test_ca_m09a_11_la_copia_d_una_denegada_es_detectada_sense_fitxers_i_amb_observacions(
    submitted,  # noqa: F811
    call,
    treasurer,
):
    denied = deny(submitted, treasurer)
    next_call = services.copy_call(call, by=treasurer)

    copy = services.copy_application(denied, next_call, by=treasurer)

    assert (copy.status, copy.call, copy.copied_from) == (S.DETECTED, next_call, denied)
    assert (copy.department, copy.amount_requested_cents) == (denied.department, 300000)
    assert [(d.name, d.ready, d.file) for d in copy.documents.all()] == [
        ("Memòria del projecte", False, None),
        ("Pressupost", False, None),
    ]
    assert [n.improvements for n in services.denial_notes_for(copy)] == ["Presentar-la abans"]
    again = services.copy_application(copy, next_call, by=treasurer)  # dues generacions
    assert [n.reason for n in services.denial_notes_for(again)] == ["Fora de termini"]


def test_la_copia_de_la_convocatoria_ho_porta_tot_excepte_les_dates(call, treasurer):
    call.opens_on, call.closes_on = date(2027, 1, 1), date(2027, 3, 31)
    call.justification_due_on, call.edition_label = date(2027, 12, 1), "2027"
    call.eligibility_requirements, call.accepts_masked_proofs = "Ser un club federat", "no"
    call.save()
    services.review_eligibility(call, status="eligible", notes="Sí", by=treasurer)

    copy = services.copy_call(GrantCall.objects.get(pk=call.pk), by=treasurer)

    assert (copy.body, copy.name, copy.edition_label) == (call.body, call.name, "2027")
    assert (copy.eligibility_requirements, copy.accepts_masked_proofs) == (
        "Ser un club federat",
        "no",
    )
    assert (copy.opens_on, copy.closes_on, copy.justification_due_on) == (None, None, None)
    assert (copy.eligibility_status, copy.previous_edition) == ("pending", call)
    assert [d.name for d in copy.documents.all()] == ["Memòria del projecte", "Pressupost"]


def test_copiar_demana_aj1_i_aj4(call, treasurer, make_admin, general):
    secretary = make_admin("secretary")
    with pytest.raises(Http404):
        services.copy_call(call, by=secretary)
    application = services.create_application(
        call, responsible=treasurer.person, department=general, by=treasurer
    )
    with pytest.raises(Http404):
        services.copy_application(application, call, by=make_admin("board"))  # no és seva


def test_el_responsable_ha_de_continuar_tenint_el_rol(call, treasurer, make_admin, general):
    board = make_admin("board")
    application = services.create_application(
        call, responsible=board.person, department=general, by=treasurer
    )
    board.role_assignments.update(removed_at=application.created_at)  # deixa la junta
    with pytest.raises(services.GrantError):
        services.copy_application(application, call, by=treasurer)
