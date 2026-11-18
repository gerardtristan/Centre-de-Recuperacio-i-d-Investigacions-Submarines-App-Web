"""Monograma (T-DX-18): l'avatar per defecte del soci surt només de la llavor (RN-M01-30), mai del
nom, i a la portada i al perfil només hi surt el del soci de la sessió, al compte personal."""

import re
from datetime import date

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.members.models import Member, MembershipType, new_avatar_seed
from apps.members.templatetags.monograma import PATTERNS, render
from apps.members.tests.test_cards import account_for, make_member

SVG = re.compile(r"<svg class=\"monograma .*?</svg>", re.S)


def avatars(html):
    return SVG.findall(html)


def test_the_same_seed_always_gives_the_same_avatar():
    seed = new_avatar_seed()
    assert render(seed) == render(seed)
    assert render(seed).startswith('<svg class="monograma monograma-paleta-')


def test_different_seeds_give_different_avatars_and_every_pattern_appears():
    drawn = [render(new_avatar_seed()) for _ in range(60)]
    assert len(set(drawn)) == 60
    assert {re.search(r'data-patro="(\w+)"', svg)[1] for svg in drawn} == set(PATTERNS)


def test_the_avatar_is_decorative_and_carries_no_colour_or_style():
    svg = render(new_avatar_seed())
    assert 'aria-hidden="true"' in svg and "style=" not in svg and "fill=" not in svg
    assert "#" not in svg and "<title" not in svg and "<text" not in svg


def test_without_a_seed_there_is_no_avatar():
    assert render("") == "" and render(None) == ""


@pytest.mark.django_db
def test_the_name_never_changes_the_avatar():
    seed = new_avatar_seed()
    anna = make_member("Anna", number=1, document="00000001R", avatar_seed=seed)
    berta = make_member("Berta", number=2, document="00000002W")
    assert render(anna.avatar_seed) == render(seed) != render(berta.avatar_seed)
    # Mateix nom, llavors diferents: avatars diferents.
    twin = make_member("Anna", number=3, document="00000003A")
    assert render(twin.avatar_seed) != render(anna.avatar_seed)
    # Corregir el nom no el canvia.
    anna.person.first_name = "Anna Maria"
    anna.person.save()
    anna.refresh_from_db()
    assert render(anna.avatar_seed) == render(seed)


@pytest.mark.django_db
@pytest.mark.parametrize("url", ["core:home", "members:profile"])
def test_home_and_profile_show_only_the_session_member_avatar(login_as, url):
    other = make_member("Berta", number=1300, document="00000000T")
    member = make_member()
    html = login_as(account_for(member), AREA_PERSONAL).get(reverse(url)).content.decode()
    # La portada o el perfil i el panell de navegació (T-DX-59): sempre el del soci de la sessió.
    assert set(avatars(html)) == {render(member.avatar_seed)}
    assert render(other.avatar_seed) not in html


@pytest.mark.django_db
def test_the_admin_account_home_has_no_avatar(login_as, admin_account):
    Member.objects.create(
        person=admin_account.person,
        member_number=1400,
        type=MembershipType.objects.get(code="full"),
        status=Member.Status.ACTIVE,
        joined_on=date(2019, 3, 12),
    )
    html = login_as(admin_account, AREA_ADMIN).get(reverse("core:home")).content.decode()
    assert avatars(html) == []
