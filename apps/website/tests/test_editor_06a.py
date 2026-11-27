"""Editor de la web: llista de pàgines i editor de blocs (T-M07-06a, decisió 106; RN-M07-15 i 16;
CA-M07-23). WP1 amb la matriu inicial de la T-M07-02. Només dades inventades."""

import pytest
from django.urls import reverse

from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website import editor, pages
from apps.website.editor_forms import BlockForm, summary
from apps.website.models import Page, PageDraft, PageVersion
from apps.website.tests.test_blocks_106 import VALID, block

pytestmark = pytest.mark.django_db
R = Role.Code
LIST = reverse("administration:website_pages")
H1, H2, H3 = (block("heading", text=t) for t in ("Un", "Dos", "Tres"))


@pytest.fixture
def president(make_admin):  # noqa: F811
    return make_admin(R.PRESIDENT)


@pytest.fixture
def page(president):
    return pages.save_page(None, actor=president, slug="editor-inventat", title="Editor")[0]


def action_url(page):
    return reverse("administration:website_page_editor_action", args=[page.pk])


def draft(page):
    return PageDraft.objects.get(page=page).blocks


@pytest.mark.parametrize(
    ("action", "index", "extra", "expected"),
    [
        ("add", 0, {"kind": "divider"}, [H1, {"kind": "divider"}, H2, H3]),
        ("up", 1, {}, [H2, H1, H3]),
        ("down", 1, {}, [H1, H3, H2]),
        ("reorder", -1, {"order": [2, 0, 1]}, [H3, H1, H2]),
        ("duplicate", 0, {}, [H1, H1, H2, H3]),
        ("hide", 2, {}, [H1, H2, {**H3, "hidden": True}]),
        ("remove", 1, {}, [H1, H3]),
        ("update", 0, {"block": H3}, [H3, H2, H3]),
    ],
)
def test_each_action_returns_a_new_list(action, index, extra, expected):
    blocks = [H1, H2, H3]
    assert editor.apply(blocks, action, index, **extra) == expected
    assert blocks == [H1, H2, H3]
    if action == "hide":
        assert editor.apply(expected, "hide", 2)[2] == {**H3, "hidden": False}


@pytest.mark.parametrize(
    ("action", "index", "extra"),
    [("up", 0, {}), ("down", 2, {}), ("remove", 3, {}), ("add", 0, {"kind": "script"}),
     ("reorder", 0, {"order": [0, 0, 1]}), ("jump", 0, {})],
)  # fmt: skip
def test_an_action_that_makes_no_sense_is_rejected(action, index, extra):
    with pytest.raises((IndexError, ValueError)):
        editor.apply([H1, H2, H3], action, index, **extra)


def test_the_editor_starts_from_the_last_version_with_old_kinds_translated(page, president):
    PageVersion.objects.create(page=page, number=1, published_by=president,
                               blocks=[{"kind": "text", "text": "Antic"}])  # fmt: skip
    assert editor.editing_blocks(page) == [{"kind": "text", "body": "Antic"}]


def test_wp1_creates_a_page_and_edits_its_blocks_with_undo_and_redo(page, president):
    client = admin_client(president)
    response = client.post(LIST, {"title": "Nova", "slug": "nova-inventada", "template": "basica"})
    new = Page.objects.get(slug="nova-inventada")
    assert response["Location"] == reverse("administration:website_page_editor", args=[new.pk])
    url = action_url(page)
    client.post(url, {"action": "add", "index": "-1", "kind": "heading"})
    response = client.post(url, {"action": "update", "index": "0", "text": "Qui som", "level": "3"})
    assert response["Location"].endswith("?bloc=0")
    assert draft(page) == [{"kind": "heading", "text": "Qui som", "level": 3}]
    client.post(url, {"action": "duplicate", "index": "0"})
    client.post(url, {"action": "hide", "index": "1"})
    client.post(url, {"action": "undo"})
    client.post(url, {"action": "undo"})
    assert draft(page) == [{"kind": "heading", "text": "Qui som", "level": 3}]
    client.post(url, {"action": "redo"})
    assert len(draft(page)) == 2
    editor_page = client.get(reverse("administration:website_page_editor", args=[page.pk]))
    assert "Títol · Qui som" in editor_page.content.decode()
    assert not PageVersion.objects.exists()  # editar no publica


def test_ca_m07_23_a_block_out_of_schema_is_rejected_and_nothing_is_saved(page, president):
    client = admin_client(president)
    pages.save_draft(page, [H1], president)
    url = action_url(page)
    response = client.post(url, {"action": "update", "index": "0", "text": "T" * 121,
                                 "level": "2"})  # fmt: skip
    assert response.status_code == 400
    assert client.post(url, {"action": "reorder", "order": "0,0"}).status_code == 302
    assert client.post(url, {"action": "update", "index": "-1"}).status_code == 302
    assert draft(page) == [H1]


@pytest.mark.parametrize("role", [R.SECRETARY, R.TREASURER, R.BOARD])
def test_without_wp1_the_screens_are_not_found(make_admin, page, role):  # noqa: F811
    client = admin_client(make_admin(role))
    assert client.get(LIST).status_code == 404
    editor_url = reverse("administration:website_page_editor", args=[page.pk])
    assert client.get(editor_url).status_code == 404
    assert client.post(action_url(page), {"action": "add", "kind": "divider"}).status_code == 404
    assert not PageDraft.objects.exists()


@pytest.mark.parametrize("kind", VALID)
def test_the_form_of_each_kind_gives_back_the_same_block(kind):
    """El formulari torna el mateix bloc, amb les variants que no s'havien triat explícites. Les
    fotos i el tema només hi surten si existeixen (biblioteca i ajuda), i les columnes d'una
    secció no s'editen aquí (P-682): es conserven."""
    skipped = ("media", "thumbnail", "topic")
    original = block(kind)
    expected = {k: v for k, v in original.items() if k not in skipped}
    if kind == "project_cards":
        cards = original["items"]
        expected["items"] = [{k: v for k, v in i.items() if k != "media"} for i in cards]
    form = BlockForm(kind, block=original)
    data = {}
    for name, field in form.fields.items():
        if name.endswith(skipped):
            continue
        value = form.get_initial_for_field(field, name)
        if value is None and hasattr(field, "coerce"):  # el primer valor del desplegable
            value = field.choices[0][0]
            expected[name] = field.coerce(value)
        if value not in (None, "", []):
            data[name] = value
    bound = BlockForm(kind, data, block=original)
    assert bound.is_valid(), bound.errors
    assert bound.to_block(original) == expected
    assert summary(original).startswith(str(summary({"kind": kind})))
