"""T-M07-34 (decisió 108, C.6): l'avís discret del butlletí a l'inici de l'àrea del soci. Una
sòcia no subscrita el veu, el tanca amb «Ara no, gràcies» i ja no hi torna a sortir. Pantalles a
1280, 390 i 320 px (clar i fosc). Dades inventades."""

import pytest
from playwright.sync_api import expect

from apps.activities.tests.helpers import a_member
from apps.core import consents
from apps.core.models import Setting
from apps.website import newsletter
from apps.website.models import NewsletterNoticeDismissal
from conftest import PASSWORD

pytestmark = pytest.mark.e2e
NOTICE = "Vols rebre les sortides, els cursos i les novetats del C.R.I.S.?"


def test_a_member_sees_and_closes_the_newsletter_notice(page, live_server, texts, review):
    Setting.objects.filter(key=newsletter.ENABLED).update(initial_value=True)
    consents.publish_text("newsletter", "Text de prova: newsletter.", by=texts)
    account = a_member("Sòcia")
    account.set_password(PASSWORD)
    account.save()
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()

    expect(page.get_by_text(NOTICE)).to_be_visible()
    review("avis-butlleti")
    page.get_by_role("button", name="Ara no, gràcies").click()
    expect(page.get_by_role("heading", name="Plataforma del C.R.I.S.")).to_be_visible()
    expect(page.get_by_text(NOTICE)).to_have_count(0)
    review("avis-butlleti-tancat")
    assert NewsletterNoticeDismissal.objects.filter(account=account).exists()
