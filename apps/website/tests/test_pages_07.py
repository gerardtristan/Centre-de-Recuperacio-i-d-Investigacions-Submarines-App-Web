"""Pàgines, versions i blocs (T-M07-04; RN-M07-03, 13 i 14; CA-M07-03, 19 i 22). WP1 és del
catàleg del nucli (T-M07-02): aquí es declara només per a la prova. Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.db import Error, connection, transaction
from django.http import Http404

from apps.core.models import AppendOnlyError, AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import pages
from apps.website.models import Page, PageVersion
from apps.website.routes import route_taken

pytestmark = pytest.mark.django_db
R = Role.Code
TEXT = [{"kind": "text", "title": "Benvinguts", "text": "Text inventat."}]


@pytest.fixture
def editor(make_admin):  # noqa: F811
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def page(editor):
    return pages.save_page(None, actor=editor, slug="prova-inventada", title="Prova")[0]


def test_the_initial_pages_are_drafts_without_content_or_route_clash():
    initial = Page.objects.all()
    assert [p.slug for p in initial] == [
        "qui-som", "el-centre", "historia", "formacio", "sortides", "medi-ambient",
        "projectes", "galeria",
    ]  # fmt: skip
    assert {p.status for p in initial} == {Page.Status.DRAFT}
    assert not PageVersion.objects.exists()
    assert not any(route_taken(p.slug) for p in initial)


def test_ca_m07_03_revert_publishes_a_copy_and_no_version_changes(page, editor):
    pages.publish_page(page, TEXT, editor, "Primera")
    second = pages.publish_page(page, TEXT + [{"kind": "join_button"}], editor, "Segona")
    before = list(PageVersion.objects.values())
    pages.publish_page(page, [{"kind": "text", "text": "Canvi"}], editor, "Tercera")
    fourth = pages.revert_to(second, editor)
    assert list(page.versions.values_list("number", flat=True)) == [1, 2, 3, 4]
    assert fourth.number == 4 and fourth.blocks == second.blocks
    assert fourth.note == "Torna a la versió 2"
    assert list(PageVersion.objects.filter(number__lte=2).values()) == before
    assert pages.current_version(page) == fourth
    page.refresh_from_db()
    assert page.status == Page.Status.PUBLISHED


def test_rn_m07_14_publishing_is_recorded_with_the_previous_version(page, editor):
    pages.publish_page(page, TEXT, editor, "Primera")
    pages.publish_page(page, TEXT, editor, "Segona")
    entries = AuditEntry.objects.filter(action=pages.ACTION_PUBLISHED).order_by("pk")
    assert [(e.old_value, e.new_value, e.reason) for e in entries] == [
        (None, 1, "Primera"), (1, 2, "Segona"),
    ]  # fmt: skip
    assert {e.actor_account_id for e in entries} == {editor.pk}


def test_versions_are_append_only_in_the_orm_and_the_database(page, editor):
    version = pages.publish_page(page, TEXT, editor)
    version.note = "canviada"
    with pytest.raises(AppendOnlyError):
        version.save()
    for sql in ("UPDATE website_pageversion SET note = 'x'", "DELETE FROM website_pageversion"):
        with pytest.raises(Error), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(sql)
    assert PageVersion.objects.get().note == ""


@pytest.mark.parametrize(
    "fields",
    [{"template": "revista"}, {"accent": "vermell"}, {"slug": "en-construccio"}, {"slug": "No!"}],
)
def test_ca_m07_19_out_of_list_or_existing_route_is_rejected(editor, fields):
    with pytest.raises(ValidationError):
        pages.save_page(None, actor=editor, **{"slug": "nova", "title": "Nova", **fields})
    assert not Page.objects.filter(title="Nova").exists()


def test_ca_m07_22_long_share_texts_are_saved_with_a_warning(page, editor):
    page, warnings = pages.save_page(page, actor=editor, share_title="T" * 70)
    page.refresh_from_db()
    assert page.share_title == "T" * 70
    assert len(warnings) == 1 and "60" in warnings[0]
    _page, warnings = pages.save_page(page, actor=editor, share_description="D" * 151)
    assert len(warnings) == 2
    _page, warnings = pages.save_page(page, actor=editor, share_title="T" * 60,
                                      share_description="D" * 150)  # fmt: skip
    assert warnings == []


@pytest.mark.parametrize(
    "blocks",
    [
        {"kind": "text"},
        [{"kind": "script"}],
        [{"kind": "news", "text": "de més"}],
        [{"kind": "text", "text": ["no"]}],
        ["text"],
    ],
)
def test_blocks_out_of_the_closed_list_are_rejected(page, editor, blocks):
    with pytest.raises(ValidationError):
        pages.publish_page(page, blocks, editor)
    assert not PageVersion.objects.exists()


def test_text_is_stored_as_written(page, editor):
    """RN-M07-10: no es neteja ni es converteix; l'escapa la plantilla (CA-M07-13, T-M07-05)."""
    blocks = [{"kind": "text", "text": "<script>alert(1)</script>"}]
    assert pages.publish_page(page, blocks, editor).blocks == blocks


def test_a_role_without_wp1_gets_not_found_and_nothing_is_saved(page, make_admin):  # noqa: F811
    secretary = make_admin(R.SECRETARY)
    with pytest.raises(Http404):
        pages.save_page(None, actor=secretary, slug="nova", title="Nova")
    with pytest.raises(Http404):
        pages.publish_page(page, TEXT, secretary)
    assert not Page.objects.filter(slug="nova").exists()
    assert not PageVersion.objects.exists()
