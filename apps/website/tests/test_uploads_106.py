"""Pujades de la web (T-M07-07b; RN-M07-19 de l'addenda M07 de la 106, amb la P-633 A de la 108;
CA-M07-28): només JPEG i PNG (i PDF), comprovades pel contingut i tornades a codificar sense EXIF
ni GPS; mida màxima; PDF com a descàrrega; punt focal i mides en WebP. Fitxers inventats."""

import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.core.models import Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import media, pages
from apps.website.models import MediaAsset, Page, PageVersion

pytestmark = pytest.mark.django_db
COMPLETE = {"author": "Autora Inventada", "licence_note": "Cedida al club"}
GPS_IFD = 0x8825


@pytest.fixture
def editor(make_admin):  # noqa: F811
    return make_admin(Role.Code.ADMINISTRATOR)


def picture(fmt="JPEG", size=(1000, 600), gps=True) -> bytes:
    exif = Image.Exif()
    exif[0x010F] = "Fabricant inventat"
    if gps:
        exif.get_ifd(GPS_IFD)[1] = "N"
        exif.get_ifd(GPS_IFD)[2] = (41.0, 23.0, 0.0)
    out = io.BytesIO()
    Image.new("RGB", size, (30, 90, 140)).save(out, fmt, exif=exif)
    return out.getvalue()


def upload(editor, name, content, **details):
    return media.upload(SimpleUploadedFile(name, content), actor=editor, alt_text="Una barca",
                        shows_people=False, **{**COMPLETE, **details})  # fmt: skip


def stored(asset, width=""):
    with media.open_content(asset, width) as handle:
        return handle.read()


def test_ca_m07_28_a_jpeg_with_gps_is_stored_without_exif_or_gps(editor):
    source = picture()
    assert Image.open(io.BytesIO(source)).getexif().get_ifd(GPS_IFD)  # la prova és vàlida
    asset = upload(editor, "foto.jpg", source)
    image = Image.open(io.BytesIO(stored(asset)))
    assert image.format == "JPEG" and not image.getexif()
    assert b"Fabricant inventat" not in stored(asset)


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("dibuix.svg", b'<svg xmlns="http://www.w3.org/2000/svg"><script>x()</script></svg>'),
        ("dibuix.png", b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'),  # extensió falsa
        ("foto.jpg", picture("PNG")),  # PNG amb extensió de JPEG
        ("foto.png", b"\x89PNG\r\n\x1a\n" + b"no es cap imatge" * 10),  # capçalera sola
        ("foto.webp", picture("WEBP")),  # P-633 A (108): cap WebP
    ],
)
def test_ca_m07_28_svg_false_extensions_broken_images_and_webp_are_rejected(editor, name, content):
    with pytest.raises(ValidationError):
        upload(editor, name, content)
    assert not MediaAsset.objects.exists()


def test_the_size_limit_is_the_setting_with_a_fallback_of_10_mb(editor, monkeypatch):
    content = picture(size=(200, 100))
    monkeypatch.setattr(media, "MAX_MB_FALLBACK", len(content) / (1024 * 1024) / 2)
    if Setting.objects.filter(key=media.MAX_MB_KEY).exists():  # quan el carril E creï la clau
        Setting.objects.filter(key=media.MAX_MB_KEY).update(initial_value=0)
    with pytest.raises(ValidationError):
        upload(editor, "foto.jpg", content)
    assert not MediaAsset.objects.exists()


def test_webp_sizes_smaller_than_the_original_are_stored_and_served(editor, client):
    asset = upload(editor, "foto.jpg", picture(size=(1000, 600)))
    assert set(asset.renditions) == {"480", "960"}
    small = Image.open(io.BytesIO(stored(asset, "480")))
    assert small.format == "WEBP" and small.size == (480, 288) and not small.getexif()
    assert upload(editor, "petita.png", picture("PNG", size=(300, 200))).renditions == {}
    Setting.objects.filter(key="website.public_images_enabled").update(initial_value=True)
    pages.publish_page(
        pages.save_page(None, actor=editor, slug="proves", title="Proves")[0],
        [{"kind": "image", "media": str(asset.key)}], editor,
    )  # fmt: skip
    response = client.get(f"/web/fotos/{asset.key}/?w=480")
    assert response["Content-Type"] == "image/webp"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert client.get(f"/web/fotos/{asset.key}/?w=123")["Content-Type"] == "image/jpeg"


def test_a_failed_save_removes_the_sizes_too(editor, monkeypatch):
    storage, saved = storages["private"], []
    real_save = storage.save
    monkeypatch.setattr(
        storage, "save", lambda *a, **k: saved.append(real_save(*a, **k)) or saved[-1]
    )

    def broken(*args, **kwargs):
        raise RuntimeError("base de dades no disponible")

    monkeypatch.setattr(MediaAsset, "save", broken)
    with pytest.raises(RuntimeError):
        upload(editor, "foto.jpg", picture())
    assert len(saved) == 3 and not any(storage.exists(key) for key in saved)


def test_the_focal_point_is_a_detail_with_the_previous_value_recorded(editor):
    asset = upload(editor, "foto.jpg", picture(gps=False))
    assert (asset.focal_x, asset.focal_y) == (50, 50)
    asset = media.update_details(asset, actor=editor, focal_x=20, focal_y=80)
    assert (asset.focal_x, asset.focal_y) == (20, 80)
    with pytest.raises(ValidationError):
        media.update_details(asset, actor=editor, focal_x=101)


def test_rn_m07_19_a_pdf_is_served_only_as_a_download(editor, client):
    Setting.objects.filter(key="website.public_images_enabled").update(initial_value=True)
    pdf = upload(editor, "horari.pdf", b"%PDF-1.7\n%inventat\n")
    assert pdf.content_type == "application/pdf" and pdf.renditions == {}
    page = pages.save_page(None, actor=editor, slug="documents", title="Documents")[0]
    # El bloc «file» del catàleg de la 106 el porta la T-M07-04: aquí la versió es crea directa.
    PageVersion.objects.create(
        page=page, number=1, blocks=[{"kind": "file", "file": str(pdf.key)}], published_by=editor
    )
    Page.objects.filter(pk=page.pk).update(status=Page.Status.PUBLISHED)
    response = client.get(f"/web/fotos/{pdf.key}/")
    assert response.status_code == 200
    assert response["Content-Disposition"].startswith("attachment")
    assert response["Content-Type"] == "application/pdf"
    assert response["X-Content-Type-Options"] == "nosniff"
