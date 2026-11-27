"""Catàleg de blocs (T-M07-04 i decisió 106; RN-M07-10 i 15; CA-M07-23 i 24). WP1 i WP3 amb la
matriu inicial de la T-M07-02. Només dades inventades."""

import uuid

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.core import business_settings
from apps.core.models import Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import blocks, media, pages
from apps.website.models import PageVersion
from apps.website.tests.test_media_07 import COMPLETE, _photo

pytestmark = pytest.mark.django_db
KEY = str(uuid.UUID(int=2**128 - 1))  # una clau inventada (només l'esquema)
MD = "Text **inventat** amb [un enllaç](https://exemple.cat)."

# Un bloc complet de cada tipus de la taula «Catàleg de blocs» de l'addenda de la 106.
VALID = {
    "heading": {"text": "Qui som", "level": 2},
    "text": {"title": "Benvinguts", "body": MD, "width": "wide"},
    "quote": {"text": "El mar ens uneix.", "attribution": "Sòcia inventada",
              "background": "soft"},
    "list": {"items": ["Primer", "Segon"], "style": "checks"},
    "disclosure": {"question": "Cal títol?", "answer": MD},
    "callout": {"body": MD, "tone": "warning"},
    "image": {"media": KEY, "caption": "Una barca", "width": "full"},
    "gallery": {"media": [KEY, KEY], "columns": 4},
    "image_text": {"media": KEY, "title": "El centre", "body": MD, "image_side": "right",
                   "background": "marine"},
    "video": {"source": "youtube", "youtube_id": "dQw4w9WgXcQ", "title": "Immersió"},
    "file": {"file": KEY, "label": "Calendari (PDF)"},
    "section": {"columns": [[{"kind": "heading", "text": "A", "level": 3}], []],
                "background": "accent"},
    "divider": {},
    "spacer": {"size": "large"},
    "button": {"label": "Inscriu-t'hi", "target": "/formacio/", "style": "primary"},
    "join_cta": {"title": "Fes-te soci", "body": MD, "background": "accent"},
    "newsletter": {"title": "Butlletí"},
    "contact_form": {},
    "upcoming_activities": {"title": "Properes", "filters": {"type": "sortida"}, "count": 6,
                            "layout": "cards"},
    "featured_activities": {"title": "Destacades"},
    "past_activities": {"title": "Fetes", "count": 12, "layout": "list"},
    "recent_news": {"title": "Notícies", "count": 3},
    "faq_topic": {"topic": 3},
    "key_figures": {"items": [{"value": "70", "label": "anys"},
                              {"value": "300", "label": "socis"}]},
    "project_cards": {"items": [{"title": "Posidònia", "body": MD, "media": KEY,
                                 "target": "https://exemple.cat/projecte"}], "columns": 3},
    "featured_trip": {"activity": 7, "background": "none"},
}  # fmt: skip


def block(kind, **changes):
    return {"kind": kind, **VALID[kind], **changes}


@pytest.fixture
def editor(make_admin):  # noqa: F811
    return make_admin(Role.Code.ADMINISTRATOR)


@pytest.fixture
def page(editor):
    return pages.save_page(None, actor=editor, slug="blocs-inventats", title="Blocs")[0]


def test_the_catalog_has_the_26_kinds_of_the_addendum():
    assert set(blocks.CATALOG) == set(VALID) and len(VALID) == 26


@pytest.mark.parametrize("kind", VALID)
def test_rn_m07_15_a_complete_block_of_each_kind_is_valid_also_hidden(kind):
    blocks.validate([block(kind), block(kind, hidden=True)], publishing=True)


@pytest.mark.parametrize(
    "bad",
    [
        block("text", colour="red"),  # camp fora d'esquema
        block("text", width="gegant"),  # variant fora de la llista
        block("gallery", columns=5),
        block("heading", level=1),  # l'h1 és el títol de la pàgina
        block("heading", level="2"),
        block("heading", text="T" * 121),
        block("list", items=["x"] * 21),
        block("upcoming_activities", count=7),  # més que `website.home_activities_count`
        block("past_activities", count=13),
        block("key_figures", items=[{"value": "1", "label": "x", "extra": "no"}] * 2),
        block("section", columns=[[block("section")]]),  # cap secció dins d'una secció
        block("section", columns=[[], [], [], []]),
        block("image", media="no-és-una-clau"),
        block("image", media=KEY.upper()),
        block("video", youtube_id="curt"),
        block("button", target="http://exemple.cat"),
        block("button", target="javascript:alert(1)"),
        block("button", target="//exemple.cat"),
        block("upcoming_activities", filters={"persona": "x"}),
        block("text", hidden="sí"),
        {"kind": "script"},
        {"text": "sense tipus"},
        "text",
    ],
)
def test_ca_m07_23_out_of_schema_is_rejected_on_save_and_publish(page, editor, bad):
    for publishing in (False, True):
        with pytest.raises(ValidationError):
            blocks.validate([bad], publishing=publishing)
    with pytest.raises(ValidationError):
        pages.publish_page(page, [block("divider"), bad], editor)
    assert not PageVersion.objects.exists()


def test_the_list_itself_must_be_a_list():
    with pytest.raises(ValidationError):
        blocks.validate({"kind": "text"}, publishing=False)


