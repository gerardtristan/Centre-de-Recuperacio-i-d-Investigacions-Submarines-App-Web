"""Pantalla de les fotos d'una sortida de medi ambient (T-M02-20; CA-M02-22; P-41 oberta). Només
dades inventades."""

import pytest
from django.urls import reverse

from apps.activities.models import EnvironmentalPhoto
from apps.core.models import Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client

from .test_environment import manager  # noqa: F401 (fixture)
from .test_environment_photos import environment_photos, jpeg, outing, switch_on  # noqa: F401

pytestmark = pytest.mark.django_db


def page(outing):  # noqa: F811
    return reverse("administration:activity_environment", args=[outing.pk])


def post_photo(client, outing, **extra):  # noqa: F811
    data = {"photo": jpeg(), "author": "Autora Inventada", "usage_permission": "on", **extra}
    return client.post(reverse("administration:activity_environment_photo", args=[outing.pk]), data)


def test_switched_off_there_is_no_photo_section_and_no_upload(outing, manager):  # noqa: F811
    client = admin_client(manager)
    assert "Fotos de la sortida" not in client.get(page(outing)).content.decode()
    post_photo(client, outing)
    assert not EnvironmentalPhoto.objects.exists()


def test_ac14_uploads_and_retires_and_the_board_only_sees(outing, manager, switch_on, make_admin):  # noqa: F811
    client = admin_client(manager)
    assert post_photo(client, outing, usage_permission="").status_code == 303
    assert not EnvironmentalPhoto.objects.exists()  # sense permís d'ús, res
    post_photo(client, outing)
    photo = EnvironmentalPhoto.objects.get()
    file_url = reverse("administration:private_file", args=[photo.file_id])
    assert file_url in client.get(page(outing)).content.decode()
    board = admin_client(make_admin("board"))
    view = board.get(page(outing)).content.decode()
    assert file_url in view and "Afegeix una foto" not in view and "Retira-la" not in view
    assert board.get(file_url).status_code == 200
    assert post_photo(board, outing).status_code == 404
    retire = reverse("administration:activity_environment_photo_retire", args=[outing.pk, photo.pk])
    assert board.post(retire, {"reason": "x"}).status_code == 404
    client.post(retire, {"reason": "Foto equivocada"})
    photo.refresh_from_db()
    assert photo.status == "retired"
    assert client.get(file_url).status_code == 404


def test_the_file_view_is_not_found_once_the_switch_is_off(outing, manager, switch_on):  # noqa: F811
    client = admin_client(manager)
    post_photo(client, outing)
    url = reverse("administration:private_file", args=[EnvironmentalPhoto.objects.get().file_id])
    Setting.objects.filter(key=environment_photos.SWITCH).update(initial_value=False)
    assert client.get(url).status_code == 404
