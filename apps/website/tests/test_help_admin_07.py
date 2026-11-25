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
