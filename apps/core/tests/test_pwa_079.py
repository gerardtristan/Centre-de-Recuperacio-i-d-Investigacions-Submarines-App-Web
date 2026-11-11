"""Còpia del carnet sense connexió després de la decisió 079 (T-M01-21; A-28, RN-M01-96,
CA-M01-110): en sortir només s'esborra la còpia del carnet; la preferència de tema es conserva.
El comportament en un navegador de debò és a `e2e/test_pwa_079.py`. Caducitat de la còpia: 30 dies
i mai després del «vàlid fins al» (decisió 081, punt 15; RN-M01-101).
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


def test_081_copy_lasts_the_decided_days_in_the_worker_and_in_the_page():
    """Decisió 081, punt 15: 30 dies, el mateix valor al service worker i a la pàgina."""
    from apps.members import cards

    assert cards.OFFLINE_COPY_DAYS == 30
    assert f"var DIES_COPIA = {cards.OFFLINE_COPY_DAYS};" in SOURCE


def test_081_an_expired_copy_is_deleted_and_never_shown():
    function = re.search(r"function copiaDelCarnet\(\) \{(.*?)\n\}", SOURCE, re.S).group(1)
    assert "copiaCaducada(copia, Date.now())" in function
    assert "esborraCarnet().then(function () { return Response.error(); })" in function
    expired = re.search(r"function copiaCaducada\(copia, ara\) \{(.*?)\n\}", SOURCE, re.S)
    expired = expired.group(1)
    # Sense hora de desar (còpia d'una versió anterior) també és caducada.
    assert "if (!desada || ara - desada > DIES_COPIA * MS_DIA) return true;" in expired
    # Mai després del «vàlid fins al»: l'endemà a les 00:00 ja no es mostra.
    assert "Number(parts[2]) + 1" in expired and "if (ara >= final) return true;" in expired


def test_081_the_page_reloads_when_the_connection_comes_back_without_a_loop():
    script = (settings.BASE_DIR / "static" / "js" / "carnet-copia.js").read_text(encoding="utf-8")
    assert "addEventListener('online', comenca)" in script
    # Primer comprova que el servidor respon; si no, reintents limitats i espaiats (cap bucle).
    assert "var ESPERES = [1000, 2000, 4000, 8000, 15000, 30000];" in script
    assert "if (intent + 1 < ESPERES.length)" in script and "if (provant) return;" in script
    assert "if (!avis || avis.hidden) return;" in script  # només a la còpia
    assert "'/static/js/carnet-copia.js'" in SOURCE  # disponible sense connexió
