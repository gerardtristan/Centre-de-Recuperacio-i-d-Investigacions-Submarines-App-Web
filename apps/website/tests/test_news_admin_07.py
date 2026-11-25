"""Pantalles de les notícies (WP2; P-M07-B, RN-M07-02, 05 i 14; CA-M07-02 i 18). Només dades
inventades."""

import pytest
from django.urls import reverse

from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website.models import NewsItem

pytestmark = pytest.mark.django_db
R = Role.Code
LIST = reverse("administration:website_news")
ADD = reverse("administration:website_news_add")
DATA = {"title": "Sortida inventada", "slug": "sortida", "date": "2026-11-20", "body": "Text."}


def test_wp2_writes_publishes_and_retires_a_news_item(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.PRESIDENT))
    response = client.post(ADD, DATA)
    item = NewsItem.objects.get()
    assert response["Location"] == reverse("administration:website_news_edit", args=[item.pk])
    client.post(reverse("administration:website_news_publish", args=[item.pk]))
    item.refresh_from_db()
    assert item.status == "published"
    retire = reverse("administration:website_news_retire", args=[item.pk])
    assert client.post(retire, {"reason": ""}).status_code == 200
    client.post(retire, {"reason": "Data equivocada"})
    item.refresh_from_db()
    assert (item.status, item.retired_reason) == ("retired", "Data equivocada")
    assert "Sortida inventada" in client.get(LIST).content.decode()


@pytest.mark.parametrize("role", [R.SECRETARY, R.TREASURER, R.BOARD])
def test_ca_m07_18_without_wp2_the_screens_are_not_found(make_admin, role):  # noqa: F811
    client = admin_client(make_admin(role))
    assert client.get(LIST).status_code == 404
    assert client.post(ADD, DATA).status_code == 404
    assert not NewsItem.objects.exists()
