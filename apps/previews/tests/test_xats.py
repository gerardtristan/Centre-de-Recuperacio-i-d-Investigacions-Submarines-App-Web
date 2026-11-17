"""T-DX-39: el caixó d'escriure dels xats no porta veu ni dictat (P-95): cap micròfon ni
reconeixement de veu del navegador, que a Chrome envia l'àudio fora de la UE."""

import pytest
from django.test import override_settings
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL

pytestmark = pytest.mark.django_db


@override_settings(SHOW_UNDER_CONSTRUCTION=True)
def test_the_chat_composer_has_no_voice_input(login_as, personal_account):
    html = login_as(personal_account, AREA_PERSONAL).get(reverse("previews:xats")).content.decode()
    assert 'id="amanuense-text"' in html
    assert not any(word in html.lower() for word in ("micr", "dicta", "speechrecognition"))
