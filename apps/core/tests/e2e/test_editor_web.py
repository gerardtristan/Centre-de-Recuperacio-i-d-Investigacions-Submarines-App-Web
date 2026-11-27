"""Editor de la web (T-M07-06a, decisió 106), al navegador: el President crea una pàgina, hi
afegeix blocs, n'omple un, l'arrossega per la nansa, el mou amb «Amunt», l'amaga i desfà amb el
teclat (Ctrl+Z). Pantalles a 1280, 390 i 320 px. Dades inventades."""

import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.website.models import Page, PageDraft

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
    # Comença amb l'exemple de la plantilla (T-M07-20b): aquí, des d'una pàgina buida.
    from apps.website import pages

    pages.save_draft(Page.objects.get(slug="sortides-inventada"), [], president)
    page.reload()

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


def test_versions_compare_schedule_retire_and_recover(page, live_server, transactional_db, review):
    """T-M07-22: comparar l'esborrany amb la versió publicada, programar i anul·lar, retirar i
    recuperar la pàgina."""
    from apps.website import pages

    president = make_admin("presidencia.prova", "president")
    web = pages.save_page(None, actor=president, slug="versions-inventada", title="Versions")[0]
    pages.publish_page(web, [{"kind": "heading", "text": "Benvinguts", "level": 2}], president)
    new = [{"kind": "heading", "text": "Benvinguts al club", "level": 2}]
    pages.save_draft(web, new, president)
    login_admin(page, live_server.url, president.login)
    page.goto(f"{live_server.url}{reverse('administration:website_page_editor', args=[web.pk])}")
    page.get_by_role("link", name="Versions i programació").click()
    expect(page.get_by_role("heading", name="Versions", exact=True)).to_be_visible()
    expect(page.get_by_text("Canviat")).to_be_visible()
    page.get_by_label("Dia i hora").fill("2030-12-01T09:00")
    page.get_by_role("button", name="Programa", exact=True).click()
    expect(page.get_by_text("Acció programada.")).to_be_visible()
    review("editor-versions")
    page.get_by_role("button", name="Anul·la").click()
    expect(page.get_by_text("Acció anul·lada.")).to_be_visible()
    page.get_by_role("button", name="Retira la pàgina").click()
    expect(page.get_by_text("Pàgina retirada. Es pot recuperar.")).to_be_visible()
    page.get_by_role("button", name="Recupera la pàgina").click()
    expect(page.get_by_text("Pàgina recuperada en esborrany.", exact=False)).to_be_visible()


GOOGLE = ("google", "youtube", "ytimg", "gstatic", "doubleclick", "ggpht")


def test_ca_m07_25_no_request_to_google_before_the_click(
    page, live_server, transactional_db, review
):
    """T-M07-23: amb `website.youtube_enabled` encès, el bloc de vídeo no demana res a cap domini
    de Google fins que es prem; després, només a youtube-nocookie.com (aquí, una resposta falsa)."""
    from apps.core.models import Setting
    from apps.website import pages

    Setting.objects.filter(key="website.youtube_enabled").update(initial_value=True)
    president = make_admin("presidencia.prova", "president")
    web = pages.save_page(None, actor=president, slug="video-inventat", title="Vídeo")[0]
    blocks = [{"kind": "video", "source": "youtube", "youtube_id": "dQw4w9WgXcQ",
               "title": "Immersió inventada"}]  # fmt: skip
    pages.save_draft(web, blocks, president)
    login_admin(page, live_server.url, president.login)
    hosts = []
    page.on("request", lambda request: hosts.append(request.url.split("/")[2]))
    page.route("https://www.youtube-nocookie.com/**", lambda route: route.fulfill(
        status=200, content_type="text/html", body="<p>video fals</p>"))  # fmt: skip
    page.goto(f"{live_server.url}{reverse('administration:website_page_preview', args=[web.pk])}")
    button = page.get_by_role("button", name="En prémer, es carrega YouTube (Google)")
    expect(button).to_be_visible()
    page.wait_for_load_state("networkidle")
    assert not [h for h in hosts if any(g in h for g in GOOGLE)]
    review("video-abans-del-clic")
    assert not [h for h in hosts if any(g in h for g in GOOGLE)]
    button.click()
    expect(page.frame_locator("iframe").get_by_text("video fals")).to_be_visible()
    google = {h for h in hosts if any(g in h for g in GOOGLE)}
    assert google == {"www.youtube-nocookie.com"}


def test_a_new_page_from_a_template_starts_with_its_example(
    page, live_server, transactional_db, review
):
    """T-M07-20b: una pàgina nova amb la plantilla Portada obre l'editor amb el seu exemple."""
    president = make_admin("presidencia.prova", "president")
    login_admin(page, live_server.url, president.login)
    page.goto(f"{live_server.url}{reverse('administration:website_pages')}")
    page.get_by_label("Títol").fill("Inici (inventada)")
    page.get_by_label("Adreça").fill("inici-inventada")
    page.get_by_label("Plantilla").select_option(label="Portada")
    page.get_by_role("button", name="Crea l'esborrany").click()
    blocks = page.locator("[data-editor-blocs]")
    expect(blocks.get_by_text("Imatge amb text · Qui som")).to_be_visible()
    expect(blocks.get_by_text("Crida «Fes-te soci» · Fes-te soci")).to_be_visible()
    review("editor-plantilla-portada")
