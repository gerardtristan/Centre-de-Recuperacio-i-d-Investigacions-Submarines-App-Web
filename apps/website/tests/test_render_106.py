"""Esborrany per pàgina i renderitzador únic (T-M07-04 i decisió 106; RN-M07-10, 15 i 16;
CA-M07-23 i 24). WP1 amb la matriu inicial de la T-M07-02. Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse

from apps.activities.models import Activity
from apps.activities.tests.helpers import an_outing
from apps.core import business_settings
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import pages, render
from apps.website.models import FaqEntry, FaqTopic, PageDraft, PageVersion
from apps.website.tests.test_blocks_106 import VALID, block
from apps.website.tests.test_media_07 import COMPLETE, _photo

pytestmark = pytest.mark.django_db
R = Role.Code


@pytest.fixture
def editor(make_admin):  # noqa: F811
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def page(editor):
    return pages.save_page(None, actor=editor, slug="esborrany-inventat", title="Esborrany")[0]


def test_rn_m07_16_one_draft_per_page_rewritten_on_each_save(page, editor, make_admin):  # noqa: F811
    pages.save_draft(page, [block("heading")], editor)
    other = make_admin(R.PRESIDENT)
    draft = pages.save_draft(page, [{"kind": "text"}], other)  # a mig fer (P-680)
    assert PageDraft.objects.count() == 1
    assert (draft.blocks, draft.updated_by) == ([{"kind": "text"}], other)
    assert str(draft) == "Esborrany" and not PageVersion.objects.exists()


def test_ca_m07_23_out_of_schema_is_not_saved_in_the_draft(page, editor):
    pages.save_draft(page, [block("heading")], editor)
    with pytest.raises(ValidationError):
        pages.save_draft(page, [block("text", colour="red")], editor)
    assert PageDraft.objects.get().blocks == [block("heading")]


def test_a_role_without_wp1_gets_not_found_and_no_draft(page, make_admin):  # noqa: F811
    with pytest.raises(Http404):
        pages.save_draft(page, [block("heading")], make_admin(R.SECRETARY))
    assert not PageDraft.objects.exists()


def test_hidden_blocks_never_reach_the_page(page):
    html = render.render_blocks(
        [block("heading", text="Visible"), block("heading", text="Amagat", hidden=True),
         block("section", columns=[[block("quote", text="Dins amagat", hidden=True)]])],
        page,
    )  # fmt: skip
    assert "Visible" in html and "Amagat" not in html and "Dins amagat" not in html


def test_ca_m07_24_markdown_fields_are_shown_safe_and_plain_fields_escaped(page):
    body = "<script>alert(1)</script> [x](javascript:alert(1)) [enllaç](https://exemple.cat)"
    html = render.render_blocks([block("text", title="<b>Títol</b>", body=body)], page)
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html and "<script>" not in html
    assert "[x](javascript:alert(1))" in html and 'href="javascript' not in html
    assert '<a href="https://exemple.cat">enllaç</a>' in html
    assert "&lt;b&gt;Títol&lt;/b&gt;" in html


def test_every_kind_renders_with_a_provisional_template(page):
    html = render.render_blocks([block(kind) for kind in VALID], page)
    assert "Qui som" in html and "Fes-te soci" in html and "Fetes" in html
    assert "Ara no hi ha cap activitat per mostrar." in html  # destacades i fetes, buides


def test_initial_kinds_render_translated_and_switches_hide_forms(page, editor):
    legacy = [{"kind": "text", "title": "Hola", "text": "**Antic**"}, {"kind": "newsletter"}]
    html = render.render_blocks(legacy, page)
    assert "<strong>Antic</strong>" in html and "butlletí" not in html
    business_settings.change("website.newsletter_enabled", True, editor, "Prova")
    assert "butlletí" in render.render_blocks(legacy, page)


def test_photos_arrive_resolved_and_a_retired_one_disappears(page, editor):
    business_settings.change("website.public_images_enabled", True, editor, "Prova")
    asset = _photo(editor, **COMPLETE)
    blocks = [block("image", media=str(asset.key))]
    assert f'alt="{asset.alt_text}"' in render.render_blocks(blocks, page)
    asset.status = asset.Status.RETIRED
    asset.save()
    assert "<img" not in render.render_blocks(blocks, page)


def test_faq_topic_and_recent_news_bring_their_data(page):
    topic = FaqTopic.objects.create(name="Quotes inventades")
    FaqEntry.objects.create(topic=topic, question="Quan es paga?", answer="Al gener.",
                            published=True)  # fmt: skip
    html = render.render_blocks([block("faq_topic", topic=topic.pk), block("recent_news")], page)
    assert "Quan es paga?" in html and "Quotes inventades" in html and "Notícies" in html


def test_review_photos_follow_the_public_images_switch_and_skip_empty_keys(page, editor):
    """Revisió de la #618: amb `website.public_images_enabled` apagat, cap foto; un forat d'una
    galeria a mig fer (P-680) no fa petar la vista prèvia."""
    asset = _photo(editor, **COMPLETE)
    blocks = [block("image", media=str(asset.key)), block("gallery", media=["", str(asset.key)])]
    assert "<img" not in render.render_blocks(blocks, page)
    business_settings.change("website.public_images_enabled", True, editor, "Prova")
    assert render.render_blocks(blocks, page).count("<img") == 2


def test_review_an_old_faq_block_without_topic_renders_nothing(page):
    assert "<details" not in render.render_blocks([{"kind": "faq"}], page)


def test_club_data_blocks_bring_resolved_items_without_names(page, make_admin):  # noqa: F811
    manager = make_admin(R.COURSES_MANAGER)
    outing = an_outing(manager, title="Sortida a les Medes (inventada)")
    Activity.objects.filter(pk=outing.pk).update(status=Activity.Status.OPEN)
    draft_only = an_outing(manager, title="Esborrany inventat")
    data = render._data(block("upcoming_activities", filters={"type": "outing"}))
    (item,) = data["items"]
    assert set(item) == {"title", "url", "start", "kind_label", "price", "photo",
                         "places_left"}  # fmt: skip
    assert item["title"] == "Sortida a les Medes (inventada)" and item["photo"] is None
    assert item["url"] == reverse("activities:public_detail", args=[outing.pk])
    assert render._data(block("featured_trip", activity=outing.pk))["activity"] == item
    assert render._data(block("featured_trip", activity=draft_only.pk)) == {
        "activity": None, "items": [],
    }  # fmt: skip
    html = render.render_blocks([block("upcoming_activities", filters={})], page)
    assert "Sortida a les Medes (inventada)" in html and "Esborrany inventat" not in html


def test_review_an_invalid_photo_key_is_ignored(editor):
    business_settings.change("website.public_images_enabled", True, editor, "Prova")
    assert render._images([{"kind": "image", "media": "no-és-una-clau"}]) == {}
