"""T-M03-15: bloc de material a «Les meves activitats» i a la fitxa de l'activitat (C10, MT2 i MT7;
RN-M02-45). Només dades inventades."""

import pytest
from django.template.loader import render_to_string

from apps.activities import extensions
from apps.activities.tests.test_attendance import a_session, enrolled
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, detail, handover

from .test_assignments import JUNE, jacket, keeper, kind, manager, outing  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
PERSONAL, ADMIN = extensions.PLACE_PERSONAL, extensions.PLACE_ADMIN


@pytest.fixture
def activity_with_material(manager, keeper):  # noqa: F811
    activity = outing(manager)
    ana, bru = enrolled(activity, "Ana"), enrolled(activity, "Bru")
    handover.deliver(assignments.assign_club(ana, jacket(keeper, "S"), by=keeper), by=keeper)
    assignments.assign_own(ana, kind("Aletes"), by=keeper)
    cancelled = assignments.assign_club(bru, jacket(keeper, "XL"), by=keeper)
    handover.cancel(cancelled, by=keeper, reason="Ja no el necessita (inventat).")
    assignments.assign_club(bru, jacket(keeper, "L"), by=keeper)
    return activity, ana.person, bru.person


def test_c10_the_participant_sees_only_their_own_material(activity_with_material):
    activity, ana, bru = activity_with_material
    context = detail.section_context(activity, place=PERSONAL, person=ana)
    assert [(r.equipment_type.name, r.origin) for r in context["rows"]] == [
        ("Aletes", "own"),
        ("Jaquet", "club"),
    ]
    assert context["with_people"] is False
    html = render_to_string(detail.SECTION.template_name, context)
    assert "El teu material" in html and "Lliurada" in html
    assert "Bru" not in html and "Ana" not in html
    assert "€" not in html  # cap cost ni preu (RN-M02-45)
    # Les assignacions cancel·lades no surten.
    rows = detail.section_context(activity, place=PERSONAL, person=bru)["rows"]
    assert [r.item.size for r in rows] == ["L"]


def test_without_a_participant_or_material_the_personal_block_is_hidden(
    activity_with_material,
    manager,  # noqa: F811
):
    activity, ana, _ = activity_with_material
    assert detail.section_context(activity, place=PERSONAL) is None
    other = outing(manager, JUNE.replace(month=7))
    assert detail.section_context(other, place=PERSONAL, person=ana) is None


def test_mt7_staff_see_everyone_with_names_and_no_costs(activity_with_material, keeper):  # noqa: F811
    activity, *_ = activity_with_material
    context = detail.section_context(activity, place=ADMIN, viewer=keeper)
    assert len(context["rows"]) == 3 and context["with_people"] is True
    html = render_to_string(detail.SECTION.template_name, context)
    assert "Material dels participants" in html
    assert "Ana Prova" in html and "Bru Prova" in html
    assert "€" not in html


def test_mt7_by_object_the_instructor_only_on_their_sessions(
    activity_with_material,
    manager,  # noqa: F811
    make_admin,  # noqa: F811
):
    activity, *_ = activity_with_material
    teacher = make_admin(Role.Code.INSTRUCTOR)
    assert detail.section_context(activity, place=ADMIN, viewer=teacher) is None
    a_session(manager, activity, JUNE, teacher.person)
    assert len(detail.section_context(activity, place=ADMIN, viewer=teacher)["rows"]) == 3


def test_without_mt7_the_admin_block_is_hidden(activity_with_material, make_admin):  # noqa: F811
    activity, *_ = activity_with_material
    assert detail.section_context(activity, place=ADMIN, viewer=make_admin()) is None
    assert detail.section_context(activity, place=ADMIN) is None


def test_the_block_is_registered_in_the_02(activity_with_material, keeper):  # noqa: F811
    activity, ana, _ = activity_with_material
    shown = extensions.detail_sections(activity, place=ADMIN, viewer=keeper)
    assert [section.key for section, _ in shown] == [detail.SECTION_KEY]
    shown = extensions.detail_sections(activity, place=PERSONAL, person=ana)
    assert [section.key for section, _ in shown] == [detail.SECTION_KEY]
