"""Bloc de vídeo de YouTube (T-M07-23, decisió 106; RN-M07-09 i CA-M07-25). La prova al navegador
que no hi ha cap petició a Google abans del clic és a `core/tests/e2e/test_editor_web.py`. Cap
petició real a la xarxa: la baixada de la miniatura se substitueix. Només dades inventades."""

import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.urls import reverse

from apps.core import business_settings
from apps.core.models import Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website import editor, media, pages, render, video
from apps.website.models import MediaAsset, PageDraft
from apps.website.tests.test_blocks_106 import block
from apps.website.tests.test_media_07 import COMPLETE, PNG

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

    monkeypatch.setattr(video._opener, "open", fake_open)
    assert video._download("dQw4w9WgXcQ") == PNG
    assert opened == [("https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg", 5)]

    def broken(url, timeout):
        raise OSError("sense xarxa")

    monkeypatch.setattr(video._opener, "open", broken)
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


MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64  # una capçalera MP4 inventada


@pytest.fixture
def video_uploads_on():
    # Sense permís al catàleg (torn del nucli) i apagat a producció (P-610): només a la prova.
    Setting.objects.filter(key=media.VIDEO_UPLOADS).update(initial_value=True)


def _mp4(content=MP4, name="video.mp4"):
    return SimpleUploadedFile(name, content)


def test_rn_m07_26_video_uploads_start_off(admin):
    with pytest.raises(ValidationError):
        media.upload_video(_mp4(), actor=admin, alt_text="Vídeo", shows_people=False)
    assert not MediaAsset.objects.exists()


@pytest.mark.parametrize("content", [PNG, b"\x00\x00\x00\x18ftypqt  " + b"\x00" * 8])
def test_rn_m07_26_only_mp4_by_its_content(admin, video_uploads_on, content):
    with pytest.raises(ValidationError):
        media.upload_video(_mp4(content), actor=admin, alt_text="Vídeo", shows_people=False)


def test_rn_m07_26_a_video_over_the_size_limit_is_rejected(admin, video_uploads_on):
    Setting.objects.filter(key="website.upload_max_mb").update(initial_value=1)
    with pytest.raises(ValidationError):
        media.upload_video(_mp4(MP4 + b"\x00" * 1024 * 1024), actor=admin, alt_text="Vídeo",
                           shows_people=False)  # fmt: skip


def test_rn_m07_26_an_own_video_is_shown_when_it_can_be_published(page, admin, video_uploads_on):
    asset = media.upload_video(_mp4(), actor=admin, alt_text="Immersió", shows_people=False)
    own = block("video", source="own", video=str(asset.key), title="Propi")
    assert asset.content_type == "video/mp4" and render.render_blocks([own], page) == ""
    with pytest.raises(ValidationError):  # sense autor ni permís, no es pot publicar
        pages.publish_page(page, [own], admin)
    media.update_details(asset, actor=admin, **COMPLETE)
    assert render.render_blocks([own], page) == ""  # com les fotos, amb les imatges públiques
    business_settings.change("website.public_images_enabled", True, admin, "Prova")
    html = render.render_blocks([own], page)
    assert f'src="/web/fotos/{asset.key}/"' in html and "<video" in html


def test_review_saving_twice_keeps_the_same_thumbnail(page, admin, youtube_on, downloads):
    """Revisió de la 23: el segon desat no torna a baixar la miniatura ni en crea una altra."""
    url = reverse("administration:website_page_editor_action", args=[page.pk])
    pages.save_draft(page, [block("video", title="")], admin)
    for title in ("Primer", "Segon"):
        blocks_, revision = pages.draft_state(page)
        admin_client(admin).post(url, {
            "action": "update", "index": "0", "source": "youtube", "youtube_id": "dQw4w9WgXcQ",
            "title": title, "width": "normal", "revision": str(revision),
            "base": editor.fingerprint(blocks_[0]),
        })  # fmt: skip
    assert MediaAsset.objects.count() == 1 and len(downloads) == 1
    assert PageDraft.objects.get().blocks[0]["title"] == "Segon"


def test_review_an_invalid_id_is_never_requested(admin, youtube_on, downloads):
    assert video.with_thumbnail(block("video", youtube_id="../../x?y=1"), admin)["kind"] == "video"
    assert downloads == []


def test_review_no_redirects_and_nothing_at_the_size_limit(monkeypatch):
    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        video._opener, "open", lambda url, timeout: Response(b"x" * (video.MAX_BYTES + 1))
    )
    assert video._download("dQw4w9WgXcQ") is None
    assert video._NoRedirect().redirect_request(None, None, 302, "", {}, "https://x") is None
    assert not any(
        isinstance(h, video.urllib.request.HTTPRedirectHandler)
        and not isinstance(h, video._NoRedirect)
        for h in video._opener.handlers
    )


def test_review_storing_an_image_needs_wp3(make_admin):  # noqa: F811
    with pytest.raises(Http404):
        media.store_image(PNG, actor=make_admin(Role.Code.SECRETARY), alt_text="x",
                          shows_people=False)  # fmt: skip
