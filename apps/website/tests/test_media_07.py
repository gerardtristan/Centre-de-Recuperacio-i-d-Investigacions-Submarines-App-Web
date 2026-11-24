"""Fotos i fitxers de la web (T-M07-07; P-M07-C, RN-M07-05 i 14; CA-M07-05; P-489). WP1 i WP3
són del catàleg del nucli (T-M07-02): aquí es declaren només per a la prova. Fitxers inventats."""

import pytest
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404

from apps.core import permissions
from apps.core.models import AuditEntry, Role, RolePermission
from apps.core.permission_catalog import CATALOG, Permission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import media, pages
from apps.website.models import MediaAsset, Page

pytestmark = pytest.mark.django_db
R = Role.Code
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
COMPLETE = {"author": "Autora Inventada", "licence_note": "Cedida al club"}


@pytest.fixture
def editor(monkeypatch, make_admin):  # noqa: F811
    extra = {
        code: Permission(code=code, ref=ref, description=code)
        for code, ref in ((pages.PERMISSION, "WP1"), (media.PERMISSION, "WP3"))
    }
    monkeypatch.setattr(permissions, "CATALOG", {**CATALOG, **extra})
    for code in extra:
        RolePermission.objects.create(
            role=Role.objects.get(code=R.ADMINISTRATOR), permission_code=code, scope="all"
        )
    return make_admin(R.ADMINISTRATOR)


def _photo(editor, *, name="foto.png", content=PNG, shows_people=False, **details):
    upload = SimpleUploadedFile(name, content)
    return media.upload(upload, actor=editor, alt_text="Una barca", shows_people=shows_people,
                        **details)  # fmt: skip


def _page(editor, slug="pagina-de-proves"):
    return pages.save_page(None, actor=editor, slug=slug, title="Proves")[0]


def _image(asset):
    return [{"kind": "image", "media": str(asset.key)}]


def test_upload_keeps_the_content_private_under_a_random_key(editor):
    asset = _photo(editor, name="nom-de-la-persona.png", **COMPLETE)
    assert "nom-de-la-persona" not in asset.storage_key
    assert asset.content_type == "image/png" and asset.size_bytes == len(PNG)
    with media.open_content(asset) as handle:
        assert handle.read() == PNG


@pytest.mark.parametrize(
    ("name", "content", "alt"),
    [
        ("doc.pdf", b"%PDF-1.7\n%inventat\n", "Un document"),
        ("foto.heic", b"\x00\x00\x00\x18ftypheic" + b"\x00" * 8, "Una foto"),
        ("foto.png", PNG, "   "),
    ],
)
def test_upload_rejects_non_web_images_and_a_missing_alt_text(editor, name, content, alt):
    with pytest.raises(ValidationError):
        media.upload(SimpleUploadedFile(name, content), actor=editor, alt_text=alt,
                     shows_people=False)  # fmt: skip
    assert not MediaAsset.objects.exists()


@pytest.mark.parametrize(
    "details",
    [
        {"licence_note": "Cedida al club"},
        {"author": "Autora Inventada"},
        {**COMPLETE, "shows_people": True},
    ],
)
def test_ca_m07_05_an_incomplete_photo_cannot_go_in_a_published_block(editor, details):
    asset = _photo(editor, **details)
    page = _page(editor)
    for blocks in (_image(asset), [{"kind": "gallery", "media": [str(asset.key)]}]):
        with pytest.raises(ValidationError):
            pages.publish_page(page, blocks, editor)
    assert not page.versions.exists()


@pytest.mark.parametrize("media_value", ["no-és-una-clau", "00000000-0000-0000-0000-000000000000"])
def test_an_unknown_photo_is_rejected(editor, media_value):
    with pytest.raises(ValidationError):
        pages.publish_page(_page(editor), [{"kind": "image", "media": media_value}], editor)


def test_with_people_and_their_consent_it_is_published_and_served(editor):
    asset = _photo(editor, shows_people=True, people_consent=True, **COMPLETE)
    pages.publish_page(_page(editor), _image(asset), editor)
    assert media.public_asset(str(asset.key)) == asset


def test_ca_m07_05_a_retired_photo_is_not_found_at_the_next_request(editor):
    asset = _photo(editor, **COMPLETE)
    pages.publish_page(_page(editor), _image(asset), editor)
    assert media.public_asset(str(asset.key)) == asset
    with pytest.raises(ValidationError):
        media.retire(asset, actor=editor, reason="  ")
    media.retire(asset, actor=editor, reason="Ho demana l'autora")
    media.retire(asset, actor=editor, reason="Una altra vegada")  # no canvia res
    with pytest.raises(Http404):
        media.public_asset(str(asset.key))
    entry = AuditEntry.objects.get(action=media.ACTION_RETIRED)
    assert (entry.old_value, entry.new_value, entry.reason) == (
        "active", "retired", "Ho demana l'autora",
    )  # fmt: skip
    with pytest.raises(ValidationError):  # ni es pot tornar a publicar
        pages.publish_page(_page(editor, "una-altra"), _image(asset), editor)


def test_only_photos_of_the_current_version_of_a_published_page_are_served(editor):
    shown, replaced, loose = (_photo(editor, **COMPLETE) for _ in range(3))
    page = _page(editor)
    pages.publish_page(page, _image(replaced), editor)
    pages.publish_page(page, _image(shown), editor)
    assert media.public_asset(str(shown.key)) == shown
    for asset in (replaced, loose):
        with pytest.raises(Http404):
            media.public_asset(str(asset.key))
    Page.objects.filter(pk=page.pk).update(status=Page.Status.RETIRED)
    for key in (str(shown.key), "no-és-una-clau", "00000000-0000-0000-0000-000000000000"):
        with pytest.raises(Http404):
            media.public_asset(key)


def test_completing_the_details_is_recorded_and_makes_it_publishable(editor):
    asset = _photo(editor, shows_people=True)
    asset = media.update_details(asset, actor=editor, people_consent=True, **COMPLETE)
    assert asset.publishable
    changes = AuditEntry.objects.filter(action=media.ACTION_CHANGED, target_id=str(asset.pk))
    assert {(e.field, e.old_value, e.new_value) for e in changes} == {
        ("people_consent", False, True),
        ("author", "", "Autora Inventada"),
        ("licence_note", "", "Cedida al club"),
    }
    media.retire(asset, actor=editor, reason="Prova")
    with pytest.raises(ValidationError):
        media.update_details(asset, actor=editor, credit="Club")


def test_a_role_without_wp3_gets_not_found(editor, make_admin):  # noqa: F811
    asset = _photo(editor, **COMPLETE)
    secretary = make_admin(R.SECRETARY)
    with pytest.raises(Http404):
        media.upload(SimpleUploadedFile("foto.png", PNG), actor=secretary, alt_text="x",
                     shows_people=False)  # fmt: skip
    with pytest.raises(Http404):
        media.retire(asset, actor=secretary, reason="Prova")
    assert MediaAsset.objects.get().status == MediaAsset.Status.ACTIVE


def test_until_t_m07_02_nobody_can_upload(make_admin):  # noqa: F811
    with pytest.raises(ImproperlyConfigured):
        media.upload(SimpleUploadedFile("foto.png", PNG), actor=make_admin(R.ADMINISTRATOR),
                     alt_text="x", shows_people=False)  # fmt: skip
