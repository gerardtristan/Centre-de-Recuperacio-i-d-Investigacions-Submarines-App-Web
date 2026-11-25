"""Notícies (T-M07-08; P-M07-B, RN-M07-02, 05 i 14; CA-M07-01 per a notícies). Només dades
inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404

from apps.core.models import AuditEntry, Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import media, news
from apps.website.models import NewsItem

pytestmark = pytest.mark.django_db
R = Role.Code
S = NewsItem.Status
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
DAY = datetime.date(2026, 11, 1)


@pytest.fixture
def editor(make_admin):  # noqa: F811
    """WP2 i WP3 són de l'administrador a la matriu inicial (T-M07-02)."""
    return make_admin(R.ADMINISTRATOR)


def _item(editor, slug="nova-sortida", days=0, **fields):
    date = DAY + datetime.timedelta(days=days)
    fields = {"title": "Sortida inventada", "body": "Text.", **fields}
    return news.save_news(None, actor=editor, slug=slug, date=date, **fields)


def _photo(editor, **details):
    return media.upload(SimpleUploadedFile("foto.png", PNG), actor=editor, alt_text="Una barca",
                        shows_people=False, **details)  # fmt: skip


def test_ca_m07_01_only_published_news_is_visible(editor):
    draft = _item(editor, "esborrany")
    shown = news.publish(_item(editor, "publicada"), actor=editor)
    retired = news.retire(news.publish(_item(editor, "retirada"), actor=editor), actor=editor,
                          reason="Data equivocada")  # fmt: skip
    assert news.get_published("publicada") == shown
    for slug in (draft.slug, retired.slug, "no-existeix"):
        with pytest.raises(Http404):
            news.get_published(slug)
    assert list(news.published()) == [shown]


def test_the_home_shows_the_most_recent_up_to_the_setting(editor):
    items = [news.publish(_item(editor, f"n{d}", days=d), actor=editor) for d in range(4)]
    assert news.home_news() == items[:0:-1]  # les tres més recents (valor inicial 3)
    Setting.objects.filter(key=news.NEWS_ON_HOME).update(initial_value=0)
    assert news.home_news() == []


def test_rn_m07_05_an_incomplete_photo_cannot_be_published(editor):
    item = _item(editor, image=_photo(editor))
    with pytest.raises(ValidationError):
        news.publish(item, actor=editor)
    item.refresh_from_db()
    assert item.status == S.DRAFT


def test_a_published_news_photo_is_served_until_the_news_is_retired(editor):
    photo = _photo(editor, author="Autora Inventada", licence_note="Cedida al club")
    item = news.publish(_item(editor, image=photo), actor=editor)
    assert media.public_asset(str(photo.key)) == photo
    news.retire(item, actor=editor, reason="Ja ha passat")
    with pytest.raises(Http404):
        media.public_asset(str(photo.key))


def test_editing_a_published_news_keeps_the_photo_rule(editor):
    item = news.publish(_item(editor), actor=editor)
    with pytest.raises(ValidationError):
        news.save_news(item, actor=editor, image=_photo(editor))
    assert news.save_news(item, actor=editor, body="Text corregit.").body == "Text corregit."


def test_rn_m07_14_publish_and_retire_are_recorded_and_retired_is_final(editor):
    item = news.publish(_item(editor), actor=editor)
    with pytest.raises(ValidationError):
        news.publish(item, actor=editor)
    with pytest.raises(ValidationError):
        news.retire(item, actor=editor, reason=" ")
    news.retire(item, actor=editor, reason="Data equivocada")
    news.retire(item, actor=editor, reason="Una altra vegada")  # no canvia res
    entries = AuditEntry.objects.filter(target_id=str(item.pk)).order_by("pk")
    assert [(e.action, e.old_value, e.new_value, e.reason) for e in entries] == [
        (news.ACTION_PUBLISHED, "draft", "published", ""),
        (news.ACTION_RETIRED, "published", "retired", "Data equivocada"),
    ]
    item.refresh_from_db()
    for action in (lambda: news.publish(item, actor=editor),
                   lambda: news.save_news(item, actor=editor, title="Una altra")):  # fmt: skip
        with pytest.raises(ValidationError):
            action()


def test_a_slug_is_unique(editor):
    _item(editor)
    with pytest.raises(ValidationError):
        _item(editor)


def test_a_role_without_wp2_gets_not_found(editor, make_admin):  # noqa: F811
    item = _item(editor)
    secretary = make_admin(R.SECRETARY)
    for action in (lambda: _item(secretary, "una-altra"),
                   lambda: news.publish(item, actor=secretary),
                   lambda: news.retire(item, actor=secretary, reason="Prova")):  # fmt: skip
        with pytest.raises(Http404):
            action()
    item.refresh_from_db()
    assert item.status == S.DRAFT and NewsItem.objects.count() == 1


def test_ca_m07_01_public_routes_show_only_published_news(client, editor):
    shown = news.publish(_item(editor, "publicada"), actor=editor)
    draft = _item(editor, "esborrany")
    page = client.get("/noticies/").content.decode()
    assert shown.title in page and "/noticies/esborrany/" not in page
    assert client.get(f"/noticies/{shown.slug}/").status_code == 200
    for slug in (draft.slug, "no-existeix"):
        assert client.get(f"/noticies/{slug}/").status_code == 404


def test_rn_m07_10_the_body_is_escaped(client, editor):
    news.publish(_item(editor, body="<script>alert(1)</script>"), actor=editor)
    page = client.get("/noticies/nova-sortida/").content.decode()
    assert "<script>alert(1)" not in page and "&lt;script&gt;" in page


def test_p489_the_public_photo_view_checks_at_every_request(client, editor):
    photo = _photo(editor, author="Autora Inventada", licence_note="Cedida al club")
    url = f"/web/fotos/{photo.key}/"
    assert client.get(url).status_code == 404  # encara no surt enlloc
    item = news.publish(_item(editor, image=photo), actor=editor)
    response = client.get(url)
    assert response.status_code == 200 and response["X-Content-Type-Options"] == "nosniff"
    assert b"".join(response.streaming_content) == PNG
    assert f'src="{url}"' in client.get(f"/noticies/{item.slug}/").content.decode()
    news.retire(item, actor=editor, reason="Ja ha passat")
    assert client.get(url).status_code == 404
