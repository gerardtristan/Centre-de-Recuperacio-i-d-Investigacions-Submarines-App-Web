"""Blocs d'activitats destacades i fetes (T-M07-29; RN-M07-21 i CA-M07-30 de l'addenda de la 106).
WP1 amb la matriu inicial de la T-M07-02. Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_ADMIN
from apps.activities.models import Activity
from apps.activities.tests.helpers import a_person, an_outing
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import featured, pages, render
from apps.website.models import FeaturedActivity
from apps.website.tests.test_blocks_106 import block

pytestmark = pytest.mark.django_db
R = Role.Code
S = Activity.Status
NAME = "Nomdepersona"


@pytest.fixture
def editor(make_admin):  # noqa: F811
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(R.COURSES_MANAGER)


def an_activity(manager, title, status=S.OPEN):
    activity = an_outing(manager, title=title, responsible=a_person(NAME))
    reason = "Motiu inventat" if status == S.CANCELLED else ""
    Activity.objects.filter(pk=activity.pk).update(
        status=status, published_at=timezone.now(), cancellation_reason=reason
    )
    return activity


def test_ca_m07_30_a_featured_activity_retired_in_02_disappears_at_the_next_request(
    editor, manager
):
    first, second = an_activity(manager, "Primera inventada"), an_activity(manager, "Segona")
    featured.add(first.pk, actor=editor)
    featured.add(second.pk, actor=editor)
    items = render._data(block("featured_activities"))["items"]
    assert [i["title"] for i in items] == ["Primera inventada", "Segona"]
    assert NAME not in repr(items) and items[0]["price"].endswith("€")
    Activity.objects.filter(pk=first.pk).update(
        status=S.CANCELLED, cancellation_reason="Motiu inventat"
    )
    assert [i["title"] for i in render._data(block("featured_activities"))["items"]] == ["Segona"]
    # Cap còpia: la web només en desa la referència, l'ordre i les dates.
    assert {f.name for f in FeaturedActivity._meta.fields} == {
        "id", "activity_ref", "order", "visible_from", "visible_until",
    }  # fmt: skip


def test_only_published_activities_once_and_with_a_valid_window(editor, manager):
    draft = an_outing(manager, title="Esborrany")
    with pytest.raises(ValidationError):
        featured.add(draft.pk, actor=editor)
    activity = an_activity(manager, "Sortida inventada")
    day = datetime.date(2027, 1, 10)
    with pytest.raises(ValidationError):
        featured.add(activity.pk, actor=editor, visible_from=day,
                     visible_until=day - datetime.timedelta(days=1))  # fmt: skip
    featured.add(activity.pk, actor=editor, visible_from=day)
    with pytest.raises(ValidationError):
        featured.add(activity.pk, actor=editor)
    assert AuditEntry.objects.filter(action=featured.ADDED).count() == 1


def test_the_visibility_window(editor, manager):
    activity = an_activity(manager, "Sortida inventada")
    start, end = datetime.date(2027, 1, 10), datetime.date(2027, 1, 20)
    featured.add(activity.pk, actor=editor, visible_from=start, visible_until=end)
    assert featured.items(today=start - datetime.timedelta(days=1)) == []
    assert [a.pk for a in featured.items(today=start)] == [activity.pk]
    assert [a.pk for a in featured.items(today=end)] == [activity.pk]
    assert featured.items(today=end + datetime.timedelta(days=1)) == []


def test_order_and_remove_are_recorded(editor, manager):
    rows = [featured.add(an_activity(manager, f"A{i}").pk, actor=editor) for i in range(3)]
    featured.move(rows[2], actor=editor, up=True)
    featured.move(rows[0], actor=editor, up=True)  # ja és la primera: res
    order = list(FeaturedActivity.objects.values_list("pk", flat=True))
    assert order == [rows[0].pk, rows[2].pk, rows[1].pk]
    featured.remove(rows[2], actor=editor)
    assert FeaturedActivity.objects.count() == 2
    actions = set(AuditEntry.objects.values_list("action", flat=True))
    assert {featured.ADDED, featured.MOVED, featured.REMOVED} <= actions


def test_without_wp1_not_found(editor, manager, make_admin):  # noqa: F811
    activity = an_activity(manager, "Sortida inventada")
    secretary = make_admin(R.SECRETARY)
    with pytest.raises(Http404):
        featured.add(activity.pk, actor=secretary)
    row = featured.add(activity.pk, actor=editor)
    for call in (lambda: featured.remove(row, actor=secretary),
                 lambda: featured.move(row, actor=secretary, up=False)):  # fmt: skip
        with pytest.raises(Http404):
            call()


def test_past_activities_block_brings_done_and_published_ones(manager):
    done = an_activity(manager, "Feta inventada", status=S.DONE)
    an_activity(manager, "Oberta inventada")
    items = render._data(block("past_activities", filters={"type": "outing"}, count=5))["items"]
    assert [i["title"] for i in items] == ["Feta inventada"] and NAME not in repr(items)
    # Revisió: el detall públic d'una activitat acabada és «no trobat»: cap enllaç.
    assert items[0]["url"] is None and reverse("activities:public_detail", args=[done.pk])


def test_the_selector_screen(login_as, editor, manager, make_admin):  # noqa: F811
    activity = an_activity(manager, "Sortida per destacar")
    client = login_as(editor, AREA_ADMIN)
    url = reverse("administration:website_featured")
    assert "Sortida per destacar" in client.get(url).content.decode()
    data = {"activity": activity.pk, "visible_from": "", "visible_until": ""}
    response = client.post(reverse("administration:website_featured_add"), data)
    assert (
        response.status_code == 302 and FeaturedActivity.objects.get().activity_ref == activity.pk
    )
    row = FeaturedActivity.objects.get()
    change = reverse("administration:website_featured_change", args=[row.pk])
    assert client.post(change, {"action": "remove"}).status_code == 302
    assert not FeaturedActivity.objects.exists()
    other = login_as(make_admin(R.SECRETARY), AREA_ADMIN)
    assert other.get(url).status_code == 404


def test_the_price_is_formatted_like_the_public_page_and_full_ones_say_so(
    editor, manager, monkeypatch
):
    activity = an_activity(manager, "Sortida plena inventada")
    Activity.objects.filter(pk=activity.pk).update(
        open_to_non_members=True, price_non_member_cents=3000
    )
    monkeypatch.setattr("apps.activities.enrolment.free_places", lambda activity: 0)  # plena
    featured.add(activity.pk, actor=editor)
    (item,) = render._data(block("featured_activities"))["items"]
    assert item["price"] == "30,00 €" and item["places_left"] == 0
    page = pages.save_page(None, actor=editor, slug="destacades-proves", title="Proves")[0]
    html = render.render_blocks([block("featured_activities")], page)
    assert "30,00 €" in html and "Places exhaurides" in html
