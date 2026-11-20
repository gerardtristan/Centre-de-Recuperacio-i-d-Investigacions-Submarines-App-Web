"""T-M09A-03: sol·licitud detectada i elegibilitat revisada per una persona (RN-M09A-03,
CA-M09A-04). Només dades inventades."""

import pytest
from django.http import Http404

from apps.core.models import AuditEntry, Department
from apps.grants import services
from apps.grants.models import GrantApplication
from apps.treasury.models import CostCentre

pytestmark = pytest.mark.django_db
S = GrantApplication.Status


def new(call, by, **extra):
    return services.create_application(
        call,
        **{
            "responsible": by.person,
            "department": Department.objects.get(name="General"),
            "by": by,
            **extra,
        },  # fmt: skip
    )


def test_la_sollicitud_neix_detectada_amb_els_documents_de_la_convocatoria(call, treasurer):
    application = new(call, treasurer, amount_requested_cents=300000)
    assert application.status == S.DETECTED
    assert [d.name for d in application.documents.all()] == ["Memòria del projecte", "Pressupost"]
    assert not any(d.ready for d in application.documents.all())
    assert AuditEntry.objects.filter(action=services.APPLICATION_CREATED).count() == 1


def test_el_responsable_ha_de_tenir_un_rol_dels_ajuts(call, treasurer, make_admin):
    secretary = make_admin("secretary")
    with pytest.raises(services.GrantError):
        new(call, treasurer, responsible=secretary.person)
    board = make_admin("board")
    assert new(call, treasurer, responsible=board.person).responsible == board.person


@pytest.mark.parametrize("extra", [{"amount_requested_cents": -1}, {"amount_requested_cents": 1.5}])
def test_import_no_valid(call, treasurer, extra):
    with pytest.raises(services.GrantError):
        new(call, treasurer, **extra)


def test_departament_i_centre_de_cost(call, treasurer, general):
    centre = CostCentre.selectable().filter(department=general).first()
    assert new(call, treasurer, cost_centre=centre).cost_centre == centre
    other = Department.objects.create(name="Medi ambient")
    with pytest.raises(services.GrantError):
        new(call, treasurer, department=other, cost_centre=centre)


def test_la_junta_nomes_crea_les_que_en_sera_responsable(call, treasurer, make_admin):
    board = make_admin("board")
    assert new(call, board).responsible == board.person
    with pytest.raises(Http404):
        new(call, board, responsible=treasurer.person)


@pytest.mark.parametrize("role", ["secretary", "president", "courses_manager", None])
def test_sense_aj4_no_es_crea(call, treasurer, make_admin, role):
    with pytest.raises(Http404):
        new(call, make_admin(*([role] if role else [])), responsible=treasurer.person)


def test_una_persona_revisa_l_elegibilitat_amb_notes_i_queda_al_registre(call, treasurer):
    services.review_eligibility(
        call, status="eligible", notes="Complim els requisits", by=treasurer
    )
    call.refresh_from_db()
    assert (call.eligibility_status, call.eligibility_reviewed_by) == ("eligible", treasurer)
    entry = AuditEntry.objects.get(action=services.ELIGIBILITY_REVIEWED)
    assert (entry.old_value, entry.new_value, entry.reason) == (
        "pending",
        "eligible",
        "Complim els requisits",
    )


@pytest.mark.parametrize(
    ("status", "notes"), [("pending", "Encara no"), ("maybe", "Potser"), ("eligible", "  ")]
)
def test_revisio_no_valida(call, treasurer, status, notes):
    with pytest.raises(services.GrantError):
        services.review_eligibility(call, status=status, notes=notes, by=treasurer)
    call.refresh_from_db()
    assert call.eligibility_status == "pending"


def test_no_elegible_tanca_les_detectades_amb_el_motiu(call, treasurer):
    open_one = new(call, treasurer)
    services.review_eligibility(
        call, status="not_eligible", notes="Només clubs federats", by=treasurer
    )
    open_one.refresh_from_db()
    assert open_one.status == S.CLOSED
    assert open_one.closed_reason == "No elegible: Només clubs federats"
    transition = open_one.transitions.get()
    assert (transition.from_status, transition.to_status) == ("detected", "closed")


@pytest.mark.parametrize("role", ["secretary", "president", None])
def test_sense_aj2_no_es_revisa(call, make_admin, role):
    with pytest.raises(Http404):
        services.review_eligibility(
            call, status="eligible", notes="Sí", by=make_admin(*([role] if role else []))
        )


def test_la_junta_revisa_l_elegibilitat(call, make_admin):
    board = make_admin("board")
    assert services.review_eligibility(call, status="eligible", notes="Sí", by=board).pk == call.pk
