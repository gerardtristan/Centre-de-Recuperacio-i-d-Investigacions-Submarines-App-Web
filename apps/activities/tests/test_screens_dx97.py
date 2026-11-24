"""T-DX-97 (revisió de DISSENY de la #513 i la #518): l'avaluació de la pràctica té el seu botó
principal (D19), i la fitxa i la sol·licitud d'homologació porten l'avantítol en text, com la resta,
amb «Tornar a les homologacions» a sota. Només dades inventades."""

# ruff: noqa: F811 (fixtures importades com a paràmetres)
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .test_admin_filings import REQUEST, client_of, detail, requested  # noqa: F401 (fixture)
from .test_assessment_views import practice, sheet_url  # noqa: F401 (fixture)
from .test_attendance import manager  # noqa: F401 (fixture)
from .test_attendance_views import today_course  # noqa: F401 (fixture)
from .test_filings import levels, secretary  # noqa: F401 (fixture)


def test_the_assessment_has_its_primary_button(login_as, practice):
    client = login_as(practice.own, AREA_ADMIN)
    page = main_of(client.get(sheet_url(practice, practice.first)).content.decode())
    assert '<button class="boto boto-principal" type="submit">Desa l\'avaluació</button>' in page


def test_the_filing_pages_have_a_plain_eyebrow_and_a_way_back(client_of, secretary, requested):
    client = client_of(secretary)
    back = f'<a href="{reverse("administration:filings")}">Tornar a les homologacions</a>'
    for url in (detail(requested), REQUEST):
        page = main_of(client.get(url).content.decode())
        assert '<p class="etiqueta-seccio">Activitats</p>' in page, url
        assert back in page, url
