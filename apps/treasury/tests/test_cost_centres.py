"""Centres de cost (T-M04-02; HU-T14; CA-T14.1 i CA-T14.2; RN-T22 i RN-T23)."""

from importlib import import_module

import pytest
from django.db import IntegrityError, migrations, transaction
from django.db.models import ProtectedError

from apps.core.models import Department, UndeletableError
from apps.treasury.models import CostCentre

pytestmark = pytest.mark.django_db


@pytest.fixture
def general():
    return Department.objects.get(name=Department.GENERAL)


@pytest.fixture
def courses():
    return Department.objects.create(name="Cursos")


def rejected(**fields):
    with pytest.raises(IntegrityError), transaction.atomic():
        CostCentre.objects.create(**fields)


class TestInitialCostCentres:
    def test_ca_t14_1_general_has_its_three_cost_centres_after_the_migrations(self, general):
        centres = CostCentre.objects.order_by("name")
        assert [c.name for c in centres] == ["Ajustos de caixa", "Llicències", "Quotes de socis"]
        assert all(c.department == general and c.active for c in centres)

    def test_ca_t14_1_full_name_shows_department_and_cost_centre(self):
        centre = CostCentre.objects.get(name="Quotes de socis")
        assert centre.full_name == "General / Quotes de socis"
        assert str(centre) == "General / Quotes de socis"

    def test_the_data_migration_can_be_undone(self):
        module = import_module("apps.treasury.migrations.0004_initial_cost_centres")
        assert all(
            isinstance(op, migrations.RunPython) and op.reverse_code is not None
            for op in module.Migration.operations
        )


class TestRules:
    def test_name_is_unique_inside_a_department(self, general, courses):
        rejected(department=general, name="Quotes de socis")
        assert CostCentre.objects.create(department=courses, name="Quotes de socis")

    def test_name_cannot_be_empty(self, general):
        rejected(department=general, name="")

    def test_a_cost_centre_is_deactivated_not_deleted(self):
        centre = CostCentre.objects.get(name="Llicències")
        with pytest.raises(UndeletableError):
            centre.delete()
        with pytest.raises(UndeletableError):
            CostCentre.objects.filter(pk=centre.pk).delete()

    def test_a_department_with_cost_centres_cannot_be_deleted(self, courses):
        CostCentre.objects.create(department=courses, name="Open Water")
        with pytest.raises(ProtectedError):
            courses.delete()


class TestSelectable:
    def test_ca_t14_2_a_deactivated_cost_centre_cannot_be_chosen(self):
        CostCentre.objects.filter(name="Llicències").update(active=False)
        names = {c.name for c in CostCentre.selectable()}
        assert names == {"Quotes de socis", "Ajustos de caixa"}

    def test_cost_centres_of_a_deactivated_department_cannot_be_chosen(self, courses):
        CostCentre.objects.create(department=courses, name="Open Water")
        assert CostCentre.selectable().filter(name="Open Water").exists()
        courses.active = False
        courses.save()
        assert not CostCentre.selectable().filter(name="Open Water").exists()

    def test_choosing_does_not_need_a_query_per_department(self, django_assert_num_queries):
        with django_assert_num_queries(1):
            assert [c.full_name for c in CostCentre.selectable()]
