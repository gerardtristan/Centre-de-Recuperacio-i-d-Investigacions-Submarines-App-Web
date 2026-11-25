"""Resultats ambientals i fitxa de projecte (T-M02-20; P-M02-G; AC14; RN-M02-23; CA-M02-21).
Portat de la branca aparcada (part de servei). Les fotos (CA-M02-22) encara no existeixen: vegeu
`apps/activities/environment.py`. Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities import catalogue, environment
from apps.activities.models import Activity, EnvironmentalResult, EnvironmentalSubtype, OutingType
from apps.core.models import AuditEntry
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_course, an_outing, general, moment

pytestmark = pytest.mark.django_db
S = Activity.Status


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")


@pytest.fixture
def project(manager):
    return catalogue.create_project(
        by=manager, name="Projecte inventat", objective="Objectiu inventat.", department=general()
    )


def env_outing(manager, project=None, status=S.DONE, **fields):
    outing = an_outing(
        manager, outing_type=OutingType.objects.get(name="Medi ambient"),
        subtype=EnvironmentalSubtype.objects.get(name="Neteja"), project=project, **fields,
    )  # fmt: skip
    reason = "Motiu inventat" if status == S.CANCELLED else ""
    Activity.objects.filter(pk=outing.pk).update(status=status, cancellation_reason=reason)
    outing.refresh_from_db()
    return outing


@pytest.mark.parametrize(("grams", "shown"), [(None, ""), (0, "0 kg"), (12500, "12,5 kg"),
                                              (24750, "24,75 kg"), (1, "0,001 kg")])  # fmt: skip
def test_grams_are_shown_as_kilos(grams, shown):
    assert environment.kilos(grams) == shown


def test_species_are_stored_one_per_line_without_blanks_or_repeats():
    text = "  Posidònia oceànica \n\nNacra\nposidònia   oceànica\nPop roquer\n"
    assert environment.clean_species(text) == "Posidònia oceànica\nNacra\nPop roquer"
    assert environment.clean_species(None) == ""


def test_results_are_recorded_after_the_outing_and_can_be_corrected(manager, make_admin):  # noqa: F811
    outing = env_outing(manager)
    when = moment(2027, 6, 16, 10)
    first = environment.record_results(
        outing, by=manager, waste_grams=12500, species="Nacra\nNacra\nPop roquer",
        observations="  Molt plàstic a la platja (observació inventada).  ", now=when,
    )  # fmt: skip
    assert (first.waste_grams, first.species) == (12500, "Nacra\nPop roquer")
    assert first.observations == "Molt plàstic a la platja (observació inventada)."
    assert (first.recorded_by, first.recorded_at) == (manager, when)
    created = AuditEntry.objects.get(action=environment.RESULTS_RECORDED)
    assert (created.actor_account, created.details["waste_grams"]) == (manager, 12500)

    president = make_admin("president")
    again = environment.record_results(outing, by=president, waste_grams=13000, species="Nacra")
    assert again.pk == first.pk and EnvironmentalResult.objects.count() == 1
    assert (again.waste_grams, again.recorded_by) == (13000, president)
    changes = {
        e.field: (e.old_value, e.new_value)
        for e in AuditEntry.objects.filter(action=environment.RESULTS_UPDATED)
    }
    assert changes["waste_grams"] == (12500, 13000)
    assert set(changes) == {"waste_grams", "species", "observations"}
    before = AuditEntry.objects.count()
    environment.record_results(outing, by=manager, waste_grams=13000, species="Nacra")
    assert AuditEntry.objects.count() == before  # sense canvis, res al registre
    assert environment.results_for(outing).recorded_by == president


def test_the_weight_is_optional(manager):
    result = environment.record_results(env_outing(manager), by=manager, species="Nacra")
    assert result.waste_grams is None


@pytest.mark.parametrize("status", [S.DRAFT, S.OPEN, S.REGISTRATION_CLOSED, S.CANCELLED])
def test_results_wait_until_the_outing_is_done(manager, status):
    outing = env_outing(manager, status=status)
    assert not environment.can_record(outing)
    with pytest.raises(ValidationError):
        environment.record_results(outing, by=manager, waste_grams=1000)
    assert not EnvironmentalResult.objects.exists()


def test_only_environmental_outings_have_results(manager):
    for activity in (an_outing(manager), a_course(manager)):
        Activity.objects.filter(pk=activity.pk).update(status=S.DONE)
        assert not environment.is_environmental(activity)
        with pytest.raises(ValidationError):
            environment.record_results(activity, by=manager, waste_grams=1000)


@pytest.mark.parametrize("wrong", [
    {"waste_grams": -1}, {"waste_grams": 12.5}, {"waste_grams": True},
    {"waste_grams": environment.MAX_GRAMS + 1}, {"species": "x" * 2001},
    {"observations": "x" * 2001},
])  # fmt: skip
def test_wrong_results_are_rejected(manager, wrong):
    with pytest.raises(ValidationError):
        environment.record_results(env_outing(manager), by=manager, **wrong)
    assert not EnvironmentalResult.objects.exists()


@pytest.mark.parametrize(("role", "records"), [
    ("courses_manager", True), ("administrator", True), ("president", True), ("board", False),
    ("treasurer", False), ("secretary", False), ("instructor", False),
])  # fmt: skip
def test_ac14_who_records(manager, make_admin, role, records):  # noqa: F811
    outing, account = env_outing(manager), make_admin(role)
    if records:
        environment.record_results(outing, by=account, waste_grams=1000)
    else:
        with pytest.raises(Http404):
            environment.record_results(outing, by=account, waste_grams=1000)
        assert not EnvironmentalResult.objects.exists()


def test_ca_m02_21_the_project_adds_up_the_waste_of_its_outings(manager, project):
    """Tres sortides d'un projecte amb 12,5 kg, 8 kg i 4,25 kg: el total és 24,75 kg."""
    for index, grams in enumerate((12500, 8000, 4250)):
        outing = env_outing(manager, project, title=f"Neteja inventada {index + 1}")
        environment.record_results(outing, by=manager, waste_grams=grams,
                                   species="Nacra\nPop roquer")  # fmt: skip
    pending = env_outing(manager, project, title="Neteja inventada sense resultats")
    other = env_outing(manager, title="Neteja inventada d'un altre lloc")  # sense projecte
    environment.record_results(other, by=manager, waste_grams=99000, species="Espècie d'un altre")
    summary = environment.project_summary(project)
    assert (summary.total_grams, summary.total_kilos) == (24750, "24,75 kg")
    assert (len(summary.outings), summary.with_results) == (4, 3)
    assert summary.species == ("Nacra", "Pop roquer")
    assert pending in [activity for activity, _result in summary.outings]


def test_a_project_without_outings_adds_up_to_zero(project):
    summary = environment.project_summary(project)
    assert (summary.total_grams, summary.total_kilos, summary.outings, summary.species) == (
        0, "0 kg", (), (),
    )  # fmt: skip


def test_no_photos_without_results(manager):
    from apps.activities import environment_photos

    assert not environment_photos.photos_for(env_outing(manager)).exists()
