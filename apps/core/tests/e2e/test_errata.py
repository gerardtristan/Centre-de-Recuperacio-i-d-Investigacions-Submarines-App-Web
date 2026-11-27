"""Errata, el resum d'errors (T-DX-06), al formulari «Fer-se soci»: si el servidor torna el
formulari amb errors, a dalt surt «Hi ha N errors» amb el focus, un enllaç per camp que hi porta,
i el mateix missatge que al costat del camp.
"""

import re

import pytest
from playwright.sync_api import expect

from .conftest import login_visitor

pytestmark = pytest.mark.e2e


def test_join_form_with_errors_shows_the_summary_and_links_to_each_field(
    page, live_server, review, page_checks, texts
):
    login_visitor(page, live_server.url)  # T-M01-53: amb sessió
    page.get_by_role("button", name="Envia la sol·licitud").click()

    summary = page.locator("[data-errata]")
    expect(summary).to_be_visible()
    expect(summary).to_be_focused()
    title = summary.get_by_role("heading")
    expect(title).to_have_text(re.compile(r"Hi ha \d+ errors?"))
    links = summary.locator("a.errata-element")
    count = links.count()
    assert count >= 2
    assert title.inner_text() == f"Hi ha {summary.locator('li').count()} errors"
    review("fer-se-soci-amb-errors")

    # El primer enllaç porta al camp amb error i hi deixa el focus.
    target = links.first.get_attribute("href").lstrip("#")
    links.first.click()
    field = page.locator(f"#{target}")
    expect(field).to_be_focused()
    expect(field).to_have_attribute("aria-invalid", "true")


def test_without_errors_there_is_no_summary(page, live_server, page_checks, texts):
    login_visitor(page, live_server.url)  # T-M01-53: amb sessió
    expect(page.locator("[data-errata]")).to_have_count(0)
