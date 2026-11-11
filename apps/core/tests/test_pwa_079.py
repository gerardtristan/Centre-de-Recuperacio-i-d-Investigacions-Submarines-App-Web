"""Còpia del carnet sense connexió després de la decisió 079 (T-M01-21; A-28, RN-M01-96,
CA-M01-110): en sortir només s'esborra la còpia del carnet; la preferència de tema es conserva.
El comportament en un navegador de debò és a `e2e/test_pwa_079.py`. La caducitat de la còpia als
N dies NO està implementada: N no està decidit.
"""

import re

import pytest
from django.conf import settings
from django.urls import reverse

SOURCE = (settings.BASE_DIR / "static" / "js" / "service-worker.js").read_text(encoding="utf-8")
THEME = (settings.BASE_DIR / "static" / "js" / "tema.js").read_text(encoding="utf-8")


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["accounts:logout", "administration:logout"])
def test_ca_m01_110_logout_does_not_clear_the_site_data(client, personal_account, name):
    client.force_login(personal_account)
    response = client.post(reverse(name))
    # «Clear-Site-Data» esborraria també el tema (localStorage): no s'envia (A-28).
    assert "Clear-Site-Data" not in response.headers


def test_ca_m01_110_service_worker_only_deletes_the_card_copy_on_login_and_logout():
    function = re.search(r"function esborraCarnet\(\) \{(.*?)\n\}", SOURCE, re.S).group(1)
    assert "caches.delete(MEMORIA_CARNET)" in function
    assert "MEMORIA_ESTILS" not in function
    # Entrar o sortir crida només `esborraCarnet`.
    assert "if (ENTRAR_O_SORTIR.test(url.pathname)) event.waitUntil(esborraCarnet());" in SOURCE
    # El service worker no toca mai l'emmagatzematge on viu el tema.
    assert "localStorage" not in SOURCE
    assert "localStorage" in THEME and "cris-tema" in THEME


def test_copy_expiry_after_n_days_is_not_implemented_until_n_is_decided():
    """RN-M01-96: N [A validar: responsable]. Cap codi no simula la regla amb un valor inventat."""
    for word in ("Date.now", "expires", "maxAge", "max-age", "DIES"):
        assert word not in SOURCE
