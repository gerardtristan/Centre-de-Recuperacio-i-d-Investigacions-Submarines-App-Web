"""Pantalles del butlletí (WP6; P-M07-F, CA-M07-02, 08, 10 i 18). Només dades inventades."""

import pytest
from django.urls import reverse

from apps.core.models import Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website.models import Newsletter, NewsletterDelivery
from apps.website.tests.test_newsletter_sending_07 import _draft, enabled, three  # noqa: F401

pytestmark = pytest.mark.django_db
R = Role.Code
LIST = reverse("administration:website_newsletters")
ADD = reverse("administration:website_newsletter_add")


def _edit(item):
    return reverse("administration:website_newsletter_edit", args=[item.pk])


def _send(item):
    return reverse("administration:website_newsletter_send", args=[item.pk])


def test_ca_m07_10_switched_off_every_screen_is_not_found(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.PRESIDENT))
    for url in (LIST, ADD):
        assert client.get(url).status_code == 404


def test_ca_m07_18_without_wp6_the_screens_are_not_found(enabled, make_admin):  # noqa: F811
    client = admin_client(make_admin(R.SECRETARY))
    assert client.get(LIST).status_code == 404
    assert client.post(ADD, {"subject": "x", "body": "y"}).status_code == 404
    assert not Newsletter.objects.exists()


def test_a_draft_shows_the_preview_and_the_count_but_never_an_address(three, make_admin):  # noqa: F811
    client = admin_client(make_admin(R.PRESIDENT))
    response = client.post(ADD, {"subject": "Sortides de gener", "body": "Text inventat."})
    item = Newsletter.objects.get()
    assert response.status_code == 302 and response["Location"] == _edit(item)
    page = main_of(client.get(_edit(item)).content.decode())
    assert "Vista prèvia" in page and "1 subscripció confirmada" in page
    assert "@example.org" not in page


def test_ca_m07_08_sending_needs_the_confirmation_and_happens_once(three, make_admin):  # noqa: F811
    president = make_admin(R.PRESIDENT)
    client, item = admin_client(president), _draft(president)
    page = client.post(_send(item), {}).content.decode()
    assert "Cal confirmar l&#x27;enviament." in page
    assert not NewsletterDelivery.objects.exists()
    response = client.post(_send(item), {"confirm": "on"})
    assert response.status_code == 302 and response["Location"] == LIST
    assert NewsletterDelivery.objects.count() == 1
    again = client.post(_send(item), {"confirm": "on"}, follow=True).content.decode()
    assert "Aquest butlletí ja s&#x27;ha enviat." in again
    assert NewsletterDelivery.objects.count() == 1
    page = main_of(client.get(_edit(item)).content.decode())
    assert "Destinataris" in page and "Desa l&#x27;esborrany" not in page
    assert "@example.org" not in page
    assert client.post(_edit(item), {"subject": "Canvi", "body": "x"}).status_code == 404