@pytest.mark.parametrize(
    "unfinished",
    [
        {"kind": "text"},
        {"kind": "image", "media": ""},
        block("gallery", media=[KEY]),
        block("list", items=["", "Segon"]),
        block("video", youtube_id=""),
        block("video", source="own"),
        block("key_figures", items=[{"value": "", "label": "x"}, {"value": "1", "label": "y"}]),
        block("section", columns=[]),
    ],
)
def test_p680_an_unfinished_block_can_be_drafted_but_not_published(unfinished):
    blocks.validate([unfinished], publishing=False)
    with pytest.raises(ValidationError):
        blocks.validate([unfinished], publishing=True)


def test_the_count_limit_follows_the_setting(editor):
    business_settings.change("website.home_activities_count", 8, editor, "Prova")
    blocks.validate([block("upcoming_activities", count=8)], publishing=True)


@pytest.mark.parametrize(
    ("source", "html"),
    [
        ("<script>alert(1)</script>", "<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>\n"),
        ("[x](javascript:alert(1))", "<p>[x](javascript:alert(1))</p>\n"),
        ("[enllaç](https://exemple.cat)", '<p><a href="https://exemple.cat">enllaç</a></p>\n'),
    ],
)
def test_ca_m07_24_script_escaped_javascript_as_text_and_https_as_a_link(source, html):
    assert blocks.render_markdown(source) == html


def test_rn_m07_10_only_the_allowed_formats_and_link_schemes():
    html = blocks.render_markdown(
        "# Un\n\n#### Dos\n\n*i* **b** ![foto](https://x.cat/f.png) [c](mailto:a@exemple.cat) "
        "[t](tel:+34930000000) [p](/qui-som/) [n](//exemple.cat) [h](http://exemple.cat) "
        "<b>x</b>\n\n- a\n\n1. b"
    )
    assert html.startswith("<h2>Un</h2>\n<h3>Dos</h3>\n")
    assert "<em>i</em> <strong>b</strong>" in html and "<img" not in html
    for href in ("mailto:a@exemple.cat", "tel:+34930000000", "/qui-som/"):
        assert f'href="{href}"' in html
    assert "[n](//exemple.cat) [h](http://exemple.cat) &lt;b&gt;x&lt;/b&gt;" in html
    assert "<ul>\n<li>a</li>\n</ul>\n<ol>\n<li>b</li>\n</ol>" in html
    assert blocks.render_markdown(None) == ""


LEGACY = [
    {"kind": "text", "title": "Hola", "text": "Text antic."},
    {"kind": "activities", "filters": {"type": "curs"}},
    {"kind": "news"},
    {"kind": "faq", "topic": 3},
    {"kind": "join_button"},
    {"kind": "contact_form"},
]


def test_the_initial_kinds_are_translated_on_reading_and_validate():
    upgraded = blocks.upgrade_all(LEGACY)
    assert [b["kind"] for b in upgraded] == [
        "text", "upcoming_activities", "recent_news", "faq_topic", "join_cta", "contact_form",
    ]  # fmt: skip
    assert upgraded[0] == {"kind": "text", "title": "Hola", "body": "Text antic."}
    assert upgraded[1]["filters"] == {"type": "curs"} and upgraded[1]["count"] == 6
    assert upgraded[2]["count"] == 3
    blocks.validate(upgraded, publishing=True)
    assert blocks.upgrade_all(upgraded) == upgraded  # el catàleg nou no es toca


def test_reverting_a_version_with_initial_kinds_publishes_them_translated(page, editor):
    """Les versions són només d'INSERT: l'antiga es queda tal com es va desar."""
    old = PageVersion.objects.create(page=page, number=1, blocks=LEGACY, published_by=editor)
    new = pages.revert_to(old, editor)
    assert new.blocks == blocks.upgrade_all(LEGACY)
    old.refresh_from_db()
    assert old.blocks == LEGACY


def test_photos_inside_sections_and_cards_are_checked_and_hidden_ones_are_not_served(page, editor):
    ready, hidden = _photo(editor, **COMPLETE), _photo(editor, **COMPLETE)
    incomplete = _photo(editor)
    nested = block("section", columns=[[block("image_text", media=str(incomplete.key))]])
    with pytest.raises(ValidationError):
        pages.publish_page(page, [nested], editor)
    shown = block("project_cards", items=[{**VALID["project_cards"]["items"][0],
                                           "media": str(ready.key)}])  # fmt: skip
    hidden_block = block("image", media=str(hidden.key), hidden=True)
    pages.publish_page(page, [block("section", columns=[[shown]]), hidden_block], editor)
    assert media.public_asset(str(ready.key)) == ready
    with pytest.raises(Http404):
        media.public_asset(str(hidden.key))


def test_the_editor_settings_start_as_the_addendum_says():
    settings = {s.key: s for s in Setting.objects.filter(key__in=[
        "website.youtube_enabled", "website.review_flow_enabled", "website.autosave_seconds",
        "website.upload_max_mb",
    ])}  # fmt: skip
    assert {k: (s.initial_value, s.min_value, s.max_value) for k, s in settings.items()} == {
        "website.youtube_enabled": (False, None, None),
        "website.review_flow_enabled": (False, None, None),
        "website.autosave_seconds": (20, 5, 120),
        "website.upload_max_mb": (10, 1, 25),
    }
