"""Pantalles dels tutorials (T-M07-10b; WP4; RN-M07-05, 11 i 14; CA-M07-02, 17 i 18). Només
dades inventades."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website import help as faq
from apps.website import media
from apps.website.models import Tutorial
from apps.website.tests.test_media_07 import PNG

pytestmark = pytest.mark.django_db
R = Role.Code
LIST = reverse("administration:website_tutorials")
ADD = reverse("administration:website_tutorial_add")
DATA = {"title": "Com pagar la quota", "slug": "pagar-la-quota", "steps": "Un.\nDos.",
        "screen_code": "payments:charge", "order": 0}  # fmt: skip


def _publish(tutorial, value):
    return reverse("administration:website_tutorial_publish", args=[tutorial.pk]), {
        "publish": value
    }


def test_wp4_writes_a_tutorial_unpublished_then_publishes_and_retires_it(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.BOARD))  # M07-4: la Junta també té WP4
    response = client.post(ADD, DATA)
    tutorial = Tutorial.objects.get()
    assert response["Location"] == reverse(
        "administration:website_tutorial_edit", args=[tutorial.pk]
    )
    assert not tutorial.published
    client.post(*_publish(tutorial, "1"))
    tutorial.refresh_from_db()
    assert tutorial.published and faq.tutorial_for("payments:charge") == tutorial
    client.post(*_publish(tutorial, "0"))
    tutorial.refresh_from_db()
    assert not tutorial.published and Tutorial.objects.count() == 1
    actions = list(
        AuditEntry.objects.filter(target_id=str(tutorial.pk)).values_list("action", flat=True)
    )
    assert actions == [faq.TUTORIAL_PUBLISHED, faq.TUTORIAL_RETIRED]
    assert "Com pagar la quota" in client.get(LIST).content.decode()


def test_an_unknown_screen_is_rejected_in_the_form(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.ADMINISTRATOR))
    response = client.post(ADD, {**DATA, "screen_code": "payments:no_existeix"})
    assert (
        response.status_code == 200 and "Aquesta pantalla no existeix." in response.content.decode()
    )
    assert not Tutorial.objects.exists()


def test_the_photo_list_offers_only_publishable_photos(make_admin):  # noqa: F811
    admin = make_admin(R.ADMINISTRATOR)
    complete = media.upload(SimpleUploadedFile("a.png", PNG), actor=admin, alt_text="Completa",
                            shows_people=False, author="Autora Inventada",
                            licence_note="Cedida al club")  # fmt: skip
    media.upload(SimpleUploadedFile("b.png", PNG), actor=admin, alt_text="Incompleta",
                 shows_people=False)  # fmt: skip
    page = admin_client(admin).get(ADD).content.decode()
    assert "Completa" in page and "Incompleta" not in page and complete.pk


@pytest.mark.parametrize("role", [R.SECRETARY, R.TREASURER])
def test_ca_m07_18_without_wp4_the_screens_are_not_found(make_admin, role):  # noqa: F811
    client = admin_client(make_admin(role))
    assert client.get(LIST).status_code == 404
    assert client.post(ADD, DATA).status_code == 404
    assert not Tutorial.objects.exists()
