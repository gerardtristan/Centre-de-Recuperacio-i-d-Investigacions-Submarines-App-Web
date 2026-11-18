"""Ajustos al navegador (T-AJ-02; 055, RN-AJ-05, CA-AJ-01 i 05; RN-RP-22): l'administrador
canvia un valor de pagaments des del menú (un valor fora de rang no es desa) i el tresorer, amb
«Cons.», veu el valor i l'historial sense formulari. Ajustos de socis (T-M01-32): el tresorer
programa un preu i canvia els recordatoris. Codis de retorn (P-291): el tresorer en canvia
l'acció. Textos dels correus (T-M00-08): la secretaria edita el de la baixa. Pantalles a
1280, 390 i 320 px."""

from datetime import timedelta

import pytest
from django.utils import timezone
from playwright.sync_api import expect

from apps.core import business_settings
from apps.core.models import Role, RolePermission, Setting

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


def test_treasurer_schedules_a_member_price_and_edits_the_reminders(page, live_server, review):
    # T-M01-32: l'apartat de socis (les claus les crea `members/0022`). El tresorer programa un
    # preu nou amb data i nota (VC-01) i canvia la llista de recordatoris (VC-02); el text del
    # darrere del carnet (VC-03) només el pot veure.
    treasurer = make_admin("tresoreria.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    page.get_by_role("navigation", name="Seccions").get_by_role("link", name="Ajustos").click()
    page.get_by_role("link", name="Ajustos de socis").click()
    expect(page.get_by_role("heading", name="Ajustos de socis")).to_be_visible()
    review("socis-apartat")

    page.get_by_role("link", name="Canvia: Quota anual de soci simpatitzant").click()
    page.get_by_label("Valor nou").fill("40,00")
    page.get_by_label("En vigor des de").fill(
        (timezone.localdate() + timedelta(days=30)).isoformat()
    )
    page.get_by_label("Nota").fill("Assemblea inventada")
    page.get_by_role("button", name="Desa el valor").click()
    expect(page.get_by_text("Valor desat.")).to_be_visible()
    review("socis-preu-programat")
    assert business_settings.get("members.annual_fee_cents.supporter") == 3500

    page.get_by_role("link", name="Ajustos de socis").click()
    expect(page.get_by_role("cell", name="40,00 € des del")).to_be_visible()
    page.get_by_role("link", name="Canvia: Dies dels recordatoris de quota").click()
    page.get_by_label("Valor nou").fill("-10, 0, 0")
    page.get_by_role("button", name="Desa el valor").click()
    expect(page.get_by_text("No s'ha desat res.")).to_be_visible()
    page.get_by_label("Valor nou").fill("-10, 0, 20")
    page.get_by_role("button", name="Desa el valor").click()
    expect(page.get_by_text("Valor desat.")).to_be_visible()
    review("socis-recordatoris")
    assert business_settings.get("members.fee_reminder_offsets") == [-10, 0, 20]

    page.get_by_role("link", name="Ajustos de socis").click()
    page.get_by_role("link", name="Historial: Text del darrere del carnet").click()
    expect(page.get_by_text("Pots veure aquest valor, però no canviar-lo.")).to_be_visible()


def test_treasurer_moves_a_return_code_to_another_action(page, live_server, review):
    # P-291 (095): els codis de retorn són ajustos de pagaments (`payments/0021`). Un codi no pot
    # ser a totes dues llistes: primer es treu de «bloquegen el mandat» i després va a «reintent».
    treasurer = make_admin("tresoreria.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    page.get_by_role("navigation", name="Seccions").get_by_role("link", name="Ajustos").click()
    page.get_by_role("link", name="Ajustos de pagaments").click()
    expect(page.get_by_role("cell", name="AC04, MD01").first).to_be_visible()
    review("codis-retorn-apartat")

    page.get_by_role("link", name="Canvia: Codis de retorn que proposen un reintent").click()
    page.get_by_label("Valor nou").fill("AM04, MD01")
    page.get_by_role("button", name="Desa el valor").click()
    expect(page.get_by_text("MD01 ja és a una altra llista")).to_be_visible()
    review("codis-retorn-conflicte")

    page.get_by_role("link", name="Ajustos de pagaments").click()
    page.get_by_role("link", name="Canvia: Codis de retorn que bloquegen el mandat").click()
    page.get_by_label("Valor nou").fill("AC04")
    page.get_by_role("button", name="Desa el valor").click()
    expect(page.get_by_text("Valor desat.")).to_be_visible()
    page.get_by_role("link", name="Ajustos de pagaments").click()
    page.get_by_role("link", name="Canvia: Codis de retorn que proposen un reintent").click()
    page.get_by_label("Valor nou").fill("AM04, MD01")
    page.get_by_role("button", name="Desa el valor").click()
    expect(page.get_by_text("Valor desat.")).to_be_visible()
    review("codis-retorn-desat")
    assert business_settings.get("payments.return_codes_retry") == "AM04, MD01"


def test_secretary_previews_and_publishes_the_leave_email(page, live_server, review):
    # T-M00-08 (085, S-1 i S-3): el text del correu de baixa (`core/0047`), amb la vista prèvia
    # amb dades inventades, un text amb HTML que no es desa i la publicació amb l'historial.
    key = "texts.baixa-efectiva"
    Setting.objects.get_or_create(
        key=key,
        defaults={"module": "texts", "value_type": "text", "initial_value": "", "max_length": 5000},
    )
    RolePermission.objects.get_or_create(
        role=Role.objects.get(code="secretary"),
        permission_code="settings.section.texts",
        defaults={"scope": "all"},
    )
    secretary = make_admin("secretaria.prova", "secretary")
    login_admin(page, live_server.url, secretary.login)
    page.get_by_role("navigation", name="Seccions").get_by_role("link", name="Ajustos").click()
    page.get_by_role("link", name="Textos dels correus").click()
    expect(page.get_by_role("heading", name="Textos dels correus")).to_be_visible()
    review("textos-apartat")

    page.get_by_role("link", name="Canvia: Correu de baixa efectiva").click()
    expect(page.get_by_label("Valor nou")).to_contain_text("des del {data}.")
    page.get_by_label("Valor nou").fill("Baixa feta\n\nHola,\n\nDes del {data} ja no ets soci.")
    page.get_by_role("button", name="Vista prèvia").click()
    expect(page.get_by_text("Des del 31/12/2026 ja no ets soci.")).to_be_visible()
    review("textos-vista-previa")

    page.get_by_label("Valor nou").fill("Baixa feta\n\n<b>Hola</b>")
    page.get_by_role("button", name="Desa el valor").click()
    expect(page.get_by_text("No s'ha desat res.")).to_be_visible()

    page.get_by_label("Valor nou").fill("Baixa feta\n\nHola,\n\nDes del {data} ja no ets soci.")
    page.get_by_label("Nota").fill("Text inventat")
    page.get_by_role("button", name="Desa el valor").click()
    expect(page.get_by_text("Valor desat.")).to_be_visible()
    expect(page.get_by_role("cell", name="Text inventat")).to_be_visible()
    review("textos-desat")
    assert business_settings.get(key).startswith("Baixa feta\n\nHola,")
