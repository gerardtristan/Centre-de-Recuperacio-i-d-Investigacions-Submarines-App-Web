"""Vista prèvia, desat automàtic, avís d'edició simultània, compartir, publicar i tornar a una
versió (T-M07-06b, decisió 106; RN-M07-13, 16 i 23; HU-M07-02; CA-M07-20 i 32). WP1 amb la matriu
inicial de la T-M07-02. Només dades inventades."""

import datetime

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.core import business_settings
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website import editor, pages
from apps.website.models import PageDraft, PageEditing, PageVersion
from apps.website.tests.test_blocks_106 import block
from apps.website.tests.test_media_07 import COMPLETE, _photo

pytestmark = pytest.mark.django_db
R = Role.Code
H1, H2 = block("heading", text="Un"), block("heading", text="Dos")


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def page(admin):
    page = pages.save_page(None, actor=admin, slug="previa-inventada", title="Prèvia")[0]
    pages.save_draft(page, [H1, block("quote", text="Amagada", hidden=True), H2], admin)
    return page


def url(name, page, *args):
    return reverse(f"administration:website_page_{name}", args=[page.pk, *args])


def test_rn_m07_23_the_preview_needs_session_and_wp1(page, admin, make_admin):  # noqa: F811
    response = admin_client(admin).get(url("preview", page) + "?tema=fosc")
    html = response.content.decode()
    assert response["X-Frame-Options"] == "SAMEORIGIN" and 'data-theme="dark"' in html
    assert '<div data-bloc="0">' in html and '<div data-bloc="2">' in html
    assert "Amagada" not in html and 'data-bloc="1"' not in html
    assert admin_client(make_admin(R.SECRETARY)).get(url("preview", page)).status_code == 404
    assert Client().get(url("preview", page)).status_code == 302  # a entrar, mai pública


def test_the_preview_only_shows_photos_already_served(page, admin):
    business_settings.change("website.public_images_enabled", True, admin, "Prova")
    asset = _photo(admin, **COMPLETE)
    pages.save_draft(page, [block("image", media=str(asset.key))], admin)
    client = admin_client(admin)
    # Fins que hi hagi la vista de fotos amb sessió (torn del nucli), només les ja servides.
    assert "<img" not in client.get(url("preview", page)).content.decode()
    other = pages.save_page(None, actor=admin, slug="ja-publicada", title="Publicada")[0]
    pages.publish_page(other, [block("image", media=str(asset.key))], admin)
    assert "<img" in client.get(url("preview", page)).content.decode()


def test_ca_m07_32_the_second_person_sees_the_notice(page, admin, make_admin):  # noqa: F811
    president = make_admin(R.PRESIDENT)
    admin_client(admin).get(reverse("administration:website_page_editor", args=[page.pk]))
    response = admin_client(president).get(
        reverse("administration:website_page_editor", args=[page.pk])
    )
    assert admin.login in response.content.decode()
    assert admin_client(admin).post(url("autosave", page)).json() == {"others": [president.login]}
    old = timezone.now() - datetime.timedelta(minutes=5)
    PageEditing.objects.filter(account=president).update(seen_at=old)
    assert admin_client(admin).post(url("autosave", page)).json() == {"others": []}


def test_ca_m07_32_autosave_does_not_overwrite_someone_elses_block(page, admin, make_admin):  # noqa: F811
    client = admin_client(admin)
    base = editor.fingerprint(H1)
    data = {"index": "0", "base": base, "text": "Un (A)", "level": "2"}
    response = client.post(url("autosave", page), data)
    assert response.status_code == 200
    assert PageDraft.objects.get().blocks[0]["text"] == "Un (A)"
    assert response.json()["base"] == editor.fingerprint(PageDraft.objects.get().blocks[0])
    # Una altra persona hi afegeix un bloc al davant: el formulari antic ja no és d'aquest bloc.
    pages.save_draft(page, [H2, *PageDraft.objects.get().blocks], make_admin(R.PRESIDENT))
    before = PageDraft.objects.get().blocks
    response = client.post(url("autosave", page), {**data, "base": response.json()["base"]})
    assert response.status_code == 409 and response.json()["error"]
    assert PageDraft.objects.get().blocks == before
    invalid = client.post(url("autosave", page), {"index": "0", "text": "T" * 121, "level": "2"})
    assert invalid.status_code == 400 and PageDraft.objects.get().blocks == before


def test_ca_m07_20_publish_and_revert_are_recorded_and_the_draft_follows(page, admin):
    client = admin_client(admin)
    client.post(url("publish", page), {"note": "Primera"})
    assert not PageDraft.objects.exists() and PageVersion.objects.get().blocks == [
        H1, block("quote", text="Amagada", hidden=True), H2,
    ]  # fmt: skip
    pages.save_draft(page, [H2], admin)
    client.post(url("publish", page))
    client.post(url("revert", page, 1))
    versions = list(page.versions.order_by("number"))
    assert [v.number for v in versions] == [1, 2, 3] and versions[2].blocks == versions[0].blocks
    assert PageDraft.objects.get().blocks == versions[0].blocks
    entries = AuditEntry.objects.filter(action=pages.ACTION_PUBLISHED).order_by("pk")
    assert [(e.old_value, e.new_value) for e in entries] == [(None, 1), (1, 2), (2, 3)]
    assert {e.actor_account_id for e in entries} == {admin.pk}


def test_an_unfinished_draft_is_not_published(page, admin):
    pages.save_draft(page, [{"kind": "text"}], admin)
    response = admin_client(admin).post(url("publish", page), follow=True)
    assert "no és com el seu tipus demana" in response.content.decode()
    assert not PageVersion.objects.exists()


def test_rn_m07_13_long_share_texts_are_saved_with_a_warning(page, admin):
    response = admin_client(admin).post(
        url("share", page), {"share_title": "T" * 70, "share_description": "Inventada"}, follow=True
    )
    page.refresh_from_db()
    assert page.share_title == "T" * 70 and "60" in response.content.decode()


@pytest.mark.parametrize("name", ["autosave", "share", "publish"])
def test_without_wp1_the_actions_are_not_found(page, make_admin, name):  # noqa: F811
    response = admin_client(make_admin(R.SECRETARY)).post(url(name, page), {"note": "x"})
    assert response.status_code == 404 and not PageVersion.objects.exists()


def test_edge_cases_of_the_live_actions(page, admin):
    client = admin_client(admin)
    gone = client.post(url("autosave", page), {"index": "9", "text": "x", "level": "2"})
    assert gone.status_code == 409 and gone.json()["error"]
    long = client.post(url("share", page), {"share_title": "T" * 201}, follow=True)
    assert long.status_code == 200 and not page.share_title
    broken = PageVersion.objects.create(page=page, number=1, published_by=admin,
                                        blocks=[{"kind": "script"}])  # fmt: skip
    client.post(url("revert", page, broken.number))
    assert page.versions.count() == 1
    assert str(PageEditing.objects.get()) == f"Prèvia · {admin.login}"
