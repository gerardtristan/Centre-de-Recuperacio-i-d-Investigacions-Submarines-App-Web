"""Versions comparables, publicació i retirada programades, retirar i recuperar (T-M07-22, decisió
106; RN-M07-16, 17 i 25; CA-M07-26 i 33). WP1 amb la matriu inicial de la T-M07-02. Només dades
inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website import pages, schedule, tasks
from apps.website.models import Page, PageDraft, PageVersion, ScheduledAction
from apps.website.tests.test_blocks_106 import block

pytestmark = pytest.mark.django_db
R = Role.Code
S = ScheduledAction.Status
H1, H2, H3 = (block("heading", text=t) for t in ("Un", "Dos", "Tres"))
SOON = datetime.timedelta(minutes=10)


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def page(admin):
    return pages.save_page(None, actor=admin, slug="versions-inventada", title="Versions")[0]


def url(name, page, *args):
    return reverse(f"administration:website_page_{name}", args=[page.pk, *args])


def test_rn_m07_16_two_versions_are_compared_block_by_block():
    four = block("heading", text="Quatre")
    rows = schedule.compare([H1, H2, H3], [H1, block("heading", text="Dos bis"), H3, four])
    assert [state for state, _a, _b in rows] == ["same", "changed", "same", "added"]
    assert rows[1] == ("changed", "Títol · Dos", "Títol · Dos bis")
    assert [s for s, _a, _b in schedule.compare([H1, H2], [H2])] == ["removed", "same"]


def test_ca_m07_26_a_scheduled_publication_runs_once_in_the_name_of_who_scheduled_it(
    page,
    admin,
    make_admin,  # noqa: F811
):
    pages.save_draft(page, [H1], admin)
    item = schedule.schedule(page, "publish", timezone.now() + SOON, admin)
    assert schedule.run_due() == 0  # encara no
    later = timezone.now() + 2 * SOON
    assert schedule.run_due(later) == 1 and schedule.run_due(later) == 0
    item.refresh_from_db()
    assert item.status == S.DONE and PageVersion.objects.get().blocks == [H1]
    entry = AuditEntry.objects.get(action=pages.ACTION_PUBLISHED)
    assert entry.actor_account_id == admin.pk and PageDraft.objects.get().blocks == [H1]
    periodic = tasks.app.periodic_registry.periodic_tasks[("website.run_scheduled_actions", "")]
    assert periodic.cron == "* * * * *"
    tasks.run_scheduled_actions(0)  # la crida de la cua, sense res pendent


def test_ca_m07_26_a_cancelled_one_does_nothing_and_cannot_be_cancelled_twice(page, admin):
    pages.save_draft(page, [H1], admin)
    item = schedule.schedule(page, "publish", timezone.now() + SOON, admin)
    schedule.cancel(item, admin)
    assert schedule.run_due(timezone.now() + 2 * SOON) == 0
    assert not PageVersion.objects.exists()
    with pytest.raises(ValidationError):
        schedule.cancel(item, admin)
    assert AuditEntry.objects.filter(action=schedule.ACTION_CANCELLED).count() == 1


def test_a_scheduled_action_that_can_no_longer_be_done_fails_with_the_reason(
    page, admin, monkeypatch
):
    pages.save_draft(page, [{"kind": "text"}], admin)  # a mig fer
    bad = schedule.schedule(page, "publish", timezone.now() + SOON, admin)
    retire = schedule.schedule(page, "retire", timezone.now() + SOON, admin)  # no és publicada
    assert schedule.run_due(timezone.now() + 2 * SOON) == 0
    pages.save_draft(page, [H1], admin)
    lost = schedule.schedule(page, "publish", timezone.now() + SOON, admin)

    def no_longer(actor):
        raise Http404

    monkeypatch.setattr(pages, "require", no_longer)  # qui la va programar ja no té WP1
    assert schedule.run_due(timezone.now() + 2 * SOON) == 0
    for item in (bad, retire, lost):
        item.refresh_from_db()
        assert item.status == S.FAILED and item.error
    assert not PageVersion.objects.exists() and str(lost).startswith("Versions · Publicar")


@pytest.mark.parametrize("delta", [datetime.timedelta(0), -SOON])
def test_the_past_or_an_unknown_action_cannot_be_scheduled(page, admin, delta):
    with pytest.raises(ValidationError):
        schedule.schedule(page, "publish", timezone.now() + delta, admin)
    with pytest.raises(ValidationError):
        schedule.schedule(page, "delete", timezone.now() + SOON, admin)
    assert not ScheduledAction.objects.exists()


def test_ca_m07_33_a_retired_page_is_recovered_as_a_draft_with_its_last_version(page, admin):
    pages.publish_page(page, [H1, H2], admin)
    with pytest.raises(ValidationError):
        pages.recover_page(page, admin)
    pages.retire_page(page, admin)
    with pytest.raises(ValidationError):
        pages.retire_page(page, admin)
    page = pages.recover_page(page, admin)
    assert page.status == Page.Status.DRAFT and PageDraft.objects.get().blocks == [H1, H2]
    assert Page.objects.filter(pk=page.pk).exists() and PageVersion.objects.count() == 1
    actions = AuditEntry.objects.filter(target_id=str(page.pk)).values_list("action", flat=True)
    assert {pages.ACTION_RETIRED, pages.ACTION_RECOVERED} <= set(actions)


def test_the_versions_screen_compares_schedules_cancels_retires_and_recovers(page, admin):
    client = admin_client(admin)
    pages.publish_page(page, [H1], admin)
    pages.save_draft(page, [H1, H2], admin)
    html = client.get(url("versions", page)).content.decode()
    assert "Afegit" in html and "Títol · Dos" in html
    assert "Igual" in client.get(url("versions", page) + "?a=1&b=1").content.decode()
    assert (
        client.post(url("schedule", page), {"action": "publish", "run_at": ""}).status_code == 400
    )
    when = (timezone.localtime() + SOON).strftime("%Y-%m-%dT%H:%M")
    client.post(url("schedule", page), {"action": "publish", "run_at": when})
    item = ScheduledAction.objects.get()
    client.post(url("schedule_cancel", page, item.pk))
    item.refresh_from_db()
    assert item.status == S.CANCELLED
    response = client.post(url("schedule_cancel", page, item.pk), follow=True)
    assert "ja no es pot anul·lar" in response.content.decode()
    client.post(url("retire", page))
    page.refresh_from_db()
    assert page.status == Page.Status.RETIRED
    client.post(url("recover", page))
    page.refresh_from_db()
    assert page.status == Page.Status.DRAFT


@pytest.mark.parametrize("name", ["versions", "schedule", "retire", "recover"])
def test_without_wp1_the_versions_screens_are_not_found(page, make_admin, name):  # noqa: F811
    client = admin_client(make_admin(R.SECRETARY))
    response = client.get(url(name, page)) if name == "versions" else client.post(url(name, page))
    assert response.status_code == 404
    with pytest.raises(Http404):
        pages.retire_page(page, make_admin(R.TREASURER))


def test_review_an_unexpected_error_fails_that_action_and_the_queue_goes_on(
    page, admin, monkeypatch, caplog
):
    pages.save_draft(page, [H1], admin)
    broken = schedule.schedule(page, "retire", timezone.now() + SOON, admin)
    good = schedule.schedule(page, "publish", timezone.now() + SOON, admin)

    def boom(page, actor):
        raise RuntimeError("error inventat")

    monkeypatch.setattr(pages, "retire_page", boom)
    assert schedule.run_due(timezone.now() + 2 * SOON) == 1
    broken.refresh_from_db()
    good.refresh_from_db()
    assert broken.status == S.FAILED and broken.error and "inventat" not in broken.error
    assert good.status == S.DONE and "error inventat" in caplog.text


def test_review_recovering_keeps_a_pending_draft_with_other_changes(page, admin):
    pages.publish_page(page, [H1], admin)
    pages.retire_page(page, admin)
    pages.save_draft(page, [H1, H2], admin)  # canvis que encara no s'havien publicat
    page = pages.recover_page(page, admin)
    assert page.status == Page.Status.DRAFT and PageDraft.objects.get().blocks == [H1, H2]


@pytest.mark.xfail(reason="La pàgina pública és la T-M07-05: llavors, «no trobat» fins que es "
                   "publica (CA-M07-33)", strict=True)  # fmt: skip
def test_ca_m07_33_the_public_does_not_see_a_recovered_page_until_it_is_published(
    page, admin, client
):
    pages.publish_page(page, [H1], admin)
    pages.retire_page(page, admin)
    pages.recover_page(page, admin)
    assert client.get(f"/{page.slug}/").status_code == 404
    pages.publish_draft(page, admin)
    assert client.get(f"/{page.slug}/").status_code == 200
