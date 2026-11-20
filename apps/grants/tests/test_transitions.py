"""T-M09A-04: transicions d'estat, documents i desfer de l'administrador (RN-M09A-01, 02 i 05;
CA-M09A-04, 05 i 06). Només dades inventades."""

from datetime import date

import pytest
from django.http import Http404

from apps.core.models import AuditEntry
from apps.grants import services
from apps.grants.models import GrantApplication

pytestmark = pytest.mark.django_db
S = GrantApplication.Status
SUBMISSION = {
    "submitted_on": date(2027, 2, 1),
    "submission_ref": "RE-2027-001",
    "amount_requested_cents": 300000,
}


@pytest.fixture
def application(call, treasurer, general):
    return services.create_application(
        call, responsible=treasurer.person, department=general, by=treasurer
    )


def eligible(call, by):
    services.review_eligibility(call, status="eligible", notes="Complim els requisits", by=by)


def ready_all(application, by):
    for document in application.documents.all():
        services.set_document_ready(document, ready=True, by=by)


def prepared(application, call, by):
    eligible(call, by)
    return services.transition(application, S.PREPARING, by=by)


def test_ca_m09a_04_sense_revisio_no_passa_a_en_preparacio(application, treasurer):
    with pytest.raises(services.EligibilityNotReviewed):
        services.transition(application, S.PREPARING, by=treasurer)
    application.refresh_from_db()
    assert application.status == S.DETECTED


def test_amb_l_elegibilitat_revisada_passa_a_en_preparacio(application, call, treasurer):
    moved = prepared(application, call, treasurer)
    assert moved.status == S.PREPARING
    entry = AuditEntry.objects.get(action=services.APPLICATION_TRANSITIONED)
    assert (entry.old_value, entry.new_value) == ("detected", "preparing")


def test_una_convocatoria_no_elegible_no_es_prepara(application, call, treasurer):
    call.eligibility_status = "not_eligible"  # en memòria: la revisió ja l'hauria tancada
    call.eligibility_reviewed_by, call.eligibility_notes = treasurer, "No"
    call.eligibility_reviewed_at = application.created_at
    call.save()
    with pytest.raises(services.InvalidTransition):
        services.transition(application, S.PREPARING, by=treasurer)


def test_ca_m09a_05_falten_documents_i_es_diu_quins(application, call, treasurer):
    prepared(application, call, treasurer)
    services.set_document_ready(application.documents.first(), ready=True, by=treasurer)
    with pytest.raises(services.MissingDocuments, match="Pressupost"):
        services.transition(application, S.SUBMITTED, by=treasurer, **SUBMISSION)


def test_presentada_amb_les_dades_i_la_resposta_prevista(application, call, treasurer):
    prepared(application, call, treasurer)
    ready_all(application, treasurer)
    moved = services.transition(application, S.SUBMITTED, by=treasurer, **SUBMISSION)
    assert (moved.status, moved.submission_ref) == (S.SUBMITTED, "RE-2027-001")
    assert moved.expected_response_on == date(2027, 5, 2)  # P + 90 (CA-M09A-03)


def test_sense_termini_publicat_la_resposta_prevista_l_escriu_el_responsable(
    application, call, treasurer
):
    call.max_resolution_days = None
    call.save()
    prepared(application, call, treasurer)
    ready_all(application, treasurer)
    moved = services.transition(
        application,
        S.SUBMITTED,
        by=treasurer,
        expected_response_on=date(2027, 4, 1),
        **SUBMISSION,
    )
    assert moved.expected_response_on == date(2027, 4, 1)


@pytest.mark.parametrize(
    "data",
    [
        {**SUBMISSION, "submitted_on": None},
        {**SUBMISSION, "submission_ref": " "},
        {**SUBMISSION, "submission_ref": "x" * 61},
        {**SUBMISSION, "amount_requested_cents": 0},
        {**SUBMISSION, "amount_requested_cents": True},
        {**SUBMISSION, "expected_response_on": "demà"},
    ],
)
def test_presentar_sense_les_dades_es_rebutja(application, call, treasurer, data):
    call.max_resolution_days = None
    call.save()
    prepared(application, call, treasurer)
    ready_all(application, treasurer)
    with pytest.raises(services.GrantError):
        services.transition(application, S.SUBMITTED, by=treasurer, **data)


