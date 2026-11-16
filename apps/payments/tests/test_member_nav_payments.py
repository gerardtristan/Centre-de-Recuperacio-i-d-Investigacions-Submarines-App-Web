"""Navegació de l'àrea del soci (T-DX-45): «Com pago la quota» per a tots els socis, i «Mandat de
domiciliació» només amb MANDATE_SIGNING_ENABLED, a la capçalera i al ventall de Ramillete."""

import re

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL
from apps.members.tests.test_cards import account_for, make_member

pytestmark = pytest.mark.django_db


def navs(html):
    head = re.search(r'<nav class="navegacio-compte".*?</nav>', html, re.S).group(0)
    fan = re.search(r'<nav class="ramillete".*?</nav>', html, re.S).group(0)
    return head, fan


def home(login_as, account):
    return login_as(account, AREA_PERSONAL).get(reverse("core:home")).content.decode()


@pytest.mark.parametrize("enabled", [False, True])
def test_member_sees_fee_method_and_mandate_only_when_enabled(login_as, settings, enabled):
    settings.MANDATE_SIGNING_ENABLED = enabled
    for nav in navs(home(login_as, account_for(make_member()))):
        assert reverse("payments:fee_method") in nav
        assert (reverse("payments:mandate") in nav) == enabled


def test_a_person_who_is_not_a_member_sees_neither(login_as, settings, personal_account):
    settings.MANDATE_SIGNING_ENABLED = True
    for nav in navs(home(login_as, personal_account)):
        assert reverse("payments:fee_method") not in nav and reverse("payments:mandate") not in nav
