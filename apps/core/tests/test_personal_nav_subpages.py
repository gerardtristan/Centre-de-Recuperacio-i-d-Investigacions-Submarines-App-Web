"""Navegació de l'àrea del soci (T-DX-76, V19 i V4): a les subpàgines (pagar una quota, el rebut,
la targeta guardada, revocar el mandat, el perfil, el carnet nou, el doble factor) queda marcada
l'entrada d'on s'obren, i cap altra. A la pàgina de les polítiques no hi ha menú: les entrades hi
tornarien a portar (ImportedPoliciesMiddleware)."""

import re

import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.urls import resolve, reverse

from apps.members.tests.test_personal_area import make_account, make_member, make_person

pytestmark = pytest.mark.django_db

NAVS = ("members/_personal_nav.html", "members/_ramillete.html")

# Ruta (amb arguments inventats: només es resol, no s'obre) i l'entrada que ha de quedar marcada.
PAGES = [
    (("payments:charge", 1), "members:fees"),
    (("payments:pay_card", 1), "members:fees"),
    (("payments:attempt_status", 1), "members:fees"),
    (("payments:receipt", 1), "members:fees"),
    (("members:fee_instalments", 1), "members:fees"),
    (("payments:saved_card",), "payments:fee_method"),
    (("payments:saved_card_remove",), "payments:fee_method"),
    (("payments:mandate_revoke",), "payments:mandate"),
    (("members:consent",), "members:profile"),
    (("members:birth_date",), "members:profile"),
    (("members:erase",), "members:profile"),
    (("members:export_data",), "members:profile"),
    (("members:card_renew",), "members:card"),
    (("accounts:totp_enrol",), "accounts:security"),
    (("activities:my_certification_photo", 1), "activities:my_certifications"),  # T-DX-117
]


@pytest.fixture
def member_account(settings):
    settings.MANDATE_SIGNING_ENABLED = True
    person = make_person("Anna", "76")
    make_member(person, 476)
    return make_account(person, "anna.76@example.org")


def render(template, account, url):
    request = RequestFactory().get(url)
    request.user = account
    request.resolver_match = resolve(url)
    return render_to_string(template, {"request": request, "user": account})


def current_links(html):
    return re.findall(r'href="([^"]+)"[^>]*aria-current="page"', html)


@pytest.mark.parametrize(("route", "entry"), PAGES)
@pytest.mark.parametrize("template", NAVS)
def test_the_entry_of_the_section_is_current_on_its_sub_pages(
    member_account, template, route, entry
):
    name, *args = route
    html = render(template, member_account, reverse(name, args=args))
    links = set(current_links(html))
    if template.endswith("_personal_nav.html") and entry == "accounts:security":
        assert links == set()  # la navegació sense JavaScript no té «Seguretat i aparença»
    else:
        assert links == {reverse(entry)}


@pytest.mark.parametrize("template", NAVS)
def test_no_menu_on_the_policies_page(member_account, template):
    html = render(template, member_account, reverse("members:accept_policies"))
    assert "<nav" not in html


@pytest.mark.parametrize("template", NAVS)
def test_newsletter_entry_only_with_the_setting(member_account, template):
    """T-DX-148: «Butlletí» surt amb `website.newsletter_enabled` encès (com la vista) i queda
    marcat a la seva pàgina; apagat, el menú no hi enllaça."""
    from apps.core.models import Setting
    from apps.website import newsletter

    url = reverse("website:my_newsletter")
    assert url not in render(template, member_account, reverse("core:home"))
    Setting.objects.filter(key=newsletter.ENABLED).update(initial_value=True)
    assert set(current_links(render(template, member_account, url))) == {url}
