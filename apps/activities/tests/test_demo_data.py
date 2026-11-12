"""Dades inventades del mòdul 02 (T-M02-25): es carreguen amb l'ordre `seed_demo_data`, només en
desenvolupament, i tot el que creen és inventat.

Els inscrits i les avaluacions no hi són: depenen de les inscripcions (T-M02-11).
"""

import pytest

from apps.accounts.models import Account
from apps.activities import demo_data, environment, public
from apps.activities.models import (
    Activity,
    CertificationLevel,
    EnvironmentalProject,
    EnvironmentalResult,
    Session,
    TrainingCatalogueEntry,
)
from apps.core.management.commands.seed_demo_data import ROLE_ACCOUNTS
from apps.core.models import AuditEntry, OutgoingEmail
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_seed_demo_data import DEV, cluber_path, run  # noqa: F401 (fixture)

from .helpers import client_for, general

pytestmark = pytest.mark.django_db

S = Activity.Status


@pytest.fixture
def created(make_admin):  # noqa: F811
    manager, instructor = make_admin("courses_manager"), make_admin("instructor")
    return demo_data.create(manager=manager, instructor=instructor, department=general())


def test_it_creates_a_catalogue_and_activities_in_every_state_that_exists(created):
    assert TrainingCatalogueEntry.objects.count() == created.entries == 3
    assert CertificationLevel.objects.count() == created.levels == 2
    assert Activity.objects.count() == created.activities == 4
    assert {a.status for a in Activity.objects.all()} == {S.DRAFT, S.OPEN, S.DONE, S.CANCELLED}
    assert EnvironmentalProject.objects.count() == 1
    # Un canvi de preu que encara ha d'entrar en vigor, per veure'l a la pantalla de preus.
    advanced = TrainingCatalogueEntry.objects.get(name="Curs de prova avançat")
    assert advanced.prices.count() == 2
    # El curs en esborrany té sessions amb l'instructor de prova.
    assert created.draft_course.sessions.count() == 2
    assert all(s.instructors.count() == 1 for s in Session.objects.all())
    # La sortida oberta té programa i requisits; la feta, resultats; la cancel·lada, motiu.
    assert created.open_outing.programme_blocks.count() == 4
    assert created.open_outing.min_level is not None
    assert created.open_outing.required_specialities.count() == 1
    result = EnvironmentalResult.objects.get()
    assert (result.activity, result.waste_grams) == (created.done_outing, 12500)
    assert created.cancelled_outing.cancellation_reason


def test_everything_is_invented_and_goes_through_the_services(created):
    """Cap nom real: tot porta «de prova» o «inventad». I el registre d'activitat queda com
    quedaria de debò, a nom del compte de prova."""
    for model in (TrainingCatalogueEntry, CertificationLevel, EnvironmentalProject):
        assert all("de prova" in obj.name.lower() for obj in model.objects.all()), model
    for activity in Activity.objects.all():
        assert "de prova" in activity.title.lower()
    assert AuditEntry.objects.filter(action="activities.activity.created").count() == 4
    assert not AuditEntry.objects.filter(
        action__startswith="activities.", actor_account__isnull=True, actor_kind="account"
    ).exists()
    # El canvi de preu de prova no envia cap correu: els comptes de prova no en tenen.
    assert not OutgoingEmail.objects.exists()


def test_the_public_list_shows_only_the_open_outing(created):
    listed = [activity.pk for activity in public.public_list()]
    assert listed == [created.open_outing.pk]
    summary = environment.project_summary(created.done_outing.project)
    assert summary.total_kilos == "12,5 kg"


def test_the_screens_render_with_the_demo_data(created, make_admin):  # noqa: F811
    client = client_for(make_admin("courses_manager"))
    for url in (
        "/gestio/activitats/",
        f"/gestio/activitats/{created.draft_course.pk}/",
        f"/gestio/activitats/{created.done_outing.pk}/resultats/",
        "/gestio/cataleg/cursos/",
        "/gestio/medi-ambient/",
    ):
        assert client.get(url).status_code == 200, url


@DEV
def test_t_m02_25_the_seed_command_loads_the_module_data(cluber_path):  # noqa: F811
    """«Es carreguen amb una ordre»: la mateixa de la resta de dades inventades, amb un compte de
    prova del responsable de cursos i sortides."""
    output = run(cluber_path=cluber_path)
    assert ("cursos-demo", "Cursos", "courses_manager") in [tuple(row) for row in ROLE_ACCOUNTS]
    manager = Account.objects.get(login="cursos-demo")
    assert manager.role_assignments.filter(role__code="courses_manager").exists()
    assert Activity.objects.count() == 4 and TrainingCatalogueEntry.objects.count() == 3
    assert Activity.objects.filter(responsible=manager.person).count() == 4
    assert "Mòdul 02: 3 fitxes del catàleg i 4 activitats" in output
    assert "cursos-demo" in output
