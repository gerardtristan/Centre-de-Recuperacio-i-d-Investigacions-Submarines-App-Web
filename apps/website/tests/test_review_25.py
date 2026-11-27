"""Revisor de qualitat abans de publicar (T-M07-25, decisió 106): avisos, mai bloquejos. Només
dades inventades."""

import pytest
from django.urls import reverse

from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website import pages, review
from apps.website.models import MediaAsset, PageVersion
from apps.website.tests.test_blocks_106 import KEY, block
from apps.website.tests.test_media_07 import COMPLETE, _photo

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin(Role.Code.ADMINISTRATOR)


@pytest.fixture
def page(admin):
    return pages.save_page(None, actor=admin, slug="revisor-inventat", title="Revisor")[0]


def test_a_clean_page_has_no_warnings(page, admin):
    published = pages.save_page(None, actor=admin, slug="qui-som-inventat", title="Qui som")[0]
    pages.publish_page(published, [block("heading")], admin)
    blocks = [block("heading"), block("text", body="Vegeu [qui som](/qui-som-inventat/)."),
              block("button", target="/ajuda/")]  # fmt: skip
    assert review.review(page, blocks) == []


def test_each_problem_gives_a_warning(page, admin):
    asset = _photo(admin, **COMPLETE)
    MediaAsset.objects.filter(pk=asset.pk).update(alt_text="  ")
    blocks = [
        block("heading", level=3),
        block("image", media=str(asset.key)),
        block("button", target="/no-existeix/", style="primary"),
        block("join_cta"),
        block("section", columns=[[block("divider", hidden=True)]]),
        {"kind": "text"},
    ]
    warnings = review.review(page, blocks)
    assert len(warnings) == 6
    text = " ".join(warnings)
    for piece in (
        "nivell 3",
        "/no-existeix/",
        "text alternatiu",
        "secció buida",
        "botó principal",
        "no es podrà",
    ):
        assert piece in text


def test_a_missing_photo_and_long_share_texts_are_warnings_too(page, admin):
    page, _w = pages.save_page(page, actor=admin, share_title="T" * 61)
    warnings = review.review(page, [block("image", media=KEY)])
    assert any("text alternatiu" in w for w in warnings) and any("60" in w for w in warnings)


def test_warnings_never_block_publishing_and_show_in_the_editor(page, admin):
    blocks = [block("heading", level=3), block("button", target="/no-existeix/")]
    pages.save_draft(page, blocks, admin)
    client = admin_client(admin)
    html = client.get(reverse("administration:website_page_editor", args=[page.pk])).content
    assert "nivell 3" in html.decode()
    revision = str(pages.draft_state(page)[1])
    client.post(reverse("administration:website_page_publish", args=[page.pk]),
                {"revision": revision})  # fmt: skip
    assert PageVersion.objects.get().blocks == blocks
