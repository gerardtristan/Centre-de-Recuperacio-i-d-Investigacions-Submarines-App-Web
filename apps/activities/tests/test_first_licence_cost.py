"""Cost previst de la primera llicència inclosa (T-M02-51b; RN-M02-59; CA-M02-60). Només dades
inventades."""

import pytest

from apps.activities import catalogue, filings
from apps.core import business_settings
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses.models import ExpenseCategory
from apps.margins.models import PlannedCost
from apps.margins.services import activity_margin

from .test_certificates import course  # noqa: F401 (fixture)
from .test_first_licence_02 import choose, includes, licence_type  # noqa: F401 (fixture)
from .test_first_star import pass_and_issue, with_official_level

pytestmark = pytest.mark.django_db


def test_ca_m02_60_two_licences_add_8000(course, licence_type, make_admin):  # noqa: F811
    category = ExpenseCategory.objects.create(name="Llicències federatives (inventat)")
    business_settings.change(
        catalogue.LICENCE_CATEGORY_KEY, category.name, make_admin(Role.Code.TREASURER),
        note="Categoria inventada.",
    )  # fmt: skip
    with_official_level(course)
    includes(course)
    choose(licence_type, make_admin)
    before = activity_margin(course.activity).margin_cents
    pass_and_issue(course, course.student)
    pass_and_issue(course, course.mate)
    planned = PlannedCost.objects.get(activity=course.activity, category=category)
    assert planned.amount_cents == 8000
    assert activity_margin(course.activity).margin_cents == before - 8000


def test_without_vc_60_nothing_is_planned_and_the_list_warns(course, licence_type, make_admin):  # noqa: F811
    with_official_level(course)
    includes(course)
    choose(licence_type, make_admin)
    pass_and_issue(course, course.student)
    assert not PlannedCost.objects.exists()
    (row,) = filings.course_pending(by=make_admin(Role.Code.SECRETARY))
    assert row["cost_not_planned"]
