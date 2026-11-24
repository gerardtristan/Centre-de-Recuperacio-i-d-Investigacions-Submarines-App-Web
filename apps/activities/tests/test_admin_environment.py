"""Pantalles dels resultats ambientals i de la fitxa de projecte (T-M02-20b; AC14; CA-M02-21;
RN-M02-23). El servei té les seves proves a `test_environment.py`. Només dades inventades."""

import html

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities.models import Activity, EnvironmentalResult
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import an_outing
from .test_environment import env_outing, manager, project  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
S = Activity.Status


def results(activity):
    return reverse("administration:activity_environment", args=[activity.pk])


def text(response):
    assert response.status_code == 200
    return html.unescape(response.content.decode())


def test_ca_m02_21_results_add_up_in_the_project(login_as, manager, project):  # noqa: F811
    outing = env_outing(manager, project, title="Neteja inventada")
    client = login_as(manager, AREA_ADMIN)
    detail = reverse("administration:activity_detail", args=[outing.pk])
    assert results(outing) in text(client.get(detail))
    data = {"kilos": "12,5", "species": "Nacra\nNacra\nPop roquer", "observations": ""}
    assert client.post(results(outing), data).status_code == 303
    result = EnvironmentalResult.objects.get()
    assert (result.waste_grams, result.species) == (12500, "Nacra\nPop roquer")
    client.post(results(outing), {**data, "kilos": "13"})
    result.refresh_from_db()
    assert result.waste_grams == 13000
    page = text(client.get(reverse("administration:environmental_project", args=[project.pk])))
    assert "13 kg" in page and "Nacra, Pop roquer" in page and "Neteja inventada" in page


def test_the_board_only_reads(login_as, make_admin, manager):  # noqa: F811
    outing = env_outing(manager)
    board = login_as(make_admin(Role.Code.BOARD), AREA_ADMIN)
    page = text(board.get(results(outing)))
    assert "Desa els resultats" not in page
    assert board.post(results(outing), {"kilos": "1"}).status_code == 404
    assert not EnvironmentalResult.objects.exists()


def test_before_the_outing_is_done_nothing_is_recorded(login_as, manager):  # noqa: F811
    outing = env_outing(manager, status=S.OPEN)
    client = login_as(manager, AREA_ADMIN)
    assert "quan la sortida ja s'ha fet" in text(client.get(results(outing)))
    assert "ja s'ha fet" in text(client.post(results(outing), {"kilos": "1"}))
    assert not EnvironmentalResult.objects.exists()


def test_a_negative_amount_is_rejected(login_as, manager):  # noqa: F811
    outing = env_outing(manager)
    response = login_as(manager, AREA_ADMIN).post(results(outing), {"kilos": "-2"})
    assert response.status_code == 200 and not EnvironmentalResult.objects.exists()


def test_only_environmental_outings_and_only_with_ac14(login_as, make_admin, manager, project):  # noqa: F811
    client = login_as(manager, AREA_ADMIN)
    assert client.get(results(an_outing(manager))).status_code == 404
    treasurer = login_as(make_admin(Role.Code.TREASURER), AREA_ADMIN)
    assert treasurer.get(results(env_outing(manager))).status_code == 404
    project_page = reverse("administration:environmental_project", args=[project.pk])
    assert treasurer.get(project_page).status_code == 404
