"""Tutorials i «Mira com es fa» (T-M07-10; RN-M07-05, 10 i 11; CA-M07-17). Només dades
inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.template import Context, Template
from django.test import RequestFactory
from django.urls import resolve

from apps.core.models import Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import help as faq
from apps.website import media
from apps.website.tests.test_media_07 import PNG

pytestmark = pytest.mark.django_db
R = Role.Code
SCREEN = "payments:charge"


@pytest.fixture
def editor(make_admin):  # noqa: F811
    return make_admin(R.ADMINISTRATOR)


def _tutorial(editor, slug="pagar-la-quota", published=True, **fields):
    data = {"title": "Com pagar la quota", "steps": "Obre «Les meves quotes».\n\nPrem «Paga».",
            "screen_code": SCREEN, **fields}  # fmt: skip
    return faq.save_tutorial(None, actor=editor, slug=slug, published=published, **data)


def _render_on(url):
    request = RequestFactory().get(url)
    request.resolver_match = resolve(url)
    return Template("{% load website_help %}{% mira_com_es_fa %}").render(
        Context({"request": request})
    )


def test_ca_m07_17_the_screen_shows_the_link_while_the_tutorial_is_published(editor):
    tutorial = _tutorial(editor)
    html = _render_on("/socis/pagaments/1/")
    assert "Mira com es fa" in html and "/ajuda/tutorials/pagar-la-quota/" in html
    assert "Mira com es fa" not in _render_on("/socis/activitats/")  # una altra pantalla
    faq.save_tutorial(tutorial, actor=editor, published=False)
    assert "Mira com es fa" not in _render_on("/socis/pagaments/1/")


def test_tutorial_for_is_the_first_published_of_the_screen(editor):
    _tutorial(editor, "esborrany", published=False, order=0)
    second = _tutorial(editor, "segon", order=2)
    first = _tutorial(editor, "primer", order=1)
    assert faq.tutorial_for(SCREEN) == first
    assert faq.tutorial_for("") is None and second.pk


def test_the_public_page_shows_only_published_tutorials_with_escaped_steps(client, editor):
    _tutorial(editor, steps="<script>alert(1)</script>\nSegon pas")
    draft = _tutorial(editor, "esborrany", published=False)
    page = client.get("/ajuda/tutorials/pagar-la-quota/").content.decode()
    assert "<li>Segon pas</li>" in page and "&lt;script&gt;" in page and "<script>alert" not in page
    assert client.get(f"/ajuda/tutorials/{draft.slug}/").status_code == 404
    help_page = client.get("/ajuda/").content.decode()
    assert "Com pagar la quota" in help_page and "/ajuda/tutorials/esborrany/" not in help_page


def test_rn_m07_05_a_published_tutorial_needs_a_publishable_photo(editor):
    photo = media.upload(SimpleUploadedFile("pas.png", PNG), actor=editor, alt_text="La pantalla",
                         shows_people=False)  # fmt: skip
    with pytest.raises(ValidationError):
        _tutorial(editor, image=photo)
    assert not faq.published_tutorials().exists()


def test_d2_the_photo_is_shown_and_served_only_with_public_images_on(client, editor):
    photo = media.upload(SimpleUploadedFile("pas.png", PNG), actor=editor, alt_text="La pantalla",
                         shows_people=False, author="Autora Inventada",
                         licence_note="Cedida al club")  # fmt: skip
    _tutorial(editor, image=photo)
    url, photo_url = "/ajuda/tutorials/pagar-la-quota/", f"/web/fotos/{photo.key}/"
    assert photo_url not in client.get(url).content.decode()
    assert client.get(photo_url).status_code == 404
    Setting.objects.filter(key="website.public_images_enabled").update(initial_value=True)
    assert photo_url in client.get(url).content.decode()
    assert client.get(photo_url).status_code == 200


def test_a_role_without_wp4_cannot_write_tutorials(make_admin):  # noqa: F811
    with pytest.raises(Http404):
        _tutorial(make_admin(R.SECRETARY))
    assert not faq.published_tutorials().exists()


# --- Revisió de la T-M07-10 -------------------------------------------------------------------


def test_rn_m07_14_publishing_retiring_and_changing_a_tutorial_are_recorded(editor):
    from apps.core.models import AuditEntry

    tutorial = _tutorial(editor, published=False)
    faq.save_tutorial(tutorial, actor=editor, published=True)
    faq.save_tutorial(tutorial, actor=editor, title="Com pagar la quota anual")
    faq.save_tutorial(tutorial, actor=editor, published=False)
    entries = AuditEntry.objects.filter(target_id=str(tutorial.pk)).order_by("pk")
    assert [(e.action, e.field, e.old_value, e.new_value) for e in entries] == [
        (faq.TUTORIAL_PUBLISHED, "published", False, True),
        (faq.TUTORIAL_CHANGED, "title", "Com pagar la quota", "Com pagar la quota anual"),
        (faq.TUTORIAL_RETIRED, "published", True, False),
    ]


def test_an_old_edit_does_not_publish_again_a_retired_tutorial(editor):
    stale = _tutorial(editor)  # publicat, carregat abans de la retirada
    faq.save_tutorial(stale, actor=editor, published=False)
    faq.save_tutorial(stale, actor=editor, steps="Un pas corregit.")
    stale.refresh_from_db()
    assert (stale.published, stale.steps) == (False, "Un pas corregit.")


def test_the_screen_must_be_an_existing_route(editor):
    with pytest.raises(ValidationError):
        _tutorial(editor, screen_code="payments:no_existeix")
    assert _tutorial(editor, "sense-pantalla", screen_code="").screen_code == ""