def test_ca_m09a_06_de_presentada_a_justificada_no_es_permes(application, call, treasurer):
    prepared(application, call, treasurer)
    ready_all(application, treasurer)
    services.transition(application, S.SUBMITTED, by=treasurer, **SUBMISSION)
    with pytest.raises(services.InvalidTransition):
        services.transition(application, S.JUSTIFIED, by=treasurer, justified_on=date(2027, 9, 1))


def test_tancar_sense_presentar_demana_el_motiu(application, treasurer):
    with pytest.raises(services.GrantError):
        services.transition(application, S.CLOSED, by=treasurer)
    moved = services.transition(application, S.CLOSED, by=treasurer, reason="No es presenta")
    assert (moved.status, moved.closed_reason) == (S.CLOSED, "No es presenta")
    with pytest.raises(services.InvalidTransition):
        services.transition(application, S.PREPARING, by=treasurer)


def test_tancar_una_justificada_demana_aj8(application, treasurer, make_admin):
    GrantApplication.objects.filter(pk=application.pk).update(
        status=S.JUSTIFIED, justified_on=date(2027, 9, 1), **SUBMISSION
    )  # justificar és de la T-M09A-10
    with pytest.raises(Http404):
        services.transition(application, S.CLOSED, by=make_admin("board"))
    assert services.transition(application, S.CLOSED, by=treasurer).status == S.CLOSED


def test_la_junta_nomes_mou_les_seves(application, call, treasurer, make_admin, general):
    eligible(call, treasurer)
    board = make_admin("board")
    with pytest.raises(Http404):
        services.transition(application, S.PREPARING, by=board)
    own = services.create_application(call, responsible=board.person, department=general, by=board)
    assert services.transition(own, S.PREPARING, by=board).status == S.PREPARING


def test_l_administrador_desfa_l_ultima_transicio_amb_motiu(
    application, call, treasurer, make_admin
):
    prepared(application, call, treasurer)
    admin = make_admin("administrator")
    with pytest.raises(Http404):
        services.undo_last_transition(application, reason="Error", by=treasurer)
    with pytest.raises(services.GrantError):
        services.undo_last_transition(application, reason=" ", by=admin)

    undone = services.undo_last_transition(application, reason="Massa d'hora", by=admin)

    assert undone.status == S.DETECTED
    last = undone.transitions.order_by("pk").last()
    assert (last.from_status, last.to_status, last.reason) == (
        "preparing",
        "detected",
        "Massa d'hora",
    )
    assert undone.transitions.count() == 2  # el desfer és una transició nova


def test_sense_transicions_no_hi_ha_res_per_desfer(application, make_admin):
    with pytest.raises(services.InvalidTransition):
        services.undo_last_transition(application, reason="Res", by=make_admin("administrator"))


def test_documents_marcar_afegir_i_registre(application, treasurer):
    document = services.set_document_ready(application.documents.first(), ready=True, by=treasurer)
    assert (document.ready, document.uploaded_by) == (True, treasurer)
    extra = services.add_document(application, name="Certificat de la Hisenda", by=treasurer)
    assert extra.name == "Certificat de la Hisenda"
    assert AuditEntry.objects.filter(action=services.DOCUMENT_CHANGED).count() == 2
    for name in ("Pressupost", " ", "x" * 201):
        with pytest.raises(services.GrantError):
            services.add_document(application, name=name, by=treasurer)


def test_els_documents_no_canvien_un_cop_presentada(application, call, treasurer):
    prepared(application, call, treasurer)
    ready_all(application, treasurer)
    services.transition(application, S.SUBMITTED, by=treasurer, **SUBMISSION)
    with pytest.raises(services.GrantError):
        services.set_document_ready(application.documents.first(), ready=False, by=treasurer)
    with pytest.raises(services.GrantError):
        services.add_document(application, name="Un altre", by=treasurer)


@pytest.mark.parametrize("role", ["secretary", "president", None])
def test_sense_aj4_no_es_toquen_els_documents(application, make_admin, role):
    other = make_admin(*([role] if role else []))
    with pytest.raises(Http404):
        services.set_document_ready(application.documents.first(), ready=True, by=other)
    with pytest.raises(Http404):
        services.add_document(application, name="Un altre", by=other)


def test_sense_termini_ni_data_no_hi_ha_resposta_prevista(application, call, treasurer):
    call.max_resolution_days = None
    call.save()
    prepared(application, call, treasurer)
    ready_all(application, treasurer)
    moved = services.transition(application, S.SUBMITTED, by=treasurer, **SUBMISSION)
    assert moved.expected_response_on is None  # RN-M09A-05: cap avís
