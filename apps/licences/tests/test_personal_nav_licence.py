"""T-DX-89: a «La meva llicència» (`licences:mine`, que s'obre des del bloc «Llicència» del perfil)
queda marcada l'entrada «El meu perfil» de la navegació personal, i cap altra (com les subpàgines de
T-DX-76). Fa servir les eines de `apps/core/tests/test_personal_nav_subpages.py`."""

import pytest
from django.urls import reverse

from apps.core.tests.test_personal_nav_subpages import (  # noqa: F401 (fixture)
    NAVS,
    current_links,
    member_account,
    render,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("template", NAVS)
def test_my_licence_marks_the_profile_entry(member_account, template):  # noqa: F811
    html = render(template, member_account, reverse("licences:mine"))
    links = set(current_links(html))
    assert links == {reverse("members:profile")}
