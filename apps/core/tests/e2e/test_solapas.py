"""Solapas, les pestanyes de les fitxes obertes a l'administració (T-DX-07; P-96, opció B).

Obrir fitxes de soci les posa a la tira amb el número i sense el nom; una pestanya porta a la
seva fitxa; arrossegar i Alt+fletxa les reordenen; tancar l'activa obre la de la dreta; la llista
només viu a sessionStorage i «Surt» la buida.
"""

import json

import pytest
from django.conf import settings
from playwright.sync_api import expect

from .conftest import login_admin

pytestmark = pytest.mark.e2e

STORED = "sessionStorage.getItem('cris-solapes')"


def open_member(page, live_server, member):
    page.goto(f"{live_server.url}/{settings.ADMIN_URL_PATH}/socis/{member.pk}/")
    expect(page.get_by_role("heading", level=1, name=str(member.person))).to_be_visible()


def tabs(page):
    return page.get_by_role("navigation", name="Fitxes obertes").locator(".solapes-llista a")


def test_member_files_open_as_tabs_without_names(
    page, live_server, secretary, builder, member, review, page_checks
):
    other = builder.paid_member(
        "Rita",
        "Prova Inventada",
        "rita.prova@example.org",
        builder.full,
        privacy=True,
        membership_terms=True,
    )
    login_admin(page, live_server.url, secretary.login)
    expect(page.get_by_role("navigation", name="Fitxes obertes")).to_be_hidden()
    open_member(page, live_server, member)
    open_member(page, live_server, other)
    expect(tabs(page)).to_have_text([f"Soci {member.member_number}", f"Soci {other.member_number}"])
    expect(tabs(page).nth(1)).to_have_attribute("aria-current", "page")
    stored = page.evaluate(STORED)
    assert "Pere" not in stored and "Rita" not in stored  # cap nom al navegador (P-96)
    review("dues-fitxes")

    # Una pestanya porta a la seva fitxa.
    tabs(page).first.click()
    expect(page.get_by_role("heading", level=1, name=str(member.person))).to_be_visible()

    # Alt+→ la mou a la dreta i el focus s'hi queda.
    tabs(page).first.focus()
    page.keyboard.press("Alt+ArrowRight")
    expect(tabs(page)).to_have_text([f"Soci {other.member_number}", f"Soci {member.member_number}"])
    expect(tabs(page).nth(1)).to_be_focused()

    # Tancar l'activa (la de la dreta, l'última) obre la de l'esquerra.
    page.get_by_role("button", name=f"Tanca Soci {member.member_number}").click()
    expect(page.get_by_role("heading", level=1, name=str(other.person))).to_be_visible()
    expect(tabs(page)).to_have_text([f"Soci {other.member_number}"])

    # «Surt» buida la llista.
    page.get_by_role("button", name="Surt").click()
    assert page.evaluate(STORED) is None


def test_dragging_a_tab_reorders_it(page, live_server, secretary, builder, member, page_checks):
    other = builder.paid_member(
        "Rita",
        "Prova Inventada",
        "rita.prova@example.org",
        builder.full,
        privacy=True,
        membership_terms=True,
    )
    login_admin(page, live_server.url, secretary.login)
    open_member(page, live_server, member)
    open_member(page, live_server, other)
    first, second = tabs(page).nth(0).bounding_box(), tabs(page).nth(1).bounding_box()
    page.mouse.move(first["x"] + 10, first["y"] + first["height"] / 2)
    page.mouse.down()
    page.mouse.move(second["x"] + second["width"] - 5, second["y"] + 5, steps=10)
    page.mouse.up()
    expect(tabs(page)).to_have_text([f"Soci {other.member_number}", f"Soci {member.member_number}"])
    order = [t["etiqueta"] for t in json.loads(page.evaluate(STORED))["llista"]]
    assert order == [f"Soci {other.member_number}", f"Soci {member.member_number}"]
    # Deixar anar no ha obert cap altra fitxa.
    expect(page.get_by_role("heading", level=1, name=str(other.person))).to_be_visible()


def test_unsaved_changes_mark_the_tab_and_closing_asks_first(
    page, live_server, secretary, member, page_checks
):
    login_admin(page, live_server.url, secretary.login)
    open_member(page, live_server, member)
    page.get_by_text("Revoca el carnet…").click()
    page.get_by_label("Motiu de la revocació").fill("Motiu inventat")
    expect(page.locator(".solapa.es-activa")).to_have_class("solapa es-activa es-bruta")
    # En tancar-la, es pregunta; si es diu que no, la fitxa es queda.
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_role("button", name=f"Tanca Soci {member.member_number}").click()
    expect(page.get_by_role("heading", level=1, name=str(member.person))).to_be_visible()
    expect(tabs(page)).to_have_count(1)
