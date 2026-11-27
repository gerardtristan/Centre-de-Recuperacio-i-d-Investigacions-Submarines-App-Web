"""Editor de la web (T-M07-06a, decisió 106), al navegador: el President crea una pàgina, hi
afegeix blocs, n'omple un, l'arrossega per la nansa, el mou amb «Amunt», l'amaga i desfà amb el
teclat (Ctrl+Z). Pantalles a 1280, 390 i 320 px. Dades inventades."""

import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.website.models import PageDraft

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def blocks_of(slug):
    return PageDraft.objects.get(page__slug=slug).blocks


def test_the_president_edits_the_blocks_of_a_page(page, live_server, transactional_db, review):
    president = make_admin("presidencia.prova", "president")
    login_admin(page, live_server.url, president.login)
    page.goto(f"{live_server.url}{reverse('administration:website_pages')}")
    expect(page.get_by_role("heading", name="Pàgines", exact=True)).to_be_visible()
    review("editor-pagines")
    page.get_by_label("Títol").fill("Sortides (inventada)")
    page.get_by_label("Adreça").fill("sortides-inventada")
    page.get_by_role("button", name="Crea l'esborrany").click()
    expect(page.get_by_role("heading", name="Editor: Sortides (inventada)")).to_be_visible()

    for kind in ("Títol", "Text"):
        page.get_by_label("Bloc nou").select_option(label=kind)
        page.get_by_role("button", name="Afegeix el bloc").click()
        expect(page.get_by_text("Esborrany desat.")).to_be_visible()
    page.get_by_role("textbox", name="Text", exact=True).fill("Sortim cada **diumenge**.")
    page.get_by_role("button", name="Desa el bloc").click()
    expect(page.get_by_role("link", name="Text", exact=True)).to_be_visible()
    review("editor-bloc")

    handle = page.locator("[data-nansa]")
    handle.nth(1).drag_to(handle.nth(0))
    page.wait_for_url(re.compile(r"/pagines/\d+/$"))  # el servidor ha desat l'ordre nou
    expect(page.locator("[data-editor-blocs] li").first).to_contain_text("Text")
    assert [b["kind"] for b in blocks_of("sortides-inventada")] == ["text", "heading"]

    page.locator("[data-editor-blocs] a", has_text="Text").click()
    page.get_by_role("button", name="Avall").click()
    assert [b["kind"] for b in blocks_of("sortides-inventada")] == ["heading", "text"]
    page.get_by_role("button", name="Amaga").click()
    expect(page.locator("[data-editor-blocs]").get_by_text("Amagat")).to_be_visible()
    page.locator("h1").click()  # fora de cap camp: la drecera és de l'editor
    page.keyboard.press("Control+z")
    expect(page.locator("[data-editor-blocs]").get_by_text("Amagat")).to_have_count(0)
    assert not blocks_of("sortides-inventada")[1].get("hidden")


def test_the_preview_selects_a_block_and_autosaves(page, live_server, transactional_db, review):
    """T-M07-06b: clicar un bloc a la vista prèvia el tria i el formulari es desa sol."""
    from apps.core.models import Setting
    from apps.website import pages

    Setting.objects.filter(key="website.autosave_seconds").update(initial_value=5)
    president = make_admin("presidencia.prova", "president")
    web = pages.save_page(None, actor=president, slug="previa-inventada", title="Prèvia")[0]
    blocks = [{"kind": "heading", "text": "Benvinguts", "level": 2},
              {"kind": "quote", "text": "El mar ens uneix (inventada)."}]  # fmt: skip
    pages.save_draft(web, blocks, president)
    login_admin(page, live_server.url, president.login)
    page.goto(f"{live_server.url}{reverse('administration:website_page_editor', args=[web.pk])}")
    preview = page.frame_locator("[data-vista-previa]")
    preview.locator('[data-bloc="1"]').click()
    expect(page.get_by_role("heading", name="Cita", exact=True)).to_be_visible()
    page.get_by_role("textbox", name="Text", exact=True).fill("El mar ens uneix des de 1954.")
    expect(page.locator("[data-desat-estat]")).to_have_text("Desat.", timeout=15000)
    expect(preview.get_by_text("El mar ens uneix des de 1954.")).to_be_visible()
    assert blocks_of("previa-inventada")[1]["text"] == "El mar ens uneix des de 1954."
    review("editor-previa")
