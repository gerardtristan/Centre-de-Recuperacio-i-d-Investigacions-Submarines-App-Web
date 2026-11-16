"""Ajustos al navegador (T-AJ-02; 055, RN-AJ-05, CA-AJ-01 i 05; RN-RP-22): l'administrador
canvia un valor de pagaments des del menú (un valor fora de rang no es desa) i el tresorer, amb
«Cons.», veu el valor i l'historial sense formulari. Pantalles a 1280, 390 i 320 px."""

import pytest
from playwright.sync_api import expect

from apps.core import business_settings
from apps.core.models import Setting

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e

KEY = "payments.bizum_ui_timeout_minutes"
GIVE_UP = "payments.safety_net_give_up_hours"
LABEL = "Minuts que la pantalla espera la confirmació d'un Bizum"
GIVE_UP_LABEL = (
    "Hores que la xarxa de seguretat torna a provar una ordre abans de deixar-la a revisar"
)


def test_administrator_changes_a_value_and_treasurer_only_sees_it(page, live_server, review):
    # Les creen les migracions del 05b (T-M05b-22 i 28); aquí, si encara no hi són.
    for key, initial, low, high in ((KEY, 15, 5, 30), (GIVE_UP, 24, 24, 168)):
        Setting.objects.get_or_create(
            key=key,
            defaults={"module": "payments", "value_type": "integer", "initial_value": initial,
                      "min_value": low, "max_value": high},
        )  # fmt: skip
    admin = make_admin("admin.prova", "administrator")
    login_admin(page, live_server.url, admin.login)
    page.get_by_role("navigation", name="Seccions").get_by_role("link", name="Ajustos").click()
    page.get_by_role("link", name="Ajustos de pagaments").click()
    expect(page.get_by_role("heading", name="Ajustos de pagaments")).to_be_visible()
    # El valor de la 093 (T-M05b-28).
    expect(page.get_by_role("link", name=f"Canvia: {GIVE_UP_LABEL}")).to_be_visible()
    review("apartat")

    page.get_by_role("link", name=f"Canvia: {LABEL}").click()
    page.get_by_label("Valor nou").fill("31")
    page.get_by_role("button", name="Desa el valor").click()
    expect(page.get_by_text("No s'ha desat res.")).to_be_visible()
    review("fora-de-rang")

    page.get_by_label("Valor nou").fill("20")
    page.get_by_label("Nota").fill("Prova inventada")
    page.get_by_role("button", name="Desa el valor").click()
    expect(page.get_by_text("Valor desat.")).to_be_visible()
    expect(page.get_by_role("cell", name="Prova inventada")).to_be_visible()
    review("desat")
    assert business_settings.get(KEY) == 20

    page.context.clear_cookies()
    treasurer = make_admin("tresoreria.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    page.get_by_role("navigation", name="Seccions").get_by_role("link", name="Ajustos").click()
    page.get_by_role("link", name="Ajustos de pagaments").click()
    page.get_by_role("link", name=f"Historial: {LABEL}").click()
    expect(page.get_by_text("Pots veure aquest valor, però no canviar-lo.")).to_be_visible()
    expect(page.get_by_role("button", name="Desa el valor")).to_have_count(0)
    review("nomes-consulta")
