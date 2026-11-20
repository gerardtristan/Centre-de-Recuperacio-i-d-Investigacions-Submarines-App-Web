"""V23 (revisió final, T-F1-01): un codi TOTP o de recuperació no es torna a mostrar mai després
d'un error del formulari, com la contrasenya. Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.forms import (
    CodeForm,
    DisableTotpForm,
    PersonalTotpResetForm,
    ReauthForm,
    ResetCredentialsForm,
)
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.views.roles import ConfirmForm
from apps.members.forms import FeeResolveForm

CODE = "482913"


@pytest.mark.parametrize(
    "form",
    [
        CodeForm({"code": CODE}),
        DisableTotpForm({"code": CODE}),  # falta la contrasenya
        ReauthForm({"code": CODE}, has_totp=True),
        FeeResolveForm({"code": CODE, "password": "x"}, has_totp=True),  # falta el motiu
        ResetCredentialsForm({"code": CODE}),
        PersonalTotpResetForm({"code": CODE}),
        ConfirmForm({"code": CODE}),
    ],
    ids=lambda form: type(form).__name__,
)
def test_the_code_is_never_rendered_again(form):
    form.is_valid()
    assert CODE not in str(form)
    assert CODE not in str(form["code"])


@pytest.mark.django_db
def test_a_screen_with_an_error_does_not_show_the_code(make_admin):  # noqa: F811
    """Eximir una quota sense motiu: el formulari torna amb l'error i sense el codi enviat."""
    from apps.members.tests.test_cards import make_member
    from apps.members.tests.test_exemption_040 import fee_for
    from apps.members.tests.test_roster import admin_client

    member = make_member()
    fee = fee_for(member)
    client = admin_client(make_admin("treasurer"))
    url = reverse("administration:member_fee_exempt", args=[member.pk, fee.pk])
    response = client.post(url, {"reason": "", "password": "x", "code": CODE})
    assert response.status_code == 200
    assert "Cal el motiu." in response.content.decode()
    assert CODE not in response.content.decode()
