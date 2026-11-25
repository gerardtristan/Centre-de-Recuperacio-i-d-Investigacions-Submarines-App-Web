"""T-M07-10 (RN-M07-11, CA-M07-17): a la pantalla de pagar una quota surt «Mira com es fa» i porta
al tutorial publicat, amb els passos. El tutorial es fa amb el servei (les pantalles de WP4
esperen el torn del nucli). Dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.core import audit, charges
from apps.website import help as faq

from .conftest import make_admin

pytestmark = pytest.mark.e2e


def test_a_member_opens_the_tutorial_of_the_payment_screen(
    page, live_server, builder, member, review
):
    faq.save_tutorial(
        None, actor=make_admin("ajuda.prova", "administrator"), title="Com pagar la quota",
        slug="pagar-la-quota", screen_code="payments:charge", published=True,
        steps="Obre «Les meves quotes».\nTria la quota pendent.\nPrem «Paga amb targeta».",
    )  # fmt: skip
    charge = charges.create_charge(
        member.person, kind="fee", amount_cents=9000, concept="Quota de prova",
        origin="proves", by=audit.system("proves-e2e"),
    )  # fmt: skip
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(builder.password)
    page.get_by_role("button", name="Entrar").click()

    page.goto(f"{live_server.url}{reverse('payments:charge', args=[charge.pk])}")
    link = page.get_by_role("link", name="Mira com es fa")
    expect(link).to_be_visible()
    review("tutorial-enllac-pagament")
    link.click()
    expect(page.get_by_role("heading", name="Com pagar la quota")).to_be_visible()
    expect(page.get_by_text("Prem «Paga amb targeta».")).to_be_visible()
    review("tutorial-passos")
