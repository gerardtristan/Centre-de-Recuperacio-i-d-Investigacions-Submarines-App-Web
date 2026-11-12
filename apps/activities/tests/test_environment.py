"""Resultats ambientals i fitxa de projecte (T-M02-20; P-M02-G; AC14; RN-M02-23; CA-M02-21).

Les fotos (CA-M02-22) no existeixen encara: vegeu `apps/activities/environment.py`. Només dades
inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import Client
from django.urls import reverse

from apps.activities import catalogue, environment, states
from apps.activities.forms import KilosField
from apps.activities.models import (
    Activity,
    EnvironmentalResult,
    EnvironmentalSubtype,
    OutingType,
)
from apps.core.models import AuditEntry
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import BEFORE_DEADLINE, a_course, an_outing, at, client_for, general

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
        manager,
        outing_type=OutingType.objects.get(name="Medi ambient"),
        subtype=EnvironmentalSubtype.objects.get(name="Neteja"),
        project=project,
        **fields,
    )
    reason = "Motiu inventat" if status == S.CANCELLED else ""
    Activity.objects.filter(pk=outing.pk).update(status=status, cancellation_reason=reason)
    outing.refresh_from_db()
    return outing


# --- Quilos i espècies ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("written", "grams"),
    [("12,5", 12500), ("8", 8000), ("4.25", 4250), ("0", 0), (" 1,005 kg ", 1005)],
)
def test_kilos_are_written_with_decimals_and_stored_in_grams(written, grams):
    assert KilosField().clean(written) == grams


@pytest.mark.parametrize("written", ["-1", "dotze", "1,2345", "1,2,3"])
def test_wrong_weights_are_rejected(written):
    with pytest.raises(ValidationError):
        KilosField().clean(written)


def test_grams_are_shown_as_kilos():
    assert environment.kilos(24750) == "24,75 kg"
    assert environment.kilos(8000) == "8 kg"
    assert environment.kilos(1005) == "1,005 kg"
    assert environment.kilos(0) == "0 kg"
    assert environment.kilos(None) == ""
    assert KilosField().prepare_value(12500) == "12,5"
    assert KilosField(required=False).clean("") is None


def test_species_are_stored_one_per_line_without_blanks_or_repeats():
    text = "  Posidònia oceànica \n\nNacra\nposidònia   oceànica\nPop roquer\n"
    assert environment.clean_species(text) == "Posidònia oceànica\nNacra\nPop roquer"
    assert environment.clean_species(None) == ""


# --- Registrar els resultats ----------------------------------------------------------------------


def test_results_are_recorded_after_the_outing_and_can_be_corrected(manager, make_admin):  # noqa: F811
    outing = env_outing(manager)
    first = environment.record_results(
        outing,
        by=manager,
        waste_grams=12500,
        species="Nacra\nNacra\nPop roquer",
        observations="  Molt plàstic a la platja (observació inventada).  ",
        now=at(2027, 6, 16, 10),
    )
    assert (first.waste_grams, first.species) == (12500, "Nacra\nPop roquer")
    assert first.observations == "Molt plàstic a la platja (observació inventada)."
    assert (first.recorded_by, first.recorded_at) == (manager, at(2027, 6, 16, 10))
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
    # Sense canvis, no queda res al registre ni canvia qui els ha registrat.
    before = AuditEntry.objects.count()
    environment.record_results(outing, by=manager, waste_grams=13000, species="Nacra")
    assert AuditEntry.objects.count() == before
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
    dive = an_outing(manager)
    course = a_course(manager)
    for activity in (dive, course):
        Activity.objects.filter(pk=activity.pk).update(status=S.DONE)
        assert not environment.is_environmental(activity)
        with pytest.raises(ValidationError):
            environment.record_results(activity, by=manager, waste_grams=1000)


@pytest.mark.parametrize(
    "wrong",
    [
        {"waste_grams": -1},
        {"waste_grams": 12.5},
        {"waste_grams": True},
        {"waste_grams": environment.MAX_GRAMS + 1},
        {"species": "x" * 2001},
        {"observations": "x" * 2001},
    ],
)
def test_wrong_results_are_rejected(manager, wrong):
    with pytest.raises(ValidationError):
        environment.record_results(env_outing(manager), by=manager, **wrong)
    assert not EnvironmentalResult.objects.exists()


# --- AC14: qui registra i qui només mira ----------------------------------------------------------


@pytest.mark.parametrize(
    ("role", "sees", "records"),
    [
        ("courses_manager", True, True),
        ("administrator", True, True),
        ("president", True, True),
        ("board", True, False),  # «Cons.»
        ("treasurer", False, False),
        ("secretary", False, False),
        ("instructor", False, False),
    ],
)
def test_ac14_who_sees_and_who_records(manager, make_admin, project, role, sees, records):  # noqa: F811
    outing = env_outing(manager, project)
    account = make_admin(role)
    if records:
        environment.record_results(outing, by=account, waste_grams=1000)
    else:
        with pytest.raises(Http404):
            environment.record_results(outing, by=account, waste_grams=1000)
        assert not EnvironmentalResult.objects.exists()
    client = client_for(account)
    for name, args in (
        ("environment", []),
        ("project_detail", [project.pk]),
        ("activity_results", [outing.pk]),
    ):
        response = client.get(reverse(f"administration:{name}", args=args))
        assert response.status_code == (200 if sees else 404), name
    response = client.post(
        reverse("administration:activity_results", args=[outing.pk]), {"waste_grams": "2"}
    )
    assert response.status_code == (303 if records else 404)
    if sees and not records:
        page = client.get(reverse("administration:activity_results", args=[outing.pk]))
        assert "Desa els resultats" not in page.content.decode()  # veu, però no hi ha formulari


# --- CA-M02-21: la fitxa del projecte -------------------------------------------------------------


def test_ca_m02_21_the_project_adds_up_the_waste_of_its_outings(manager, project):
    """CA-M02-21: tres sortides d'un projecte amb 12,5 kg, 8 kg i 4,25 kg de residus: el total de
    la fitxa és 24,75 kg (24.750 grams)."""
    for index, grams in enumerate((12500, 8000, 4250)):
        outing = env_outing(manager, project, title=f"Neteja inventada {index + 1}")
        environment.record_results(
            outing, by=manager, waste_grams=grams, species="Nacra\nPop roquer"
        )
    pending = env_outing(manager, project, title="Neteja inventada sense resultats")
    other = env_outing(manager, title="Neteja inventada d'un altre lloc")  # sense projecte
    environment.record_results(other, by=manager, waste_grams=99000, species="Espècie d'un altre")

    summary = environment.project_summary(project)
    assert summary.total_grams == 24750
    assert summary.total_kilos == "24,75 kg"
    assert (len(summary.outings), summary.with_results) == (4, 3)
    assert summary.species == ("Nacra", "Pop roquer")
    assert pending in [activity for activity, _result in summary.outings]

    page = client_for(manager).get(reverse("administration:project_detail", args=[project.pk]))
    html = page.content.decode()
    assert "24,75 kg" in html and "3 de 4" in html
    assert "Nacra, Pop roquer" in html
    assert "99 kg" not in html and "un altre lloc" not in html


def test_a_project_without_outings_adds_up_to_zero(manager, project):
    summary = environment.project_summary(project)
    assert (summary.total_grams, summary.total_kilos, summary.outings, summary.species) == (
        0,
        "0 kg",
        (),
        (),
    )


# --- Les pantalles --------------------------------------------------------------------------------


def test_the_results_screen_records_and_corrects(manager, project):
    client = client_for(manager)
    outing = env_outing(manager, project)
    url = reverse("administration:activity_results", args=[outing.pk])
    assert "Encara no s&#x27;han registrat" in client.get(url).content.decode() or (
        "Encara no s'han registrat" in client.get(url).content.decode()
    )
    response = client.post(url, {"waste_grams": "dotze"})
    assert response.status_code == 200
    assert "Escriu els quilos amb xifres" in response.content.decode()
    assert not EnvironmentalResult.objects.exists()

    data = {"waste_grams": "12,5", "species": "Nacra\nPop roquer", "observations": "Tot bé."}
    assert client.post(url, data).status_code == 303
    result = EnvironmentalResult.objects.get()
    assert (result.waste_grams, result.species) == (12500, "Nacra\nPop roquer")
    page = client.get(url).content.decode()
    assert "Resultats desats" in page and "12,5 kg" in page and "Nacra, Pop roquer" in page
    assert 'value="12,5"' in page  # el formulari per corregir porta el que hi ha
    listing = client.get(reverse("administration:environment")).content.decode()
    assert "Registrats" in listing and outing.title in listing and "12,5 kg" in listing


def test_the_results_screen_only_exists_for_environmental_outings(manager):
    client = client_for(manager)
    dive = an_outing(manager)
    assert client.get(reverse("administration:activity_results", args=[dive.pk])).status_code == 404
    assert client.get(reverse("administration:activity_results", args=[999_999])).status_code == 404
    not_done = env_outing(manager, status=S.OPEN)
    url = reverse("administration:activity_results", args=[not_done.pk])
    page = client.get(url).content.decode()
    assert "quan la sortida ja s'ha fet" in page and "Desa els resultats" not in page
    response = client.post(url, {"waste_grams": "1"})  # enviat a mà, el servei ho rebutja
    assert response.status_code == 200
    assert not EnvironmentalResult.objects.exists()


def test_the_activity_detail_links_to_the_results_only_when_it_applies(manager, make_admin):  # noqa: F811
    env, dive = env_outing(manager), an_outing(manager)
    client = client_for(manager)
    results = reverse("administration:activity_results", args=[env.pk])
    assert (
        f'href="{results}"'
        in client.get(reverse("administration:activity_detail", args=[env.pk])).content.decode()
    )
    assert (
        "Resultats ambientals</a>"
        not in client.get(reverse("administration:activity_detail", args=[dive.pk]))
        .content.decode()
        .split("</aside>")[-1]
    )
    # El tresorer gestiona activitats (AC7) però no té AC14: no hi veu l'enllaç.
    treasurer = client_for(make_admin("treasurer"))
    page = treasurer.get(reverse("administration:activity_detail", args=[env.pk])).content.decode()
    assert f'href="{results}"' not in page
    # I a «Projectes» (AC6) tampoc veu l'enllaç a la fitxa del projecte.
    catalogue.create_project(
        by=manager, name="Projecte inventat", objective="Objectiu.", department=general()
    )
    assert (
        "Fitxa"
        not in treasurer.get(reverse("administration:projects"))
        .content.decode()
        .split("</aside>")[-1]
    )


# --- RN-M02-23: res no es publica -----------------------------------------------------------------


def test_rn_m02_23_results_are_never_on_the_public_pages(manager, project):
    """Una sortida de medi ambient publicada no ensenya mai els resultats, i una de feta ja no és
    pública."""
    open_outing = env_outing(manager, project, status=S.DRAFT, title="Neteja inventada oberta")
    states.publish(open_outing, by=manager, now=BEFORE_DEADLINE)
    done = env_outing(manager, project, title="Neteja inventada feta")
    environment.record_results(
        done, by=manager, waste_grams=12500, species="Nacra", observations="X"
    )
    visitor = Client()
    assert visitor.get(reverse("activities:detail", args=[done.pk])).status_code == 404
    page = visitor.get(reverse("activities:detail", args=[open_outing.pk])).content.decode()
    listing = visitor.get(reverse("activities:list")).content.decode()
    for html in (page, listing):
        assert "12,5 kg" not in html and "Nacra" not in html and "Residus" not in html
    assert visitor.get(reverse("administration:environment")).status_code == 302  # cal entrar
    assert datetime.date(2027, 6, 14) == open_outing.starts_on
