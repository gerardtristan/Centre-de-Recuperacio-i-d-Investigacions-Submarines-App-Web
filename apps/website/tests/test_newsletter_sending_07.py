"""Butlletí: redactar, enviar per la cua i recomptes (T-M07-14; CA-M07-08 i 10, RN-M07-06 i 14,
CA-M07-18 per a WP6). Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.core.models import AuditEntry, LegalText, OutgoingEmail, Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import newsletter
from apps.website.models import Newsletter, NewsletterDelivery

pytestmark = pytest.mark.django_db
R = Role.Code


@pytest.fixture
def enabled():
    Setting.objects.filter(key=newsletter.ENABLED).update(initial_value=True)


@pytest.fixture
def three(enabled):
    """Una subscripció confirmada, una de pendent i una de baixa."""
    text = LegalText.objects.create(kind="newsletter", version=1, content="Butlletí inventat")
    confirmed, _ = newsletter.subscribe("confirmada@example.org", legal_text=text)
    newsletter.confirm(confirmed.token)
    newsletter.subscribe("pendent@example.org", legal_text=text)
    gone, _ = newsletter.subscribe("baixa@example.org", legal_text=text)
    newsletter.unsubscribe(gone.token)
    return confirmed


@pytest.fixture
def president(make_admin):  # noqa: F811
    return make_admin(R.PRESIDENT)


def _draft(actor):
    return newsletter.save_draft(actor=actor, subject="Sortides de desembre", body="Text inventat")


def test_ca_m07_08_only_the_confirmed_one_gets_it_and_it_is_sent_only_once(three, president):
    draft = _draft(president)
    assert newsletter.recipients_count(president) == 1
    assert newsletter.send(draft, actor=president) == 1
    draft.refresh_from_db()
    assert draft.status == Newsletter.Status.SENT and draft.sent_at
    assert [d.subscription for d in NewsletterDelivery.objects.all()] == [three]
    with pytest.raises(ValidationError):
        newsletter.send(draft, actor=president)
    with pytest.raises(ValidationError):
        newsletter.save_draft(actor=president, subject="Canvi", body="x", newsletter=draft)
    assert NewsletterDelivery.objects.count() == 1


def test_rn_m07_14_sending_is_recorded_with_the_previous_value(three, president):
    newsletter.send(_draft(president), actor=president)
    entry = AuditEntry.objects.get(action=newsletter.ACTION_SENT)
    assert (entry.old_value, entry.new_value, entry.details) == ("draft", "sent", {"recipients": 1})


def test_drafts_are_numbered(enabled, president):
    assert [_draft(president).number for _ in range(2)] == [1, 2]


def test_ca_m07_10_switched_off_wp6_cannot_write_or_send(three, president):
    draft = _draft(president)
    Setting.objects.filter(key=newsletter.ENABLED).update(initial_value=False)
    for call in (
        lambda: _draft(president),
        lambda: newsletter.send(draft, actor=president),
        lambda: newsletter.recipients_count(president),
        lambda: newsletter.counts(draft, actor=president),
    ):
        with pytest.raises(Http404):
            call()


@pytest.mark.parametrize("role", [R.SECRETARY, R.TREASURER, R.BOARD])
def test_ca_m07_18_without_wp6_it_is_not_found(three, make_admin, role):  # noqa: F811
    with pytest.raises(Http404):
        _draft(make_admin(role))


def test_ca_m07_18_wp6_sees_counts_never_an_email(three, president):
    draft = _draft(president)
    newsletter.send(draft, actor=president)
    counts = newsletter.counts(draft, actor=president)
    assert counts == {"recipients": 1, "sent": 0, "failed": 0, "unsubscribed_after": 0}
    assert "@" not in str(counts)


def test_ca_m07_08_unsubscriptions_after_sending_are_counted(three, president):
    draft = _draft(president)
    newsletter.send(draft, actor=president)
    newsletter.unsubscribe(three.token)
    assert newsletter.counts(draft, actor=president)["unsubscribed_after"] == 1


def test_rn_m07_06_an_unsubscription_before_the_batch_goes_out_skips_it(three, president):
    newsletter.send(_draft(president), actor=president)
    newsletter.unsubscribe(three.token)
    newsletter.send_batch(list(NewsletterDelivery.objects.values_list("pk", flat=True)))
    delivery = NewsletterDelivery.objects.get()
    assert delivery.skipped and delivery.email is None
    assert not OutgoingEmail.objects.exists()


def test_the_batches_go_to_the_queue(three, president, monkeypatch):
    calls = []
    monkeypatch.setattr(newsletter, "BATCH_SIZE", 1)
    from apps.website import tasks

    monkeypatch.setattr(tasks.send_newsletter_batch, "defer", lambda **kw: calls.append(kw))
    newsletter.send(_draft(president), actor=president)
    assert calls == [{"delivery_ids": [NewsletterDelivery.objects.get().pk]}]


def test_ca_m07_08_each_email_has_the_unsubscribe_link_and_low_priority(three, president):
    newsletter.send(_draft(president), actor=president)
    newsletter.send_batch(list(NewsletterDelivery.objects.values_list("pk", flat=True)))
    email = OutgoingEmail.objects.get()
    assert email.priority == OutgoingEmail.Priority.NEWSLETTER
    assert f"/butlleti/baixa/{three.token}/" in email.body_text
    assert email.to_address == "confirmada@example.org"


def test_the_newsletter_subject_is_not_html_escaped():
    from apps.core import mail

    email = mail.queue_email(
        newsletter.TEMPLATE, to="x@example.org",
        context={"subject": "Cursos & sortides", "body": "b", "unsubscribe_url": "u"},
    )  # fmt: skip
    assert email.subject == "Cursos & sortides"
