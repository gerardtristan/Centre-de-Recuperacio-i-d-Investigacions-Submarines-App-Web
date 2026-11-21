"""T-M09A-15: requeriments d'esmena, canvi de data límit, pròrroga i despeses lligades d'una
justificada amb un requeriment obert (RN-M09A-19 a 22; CA-M09A-17, 21, 22 i 25). Només dades
inventades."""

from datetime import date

import pytest
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.core.models import AuditEntry
from apps.grants import justification as j
from apps.grants import requirements as r
from apps.grants.models import GrantApplication, GrantExpenseLink, GrantRequirement
from apps.grants.tests.test_justification import expense, granted  # noqa: F401 (fixture)
from apps.grants.tests.test_resolution import submitted  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db
D = date(2027, 10, 15)


def record(application, by, **extra):
    fields = {
        "origin": "body",
        "received_on": date(2027, 10, 1),
        "due_on": D,
        "description": "Cal la factura original de l'embarcació",
        "responsible": by.person,
        "by": by,
    }
    return r.record_requirement(application, **{**fields, **extra})


def test_ca_m09a_17_la_sollicitud_continua_concedida(granted, treasurer):  # noqa: F811
    requirement = record(granted, treasurer)
    granted.refresh_from_db()
    assert granted.status == "granted"
    assert (requirement.due_on, requirement.answered_on, str(requirement)) == (
        D,
        None,
        f"{granted.pk}: {D}",
    )
    assert AuditEntry.objects.filter(action=r.REQUIREMENT_RECORDED).count() == 1


def test_ca_m09a_25_un_requeriment_del_club_porta_motiu(granted, treasurer):  # noqa: F811
    with pytest.raises(r.MissingReason):
        record(granted, treasurer, origin="club")
    requirement = record(granted, treasurer, origin="club", origin_reason="Comprovant il·legible")
    assert requirement.origin_reason == "Comprovant il·legible"


@pytest.mark.parametrize(
    "extra",
    [
        {"origin": "bank"},
        {"description": " "},
        {"due_on": date(2027, 9, 30)},
        {"received_on": None},
        {"due_on": "demà"},
    ],
)
def test_requeriment_que_no_val(granted, treasurer, extra):  # noqa: F811
    with pytest.raises(r.GrantError):
        record(granted, treasurer, **extra)


def test_un_requeriment_arriba_quan_ja_s_ha_presentat(call, treasurer, general):
    from apps.grants import services

    detected = services.create_application(
        call, responsible=treasurer.person, department=general, by=treasurer
    )
    with pytest.raises(r.GrantError):
        record(detected, treasurer)


def test_ca_m09a_22_canviar_la_data_limit_demana_motiu_i_queda_al_registre(granted, treasurer):  # noqa: F811
    requirement = record(granted, treasurer)
    with pytest.raises(r.MissingReason):
        r.change_requirement_due_on(
            requirement, due_on=date(2027, 10, 25), reason=" ", by=treasurer
        )
    with pytest.raises(r.InvalidDates):
        r.change_requirement_due_on(
            requirement, due_on=date(2027, 9, 1), reason="Error", by=treasurer
        )
    changed = r.change_requirement_due_on(
        requirement, due_on=date(2027, 10, 25), reason="Pròrroga de l'organisme", by=treasurer
    )
    assert changed.due_on == date(2027, 10, 25)
    entry = AuditEntry.objects.get(action=r.REQUIREMENT_DUE_CHANGED)
    assert (entry.old_value, entry.new_value, entry.reason) == (
        "2027-10-15",
        "2027-10-25",
        "Pròrroga de l'organisme",
    )


