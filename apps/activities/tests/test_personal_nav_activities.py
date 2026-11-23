"""T-DX-95: «Les meves activitats» (`activities:mine`) té entrada a la navegació personal i al
Ramillete («Activitats»), i a la seva pàgina i a la inscripció del soci és l'única entrada marcada.
Fa servir les eines de `apps/core/tests/test_personal_nav_subpages.py`."""

import pytest
from django.urls import reverse

from apps.core.tests.test_personal_nav_subpages import (  # noqa: F401 (fixture)
    NAVS,
    current_links,
    member_account,
    render,
)

pytestmark = pytest.mark.django_db
URL = reverse("activities:mine")


@pytest.mark.parametrize("template", NAVS)
@pytest.mark.parametrize("page", [URL, reverse("activities:member_enrol", args=[1])])
def test_the_activities_entry_is_shown_and_current(member_account, template, page):  # noqa: F811
    assert f'href="{URL}"' in render(template, member_account, reverse("core:home"))
    assert set(current_links(render(template, member_account, page))) == {URL}
