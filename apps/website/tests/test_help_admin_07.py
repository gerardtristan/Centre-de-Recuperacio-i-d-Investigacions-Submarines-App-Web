"""Pantalles de les preguntes freqüents (T-M07-09b; WP4; P-M07-G, CA-M07-02, 16 i 18). Només
dades inventades."""

import pytest
from django.urls import reverse

from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website import help
from apps.website.models import FaqEntry, FaqTopic

pytestmark = pytest.mark.django_db
R = Role.Code
LIST = reverse("administration:website_help")


def _url(name, *args):
    return reverse(f"administration:website_help_{name}", args=args)


def test_ca_m07_18_wp4_is_for_the_administration_the_president_and_the_board(make_admin):  # noqa: F811
    for role in (R.ADMINISTRATOR, R.PRESIDENT, R.BOARD):
        assert admin_client(make_admin(role)).get(LIST).status_code == 200
    secretary = admin_client(make_admin(R.SECRETARY))
    assert secretary.get(LIST).status_code == 404
    assert secretary.post(_url("topic_add"), {"name": "Quotes", "order": 1}).status_code == 404
    assert not FaqTopic.objects.exists()


def test_without_a_session_nothing_is_shown(client):
    assert client.get(LIST).status_code != 200


def test_a_question_is_created_unpublished_then_published_and_retired(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.BOARD))
    assert client.post(_url("topic_add"), {"name": "Quotes", "order": 1}).status_code == 302
    topic = FaqTopic.objects.get()
    data = {
        "topic": topic.pk,
        "question": "Quan es paga la quota?",
        "answer": "Al gener.",
        "order": 1,
    }
    response = client.post(_url("add"), data)
    entry = FaqEntry.objects.get()
    assert response.status_code == 302 and response["Location"] == _url("edit", entry.pk)
    assert entry.published is False and list(help.search("quota")) == []
    client.post(_url("publish", entry.pk), {"publish": "1"})
    assert list(help.search("quota")) == [entry]
    client.post(_url("publish", entry.pk), {"publish": "0"})
    entry.refresh_from_db()
    assert entry.published is False and FaqEntry.objects.count() == 1  # retirada, no esborrada
    page = client.get(LIST).content.decode()
    assert "Quan es paga la quota?" in page and "Publica-la" in page


def test_an_empty_question_shows_the_error_and_saves_nothing(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.ADMINISTRATOR))
    topic = FaqTopic.objects.create(name="Cursos")
    response = client.post(
        _url("add"), {"topic": topic.pk, "question": "", "answer": "x", "order": 1}
    )
    assert response.status_code == 200 and "Hi ha 1 error" in response.content.decode()
    assert not FaqEntry.objects.exists()


def test_rn_m07_14_publishing_retiring_and_editing_leave_a_trace_with_the_old_value(make_admin):  # noqa: F811
    from apps.core.models import AuditEntry

    actor = make_admin(R.ADMINISTRATOR)
    topic = FaqTopic.objects.create(name="Quotes")
    entry = help.save_entry(None, actor=actor, topic=topic, question="Quan?", answer="Al gener.")
    help.save_entry(entry, actor=actor, published=True)
    help.save_entry(entry, actor=actor, answer="Al febrer.")
    help.save_entry(entry, actor=actor, published=False)
    rows = list(
        AuditEntry.objects.filter(action__startswith="website.help")
        .order_by("pk")
        .values_list("action", "field", "old_value", "new_value")
    )
    assert (help.ACTION_PUBLISHED, "published", False, True) in rows
    assert (help.ACTION_CHANGED, "answer", "Al gener.", "Al febrer.") in rows
    assert (help.ACTION_RETIRED, "published", True, False) in rows


def test_a_stale_edit_does_not_publish_a_retired_question_again(make_admin):  # noqa: F811
    actor = make_admin(R.ADMINISTRATOR)
    topic = FaqTopic.objects.create(name="Quotes")
    entry = help.save_entry(None, actor=actor, topic=topic, question="Quan?", answer="x")
    help.save_entry(entry, actor=actor, published=True)
    stale = FaqEntry.objects.get(pk=entry.pk)  # una altra pestanya, encara publicada
    help.save_entry(entry, actor=actor, published=False)
    help.save_entry(stale, actor=actor, question="Quan es paga?")
    entry.refresh_from_db()
    assert (entry.published, entry.question) == (False, "Quan es paga?")


def test_publishing_an_invalid_question_shows_the_error_instead_of_failing(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.ADMINISTRATOR))
    topic = FaqTopic.objects.create(name="Cursos")
    entry = FaqEntry.objects.create(topic=topic, question="", answer="x")  # dada antiga, invàlida
    response = client.post(_url("publish", entry.pk), {"publish": "1"}, follow=True)
    assert response.status_code == 200
    entry.refresh_from_db()
    assert entry.published is False
