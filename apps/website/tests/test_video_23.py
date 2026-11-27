"""Bloc de vídeo de YouTube (T-M07-23, decisió 106; RN-M07-09 i CA-M07-25). La prova al navegador
que no hi ha cap petició a Google abans del clic és a `core/tests/e2e/test_editor_web.py`. Cap
petició real a la xarxa: la baixada de la miniatura se substitueix. Només dades inventades."""

import io

import pytest
from django.urls import reverse

from apps.core import business_settings
from apps.core.models import Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website import editor, pages, render, video
from apps.website.models import MediaAsset, PageDraft
from apps.website.tests.test_blocks_106 import block
from apps.website.tests.test_media_07 import PNG

pytestmark = pytest.mark.django_db
YOUTUBE = block("video", title="Immersió inventada")  # source youtube, youtube_id d'11


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin(Role.Code.ADMINISTRATOR)


@pytest.fixture
def page(admin):
    return pages.save_page(None, actor=admin, slug="video-inventat", title="Vídeo")[0]


@pytest.fixture
def youtube_on():
    # Sense permís al catàleg encara (torn del nucli): s'encén directament per a la prova.
    Setting.objects.filter(key=video.ENABLED).update(initial_value=True)


@pytest.fixture
def downloads(monkeypatch):
    calls = []

    def fake(youtube_id):
        calls.append(youtube_id)
        return PNG

    monkeypatch.setattr(video, "_download", fake)
    return calls


def test_the_notice_is_a_setting_and_youtube_starts_off():
    assert business_settings.get(video.NOTICE) == "En prémer, es carrega YouTube (Google)"
    assert business_settings.get(video.ENABLED) is False


def test_with_youtube_off_nothing_is_downloaded_and_the_block_does_not_show(page, admin, downloads):
    assert video.with_thumbnail(YOUTUBE, admin) == YOUTUBE and downloads == []
    assert render.render_blocks([YOUTUBE], page) == ""


def test_ca_m07_25_before_the_click_the_page_asks_nothing_of_google(page, youtube_on):
    html = render.render_blocks([YOUTUBE], page)
    assert 'data-embed="https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?autoplay=1"' in html
    assert "En prémer, es carrega YouTube (Google)" in html
    for host in ("<iframe", "ytimg", "google", "www.youtube.com", "gstatic"):
        assert host not in html
    assert render.render_blocks([block("video", source="own", title="Propi")], page) == ""


def test_the_thumbnail_is_stored_by_the_server_and_waits_for_a_review(admin, youtube_on, downloads):
    new = video.with_thumbnail(YOUTUBE, admin)
    asset = MediaAsset.objects.get()
    assert new == {**YOUTUBE, "thumbnail": str(asset.key)} and downloads == ["dQw4w9WgXcQ"]
    assert asset.alt_text == "Immersió inventada" and asset.shows_people
    assert not asset.publishable  # P-685: fins que WP3 confirma les persones
    assert video.with_thumbnail(new, admin) == new and len(downloads) == 1


@pytest.mark.parametrize("content", [None, b"no es una imatge"])
def test_without_a_valid_thumbnail_the_block_is_kept(admin, youtube_on, monkeypatch, content):
    monkeypatch.setattr(video, "_download", lambda youtube_id: content)
    assert video.with_thumbnail(YOUTUBE, admin) == YOUTUBE
    assert video.with_thumbnail(block("text"), admin) == block("text")
    assert not MediaAsset.objects.exists()


def test_the_download_goes_only_to_the_thumbnail_address(monkeypatch):
    opened = []

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_open(url, timeout):
        opened.append((url, timeout))
        return Response(PNG)

    monkeypatch.setattr(video.urllib.request, "urlopen", fake_open)
    assert video._download("dQw4w9WgXcQ") == PNG
    assert opened == [("https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg", 5)]

    def broken(url, timeout):
        raise OSError("sense xarxa")

    monkeypatch.setattr(video.urllib.request, "urlopen", broken)
    assert video._download("dQw4w9WgXcQ") is None


def test_saving_a_video_block_in_the_editor_stores_the_thumbnail(
    page, admin, youtube_on, downloads
):
    draft = pages.save_draft(page, [block("video", title="")], admin)
    data = {"action": "update", "index": "0", "source": "youtube", "youtube_id": "dQw4w9WgXcQ",
            "title": "Immersió inventada", "width": "normal", "revision": str(draft.revision),
            "base": editor.fingerprint(draft.blocks[0])}  # fmt: skip
    admin_client(admin).post(reverse("administration:website_page_editor_action", args=[page.pk]),
                             data)  # fmt: skip
    saved = PageDraft.objects.get().blocks[0]
    assert saved["thumbnail"] == str(MediaAsset.objects.get().key)
