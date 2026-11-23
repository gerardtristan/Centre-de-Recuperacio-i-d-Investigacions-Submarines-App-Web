"""T-DX-90: «Les meves factures» (`invoicing:my_invoices`) té entrada a la navegació personal i al
Ramillete (dins de «Més», B15) i, a la seva pàgina, és l'única entrada marcada; a l'escriptori,
«Més» ja surt obert. Fa servir les eines de `apps/core/tests/test_personal_nav_subpages.py`."""

import pytest
from django.urls import reverse

from apps.core.tests.test_personal_nav_subpages import (  # noqa: F401 (fixture)
    NAVS,
    current_links,
    member_account,
    render,
)

pytestmark = pytest.mark.django_db
URL = reverse("invoicing:my_invoices")


@pytest.mark.parametrize("template", NAVS)
def test_the_invoices_entry_is_shown_and_current(member_account, template):  # noqa: F811
    assert f'href="{URL}"' in render(template, member_account, reverse("core:home"))
    html = render(template, member_account, URL)
    assert set(current_links(html)) == {URL}


def test_the_desktop_more_menu_is_open_on_the_invoices_page(member_account):  # noqa: F811
    html = render("members/_ramillete.html", member_account, URL)
    assert 'aria-expanded="true" aria-controls="ramillete-lateral-mes"' in html


def test_the_invoice_total_is_right_aligned(member_account, login_as):  # noqa: F811
    from apps.accounts.security import AREA_PERSONAL

    html = login_as(member_account, AREA_PERSONAL).get(URL).content.decode()
    assert '<th scope="col" class="cel-import">Total</th>' in html
