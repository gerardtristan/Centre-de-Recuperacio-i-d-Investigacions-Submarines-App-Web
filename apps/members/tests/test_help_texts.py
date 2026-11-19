"""Textos d'ajuda editables a les pantalles (T-M00-08e): el plafó «Ajuda» mostra el text vigent,
escapat. Només dades inventades."""

import pytest
from django.urls import reverse

from apps.core import business_settings
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.tests.test_birth_date_035 import personal_client
from apps.members.tests.test_member_edit import EDIT, a_member
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db
EDITED = "Escriu a la secretaria & la junta.\nT'hi respondrem."


def test_the_profile_shows_the_default_and_then_the_edited_help(make_admin):  # noqa: F811
    member = a_member()
    client, _account = personal_client(member.person)
    page = client.get(reverse("members:profile")).content.decode()
    assert "Per canviar el nom o el document, adreça&#x27;t a la secretaria." in page
    assert "El tipus i la data d&#x27;alta els porta la secretaria." in page
    key = "texts-members.ajuda-perfil-nom"
    business_settings.change(key, EDITED, make_admin("secretary"))
    page = client.get(reverse("members:profile")).content.decode()
    assert "Escriu a la secretaria &amp; la junta.<br>T&#x27;hi respondrem." in page
    assert "Com canvio el nom o el document?" in page


def test_the_member_edit_screen_shows_the_edited_help(make_admin):  # noqa: F811
    secretary = make_admin("secretary")
    business_settings.change("texts-members.ajuda-edicio-soci", EDITED, secretary)
    page = admin_client(secretary).get(reverse(EDIT, args=[a_member().pk])).content.decode()
    assert "Què queda registrat?" in page and "Escriu a la secretaria &amp; la junta." in page
