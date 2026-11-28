"""Patrons i blocs compartits (T-M07-20a, decisió 106): dades amb versions, inserir-los a l'editor
i, d'un bloc compartit, canviar-lo en un sol lloc. WP1 fa de WP9 i WP10 fins al torn del nucli.
Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.db import Error, connection, transaction
from django.urls import reverse

from apps.core import business_settings
from apps.core.models import AppendOnlyError, AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website import editor, library, media, pages, render
from apps.website.models import PageDraft, Pattern, PatternVersion, SharedBlock
from apps.website.tests.test_blocks_106 import block
from apps.website.tests.test_media_07 import COMPLETE, _photo

pytestmark = pytest.mark.django_db
R = Role.Code
H1, H2 = block("heading", text="Un"), block("heading", text="Dos")
CTA = block("join_cta", title="Fes-te soci (inventat)")


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def page(admin):
    page = pages.save_page(None, actor=admin, slug="biblioteca-inventada", title="Biblioteca")[0]
    pages.save_draft(page, [H1, H2], admin)
    return page


def post(client, page, data):
    blocks, revision = pages.draft_state(page)
    url = reverse("administration:website_page_library", args=[page.pk])
    return client.post(url, {"revision": str(revision), **data})


def test_a_pattern_has_versions_in_the_record_and_they_cannot_change(admin):
    first = library.save_pattern("Capçalera", [H1], admin)
    second = library.save_pattern(" Capçalera ", [H1, H2], admin)
    assert (first.number, second.number, Pattern.objects.count()) == (1, 2, 1)
    assert library.pattern_blocks(Pattern.objects.get()) == [H1, H2]
    entries = AuditEntry.objects.filter(action=library.ACTION_PATTERN).order_by("pk")
    assert [(e.old_value, e.new_value) for e in entries] == [(None, 1), (1, 2)]
    second.blocks = []
    with pytest.raises(AppendOnlyError):
        second.save()
    for sql in ("UPDATE website_patternversion SET number = 9",
                "DELETE FROM website_patternversion"):  # fmt: skip
        with pytest.raises(Error), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(sql)
    assert str(second) == "Capçalera v2" and str(second.pattern) == "Capçalera"


@pytest.mark.parametrize(
    ("name", "blocks"), [("", [H1]), ("N" * 101, [H1]), ("Bo", [{"kind": "script"}])]
)
def test_a_pattern_without_a_name_or_out_of_schema_is_rejected(admin, name, blocks):
    with pytest.raises(ValidationError):
        library.save_pattern(name, blocks, admin)
    assert not PatternVersion.objects.exists()


def test_a_shared_block_is_not_a_reference_and_its_name_is_unique(admin):
    version = library.save_shared("Crida", {**CTA, "hidden": True}, admin)
    assert version.block == CTA and str(version) == "Crida v1"  # `hidden` és de cada pàgina
    for name, content in (("Crida", CTA), ("Una altra", {"kind": "shared", "shared": 1})):
        with pytest.raises(ValidationError):
            library.save_shared(name, content, admin)
    assert str(SharedBlock.objects.get()) == "Crida"


def test_the_editor_saves_and_inserts_a_pattern_as_a_copy(page, admin):
    client = admin_client(admin)
    post(client, page, {"action": "save_pattern", "name": "Inici"})
    pattern = Pattern.objects.get()
    post(client, page, {"action": "insert_pattern", "pattern": pattern.pk, "index": "0"})
    assert PageDraft.objects.get().blocks == [H1, H1, H2, H2]
    library.save_pattern("Inici", [CTA], admin)  # una versió nova no canvia la pàgina
    assert PageDraft.objects.get().blocks == [H1, H1, H2, H2]


def test_a_shared_block_changes_in_one_place_for_every_page(page, admin):
    client = admin_client(admin)
    post(client, page, {"action": "make_shared", "name": "Títol comú", "index": "1"})
    shared = SharedBlock.objects.get()
    assert PageDraft.objects.get().blocks[1] == {"kind": "shared", "shared": shared.pk,
                                                 "hidden": False}  # fmt: skip
    other = pages.save_page(None, actor=admin, slug="altra-inventada", title="Altra")[0]
    pages.save_draft(other, [], admin)
    post(client, other, {"action": "insert_shared", "shared": shared.pk, "index": "-1"})
    editor_html = client.get(reverse("administration:website_page_editor", args=[other.pk])
                             + "?bloc=0").content.decode()  # fmt: skip
    assert "Bloc compartit: Títol comú" in editor_html
    assert "canvia l'esborrany de totes les pàgines" in editor_html
    data = {"action": "update_shared", "index": "0", "text": "Dos (comú)", "level": "2"}
    assert post(client, other, {**data, "base": "antiga"}).status_code == 409
    wrong = {**data, "level": "9", "base": editor.fingerprint(H2)}
    assert post(client, other, wrong).status_code == 400
    post(client, other, {**data, "base": editor.fingerprint(H2)})
    for each in (page, other):
        html = render.render_blocks(PageDraft.objects.get(page=each).blocks, each)
        assert "Dos (comú)" in html


def test_rendering_keeps_the_hidden_of_each_page_and_skips_a_missing_one(page, admin):
    version = library.save_shared("Cita", block("quote", text="Comuna"), admin)
    ref = {"kind": "shared", "shared": version.shared_id}
    assert "Comuna" in render.render_blocks([ref], page)
    assert render.render_blocks([{**ref, "hidden": True}], page) == ""
    section = block("section", columns=[[ref]])
    assert "Comuna" in render.render_blocks([section], page)
    assert render.render_blocks([{"kind": "shared", "shared": 999}], page) == ""


def test_publishing_checks_the_shared_content_and_serves_its_photos(page, admin):
    business_settings.change("website.public_images_enabled", True, admin, "Prova")
    asset = _photo(admin)
    version = library.save_shared("Foto", block("image", media=str(asset.key)), admin)
    ref = [{"kind": "shared", "shared": version.shared_id}]
    with pytest.raises(ValidationError):  # la foto no té autor ni permís
        pages.publish_page(page, ref, admin)
    media.update_details(asset, actor=admin, **COMPLETE)
    pages.publish_page(page, ref, admin)
    assert media.public_asset(str(asset.key)) == asset


@pytest.mark.parametrize(
    "data",
    [{"action": "make_shared", "name": "X", "index": "9"}, {"action": "jump"},
     {"action": "update_shared", "index": "0"}],
)  # fmt: skip
def test_actions_that_make_no_sense_are_refused(page, admin, data):
    response = post(admin_client(admin), page, data)
    assert response.status_code == 302 and not SharedBlock.objects.exists()


def test_without_wp1_the_library_is_not_found(page, make_admin):  # noqa: F811
    response = post(admin_client(make_admin(R.SECRETARY)), page, {"action": "save_pattern",
                                                                  "name": "X"})  # fmt: skip
    assert response.status_code == 404 and not Pattern.objects.exists()


def test_review_a_published_page_keeps_its_shared_version_until_it_is_published_again(page, admin):
    """Revisió de la 20a: canviar un compartit no canvia la web fins que es torna a publicar la
    pàgina; tornar a una versió recupera el contingut d'aleshores."""
    version = library.save_shared("Cita", block("quote", text="Primera"), admin)
    ref = {"kind": "shared", "shared": version.shared_id}
    first = pages.publish_page(page, [ref], admin)
    assert first.blocks == [{**ref, "version": 1}]
    library.save_shared(SharedBlock.objects.get(), block("quote", text="Segona"), admin)
    assert "Primera" in render.render_blocks(first.blocks, page)  # la web, com abans
    assert "Segona" in render.render_blocks([ref], page, preview=True)  # l'esborrany, la nova
    pages.save_draft(page, [ref], admin)
    second = pages.publish_draft(page, admin)
    assert "Segona" in render.render_blocks(second.blocks, page)
    third = pages.revert_to(first, admin)
    assert "Primera" in render.render_blocks(third.blocks, page)


def test_review_a_shared_block_cannot_hold_a_reference_inside_a_section(admin):
    inner = block("section", columns=[[{"kind": "shared", "shared": 1}]])
    with pytest.raises(ValidationError):
        library.save_shared("Amb secció", inner, admin)
