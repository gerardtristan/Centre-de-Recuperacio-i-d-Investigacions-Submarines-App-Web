"""Plantilles de pàgina amb contingut d'exemple i les fotos de la 107 a les dades de mostra
(T-M07-20b, decisió 106). Només dades inventades i fitxers de prova."""

import importlib

import pytest
from django.apps import apps as registry
from django.urls import reverse

from apps.core import business_settings
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website import blocks, demo_data, page_templates, pages
from apps.website.models import MediaAsset, Page, PageDraft
from apps.website.tests.test_media_07 import COMPLETE, JPEG, PNG, _photo

pytestmark = pytest.mark.django_db
SIX = ["portada", "seccio", "article", "projecte", "galeria", "captacio"]


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin(Role.Code.ADMINISTRATOR)


def test_the_six_templates_of_the_addendum_are_a_closed_list():
    assert list(Page.Template.values) == SIX
    assert page_templates.example("inventada") == []


@pytest.mark.parametrize("template", SIX)
def test_each_example_is_a_valid_draft_and_with_photos_it_can_be_published(admin, template):
    blocks.validate(page_templates.example(template), publishing=False)
    for _i in range(6):
        _photo(admin, **COMPLETE)
    business_settings.change("website.public_images_enabled", True, admin, "Prova")
    pages.validate_blocks(page_templates.example(template), publishing=True)


def test_a_new_page_starts_with_the_example_of_its_template(admin):
    response = admin_client(admin).post(
        reverse("administration:website_pages"),
        {"title": "Fes-te soci (prova)", "slug": "captacio-inventada", "template": "captacio"},
    )
    page = Page.objects.get(slug="captacio-inventada")
    assert response.status_code == 302
    assert PageDraft.objects.get(page=page).blocks == page_templates.example("captacio")


def test_p750_the_old_templates_move_to_the_nearest_new_one(admin):
    migration = importlib.import_module("apps.website.migrations.0023_page_templates")
    made = {old: pages.save_page(None, actor=admin, slug=f"vella-{old}", title=old)[0]
            for old in ("basica", "llista", "blog", "portada")}  # fmt: skip
    for old, page in made.items():
        Page.objects.filter(pk=page.pk).update(template=old)
    migration.forward(registry, None)
    assert {old: Page.objects.get(pk=p.pk).template for old, p in made.items()} == {
        "basica": "seccio", "llista": "seccio", "blog": "article", "portada": "portada",
    }  # fmt: skip
    migration.backward(registry, None)
    assert Page.objects.get(pk=made["blog"].pk).template == "blog"


def test_the_demo_data_loads_the_107_photos_with_their_details(admin, tmp_path, monkeypatch):
    monkeypatch.setattr(demo_data, "PHOTOS", tmp_path)
    assert demo_data.load_photos(admin) == []  # sense `fotos.yml`, cap
    (tmp_path / "barca.png").write_bytes(PNG)
    (tmp_path / "port.jpg").write_bytes(JPEG)
    (tmp_path / "fotos.yml").write_text(
        "fotos:\n"
        "  - fitxer: barca.png\n    autor: C.R.I.S.\n    permis: «Del club (107)»\n"
        '    persones: no\n    alt: "Una barca al port"\n'
        "  - fitxer: port.jpg\n    autor: C.R.I.S.\n    permis: «Del club (107)»\n"
        '    persones: sí\n    alt: "Tres bussejadors"\n'
        '  - fitxer: no-hi-es.jpg\n    alt: "Falta"\n'
        '  - fitxer: animada.gif\n    alt: "No es carrega"\n',
        encoding="utf-8",
    )
    loaded = demo_data.load_photos(admin)
    assert [(a.alt_text, a.shows_people, a.people_consent, a.licence_note) for a in loaded] == [
        ("Una barca al port", False, False, "Del club (107)"),
        ("Tres bussejadors", True, True, "Del club (107)"),
    ]
    assert all(a.publishable for a in MediaAsset.objects.all())
