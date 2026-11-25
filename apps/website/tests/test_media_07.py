"""Fotos i fitxers de la web (T-M07-07; P-M07-C, RN-M07-05 i 14; CA-M07-05; P-489). WP1 i WP3,
amb la matriu inicial de la T-M07-02 (`core/0078`). Fitxers inventats."""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404

from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import media, pages
from apps.website.models import MediaAsset, Page

pytestmark = pytest.mark.django_db
R = Role.Code
# Un PNG vàlid de 8×8 px (inventat): en pujar-lo, se'n treuen les metadades.
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000080000000808020000004b6d29dc0000001149444154789c63908b"
    "eac18a18869604004abf41011d609a4f0000000049454e44ae426082"
)
COMPLETE = {"author": "Autora Inventada", "licence_note": "Cedida al club"}


@pytest.fixture
def editor(make_admin):  # noqa: F811
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


def test_the_president_has_wp3_too(make_admin):  # noqa: F811
    asset = _photo(make_admin(R.PRESIDENT), **COMPLETE)  # M07-4
    assert asset.publishable


def test_unknown_fields_are_a_programming_error(editor):
    with pytest.raises(ValueError):
        _photo(editor, status="retired")
    asset = _photo(editor, **COMPLETE)
    with pytest.raises(ValueError):
        media.update_details(asset, actor=editor, storage_key="un-altre")
    assert MediaAsset.objects.count() == 1


def test_a_failed_save_removes_the_stored_file(editor, monkeypatch):
    storage, stored = storages["private"], []
    real_save = storage.save

    def save(*args, **kwargs):
        stored.append(real_save(*args, **kwargs))
        return stored[-1]

    monkeypatch.setattr(storage, "save", save)

    def broken(*args, **kwargs):
        raise RuntimeError("base de dades no disponible")

    monkeypatch.setattr(MediaAsset, "save", broken)
    with pytest.raises(RuntimeError):
        _photo(editor, **COMPLETE)
    assert stored and not storage.exists(stored[0])


@pytest.mark.parametrize(
    "block", [{"kind": "image", "media": ["una", "llista"]}, {"kind": "gallery", "media": "una"}]
)
def test_an_image_block_carries_one_photo_and_a_gallery_a_list(editor, block):
    with pytest.raises(ValidationError):
        pages.publish_page(_page(editor), [block], editor)
    assert media.block_media_keys(["no és un bloc", {"kind": "text"}]) == []


def test_names_and_unknown_page_fields(editor):
    asset = _photo(editor, **COMPLETE)
    page = _page(editor)
    version = pages.publish_page(page, _image(asset), editor)
    assert (str(asset), str(page), str(version)) == ("Una barca", "Proves", "Proves v1")
    with pytest.raises(ValueError):
        pages.save_page(page, actor=editor, status="published")


# Un JPEG inventat amb EXIF (GPS i número de sèrie) i un comentari: SOI, APP1, COM, SOS i EOI.
EXIF = b"Exif\x00\x00GPS 41.38N 2.17E; serie INVENTADA-123"
JPEG = (
    b"\xff\xd8"
    + b"\xff\xe1" + (len(EXIF) + 2).to_bytes(2, "big") + EXIF
    + b"\xff\xfe\x00\x0cPropietari"
    + b"\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00" + b"\x12\x34\x56" + b"\xff\xd9"
)  # fmt: skip


def test_the_metadata_of_a_jpeg_is_removed_on_upload(editor):
    """Revisió de la #597: el fitxer desat (i servit) no porta GPS, número de sèrie ni propietari."""
    asset = _photo(editor, name="foto.jpg", content=JPEG, **COMPLETE)
    with media.open_content(asset) as handle:
        kept = handle.read()
    assert b"GPS" not in kept and b"INVENTADA" not in kept and b"Propietari" not in kept
    assert kept.startswith(b"\xff\xd8") and kept.endswith(b"\x12\x34\x56\xff\xd9")
    assert asset.size_bytes == len(kept)


def test_the_text_chunks_of_a_png_are_removed_on_upload(editor):
    text = b"tEXt" + b"Author\x00Persona Inventada"
    chunk = (len(text) - 4).to_bytes(4, "big") + text + b"\x00\x00\x00\x00"
    content = PNG[:33] + chunk + PNG[33:]  # després de l'IHDR
    asset = _photo(editor, content=content, **COMPLETE)
    with media.open_content(asset) as handle:
        assert handle.read() == PNG


def test_p633_webp_is_rejected_because_it_cannot_be_cleaned_without_a_new_library(editor):
    webp = b"RIFF\x1a\x00\x00\x00WEBPVP8 " + b"\x00" * 14
    with pytest.raises(ValidationError):
        _photo(editor, name="foto.webp", content=webp, **COMPLETE)
    assert not MediaAsset.objects.exists()
