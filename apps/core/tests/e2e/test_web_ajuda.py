"""T-M07-09 (P-M07-G; RN-M07-12, CA-M07-16): un visitant cerca a les preguntes freqüents i, sense
resultats, troba l'enllaç al contacte. Les preguntes es fan amb el servei (les pantalles de WP4
esperen el torn del nucli). Dades inventades."""

import pytest
from playwright.sync_api import expect

from apps.core.models import Setting
from apps.website import help as faq

from .conftest import make_admin

pytestmark = pytest.mark.e2e


def test_visitor_searches_the_help(page, live_server, transactional_db, review):
    Setting.objects.filter(key="website.contact_enabled").update(initial_value=True)
    editor = make_admin("ajuda.prova", "administrator")
    fees = faq.save_topic(None, actor=editor, name="Quotes", order=0)
    courses = faq.save_topic(None, actor=editor, name="Cursos", order=1)
    for topic, question, answer in (
        (fees, "Quan es paga la quota?", "Al gener, per domiciliació o amb targeta."),
        (fees, "Puc canviar el mètode de pagament?", "Sí, des de «Les meves quotes»."),
        (courses, "Com m'inscric a un curs?", "Des de la fitxa de l'activitat."),
    ):
        faq.save_entry(None, actor=editor, topic=topic, question=question, answer=answer,
                       published=True)  # fmt: skip

    page.goto(f"{live_server.url}/ajuda/")
    expect(page.get_by_role("heading", name="Preguntes freqüents")).to_be_visible()
    review("ajuda-temes")
    page.get_by_label("Cercar a les preguntes i a les respostes").fill("quota")
    page.get_by_role("button", name="Cerca").click()
    expect(page.get_by_text("1 resposta per «quota».")).to_be_visible()
    expect(page.get_by_text("Al gener, per domiciliació o amb targeta.")).to_be_visible()
    review("ajuda-cerca")
    page.get_by_label("Cercar a les preguntes i a les respostes").fill("immersió nocturna")
    page.get_by_role("button", name="Cerca").click()
    expect(page.get_by_text("No hem trobat cap resposta.")).to_be_visible()
    expect(page.get_by_role("link", name="Escriu al club")).to_be_visible()
    review("ajuda-sense-resultats")