def test_respondre_tanca_el_requeriment(granted, treasurer):  # noqa: F811
    requirement = record(granted, treasurer)
    with pytest.raises(r.InvalidDates):
        r.answer_requirement(requirement, answered_on=date(2027, 9, 1), by=treasurer)
    r.answer_requirement(requirement, answered_on=date(2027, 10, 10), by=treasurer)
    with pytest.raises(r.RequirementNotOpen):
        r.answer_requirement(requirement, answered_on=date(2027, 10, 11), by=treasurer)
    with pytest.raises(r.RequirementNotOpen):
        r.change_requirement_due_on(requirement, due_on=D, reason="Tard", by=treasurer)


def test_ca_m09a_19_proroga_amb_motiu_al_registre(granted, treasurer):  # noqa: F811
    with pytest.raises(r.MissingReason):
        r.set_justification_extension(
            granted, extended_to=date(2028, 2, 1), reason="", by=treasurer
        )
    extended = r.set_justification_extension(
        granted, extended_to=date(2028, 2, 1), reason="L'organisme ho permet", by=treasurer
    )
    assert extended.justification_extended_to == date(2028, 2, 1)
    r.set_justification_extension(
        granted, extended_to=date(2028, 3, 1), reason="Una altra", by=treasurer
    )
    entries = AuditEntry.objects.filter(action=r.EXTENSION_SET).order_by("pk")
    assert [(e.old_value, e.new_value) for e in entries] == [
        (None, "2028-02-01"),
        ("2028-02-01", "2028-03-01"),
    ]


def test_ca_m09a_21_una_justificada_nomes_canvia_amb_un_requeriment_obert(granted, treasurer):  # noqa: F811
    first = j.link_expense(granted, expense(treasurer), 1000, by=treasurer)
    GrantApplication.objects.filter(pk=granted.pk).update(status="justified", justified_on=D)
    requirement = record(granted, treasurer)

    removed = j.unlink_expense(first, by=treasurer, requirement=requirement)
    added = j.link_expense(
        granted, expense(treasurer, number="F-2"), 2000, by=treasurer, requirement=requirement
    )
    assert (removed.removed_requirement, added.requirement) == (requirement, requirement)

    r.answer_requirement(requirement, answered_on=date(2027, 10, 10), by=treasurer)
    with pytest.raises(r.RequirementNotOpen):
        j.link_expense(
            granted, expense(treasurer, number="F-3"), 1, by=treasurer, requirement=requirement
        )
    with pytest.raises(j.AlreadyJustified):
        j.link_expense(granted, expense(treasurer, number="F-4"), 1, by=treasurer)
    assert GrantExpenseLink.objects.count() == 2


def test_un_requeriment_d_una_altra_sollicitud_no_val(granted, treasurer, call, general):  # noqa: F811
    other = GrantApplication.objects.create(
        call=call,
        responsible=treasurer.person,
        department=general,
        created_by=treasurer,
        status="granted",
        submitted_on=date(2027, 2, 1),
        submission_ref="RE-9",
        amount_requested_cents=1,
    )
    foreign = record(other, treasurer)
    with pytest.raises(r.RequirementNotOpen):
        j.link_expense(granted, expense(treasurer), 1, by=treasurer, requirement=foreign)


def test_aj13_i_la_junta_nomes_les_seves(granted, treasurer, make_admin):  # noqa: F811
    with pytest.raises(Http404):
        record(granted, make_admin("secretary"))
    with pytest.raises(Http404):
        record(granted, make_admin("board"))  # no n'és responsable


def test_restriccions_de_la_base_de_dades(granted, treasurer):  # noqa: F811
    with pytest.raises(IntegrityError), transaction.atomic():
        GrantRequirement.objects.create(application=granted, origin="club", received_on=D,
                                        due_on=D, description="x", responsible=treasurer.person,
                                        created_by=treasurer)  # fmt: skip
    with pytest.raises(IntegrityError), transaction.atomic():
        GrantRequirement.objects.create(
            application=granted,
            origin="body",
            received_on=D,
            due_on=date(2027, 1, 1),
            description="x",
            responsible=treasurer.person,
            created_by=treasurer,
        )
