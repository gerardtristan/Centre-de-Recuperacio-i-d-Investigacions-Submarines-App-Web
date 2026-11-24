"""T-M07-17 (en part): proves de principi a fi del 07 al navegador, amb els interruptors encesos
només aquí. (1) Contacte → safata → resposta (el correu a la cua) → tancar amb motiu.
(2) Subscriure's → confirmar amb el botó (l'enllaç del correu) → redactar i enviar el butlletí →
el correu a la cua amb l'enllaç de baixa → baixa. «Publicar → veure» espera l'editor (106).
Pantalles a 1280, 390 i 320 px. Dades inventades."""

import re
from urllib.parse import urlsplit

import pytest
from django.urls import reverse
from playwright.sync_api import expect
from procrastinate.contrib.django.models import ProcrastinateJob

from apps.core import consents
from apps.core.models import OutgoingEmail, Setting
from apps.website import contact, newsletter
from apps.website.models import ContactMessage, NewsletterSubscription

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e
VISITOR = "visitant.flux@example.org"


def _link_in(email, live_server):
    """L'enllaç del correu, cap al servidor de la prova (el correu porta l'adreça pública)."""
    url = re.search(r"https?://\S+", email.body_text).group(0)
    return live_server.url + urlsplit(url).path


def _write(page, live_server, reason, body):
    page.goto(f"{live_server.url}/contacte/")
    page.get_by_label("Motiu").select_option(label=reason)
    page.get_by_label("Nom", exact=True).fill("Visitant Flux Prova")
    page.get_by_label("Correu electrònic").fill(VISITOR)
    page.get_by_label("Missatge").fill(body)
    page.locator("input[name='accept_privacy']").check()
    page.get_by_role("button", name="Envia el missatge").click()
    expect(page.get_by_text("Missatge enviat")).to_be_visible()


def test_contact_inbox_reply_and_close(page, live_server, texts, review, monkeypatch):
    Setting.objects.filter(key=contact.ENABLED).update(initial_value=True)
    monkeypatch.setattr(contact, "MIN_SECONDS", 0)  # el temps mínim té la seva prova unitària
    _write(page, live_server, "Quotes", "Quan es paga la quota de l'any vinent?")
    _write(page, live_server, "Cursos", "Hi ha curs d'iniciació al gener?")

    login_admin(page, live_server.url, make_admin("secretaria.flux", "secretary").login)
    page.goto(f"{live_server.url}{reverse('administration:website_contact')}")
    expect(page.get_by_role("heading", name="Missatges de contacte")).to_be_visible()
    review("flux-contacte-safata")
    page.get_by_role("row", name="Quotes").get_by_role("link").click()
    page.get_by_label("Resposta", exact=True).fill("Es paga al gener (resposta inventada).")
    review("flux-contacte-resposta")
    page.get_by_role("button", name="Envia la resposta").click()
    expect(page.get_by_text("Resposta enviada.")).to_be_visible()
    reply = OutgoingEmail.objects.get(template=contact.REPLY_TEMPLATE)
    assert reply.to_address == VISITOR and "Es paga al gener" in reply.body_text
    assert reply.status == OutgoingEmail.Status.QUEUED

    page.get_by_role("row", name="Cursos").get_by_role("link").click()
    page.get_by_label("Motiu del tancament").fill("Resolt per telèfon")
    page.get_by_role("button", name="Tanca el missatge").click()
    expect(page.get_by_text("Missatge tancat.")).to_be_visible()
    review("flux-contacte-fet")
    states = dict(ContactMessage.objects.values_list("reason__name", "status"))
    assert states == {"Quotes": "answered", "Cursos": "closed"}


def test_subscribe_confirm_send_and_unsubscribe(page, live_server, texts, review):
    Setting.objects.filter(key=newsletter.ENABLED).update(initial_value=True)
    consents.publish_text("newsletter", "Text de prova: newsletter.", by=texts)
    page.goto(f"{live_server.url}/butlleti/")
    page.get_by_label("Correu electrònic").fill(VISITOR)
    page.locator("input[name='accept_newsletter']").check()
    page.get_by_role("button", name="Subscriu-me").click()
    expect(page.get_by_text("Revisa el correu")).to_be_visible()

    confirmation = OutgoingEmail.objects.get(template=newsletter.CONFIRMATION_TEMPLATE)
    assert confirmation.to_address == VISITOR
    page.goto(_link_in(confirmation, live_server))
    page.get_by_role("button", name="Confirma la subscripció").click()
    expect(page.get_by_text("Subscripció confirmada")).to_be_visible()
    review("flux-butlleti-confirmat")

    login_admin(page, live_server.url, make_admin("presidencia.flux", "president").login)
    page.goto(f"{live_server.url}{reverse('administration:website_newsletter_add')}")
    page.get_by_label("Assumpte").fill("Sortides de gener")
    page.get_by_label("Text", exact=True).fill("Primera sortida a les Medes (text inventat).")
    page.get_by_role("button", name="Desa l'esborrany").click()
    expect(page.get_by_text("Ara l'han de rebre 1 subscripció confirmada.")).to_be_visible()
    page.get_by_label("Confirmo que l'envio ara").check()
    page.get_by_role("button", name="Envia el butlletí").click()
    expect(page.get_by_text("Butlletí a la cua per a 1 destinataris.")).to_be_visible()

    # Fa de treballador de la cua: el lot que ha deixat l'enviament.
    job = ProcrastinateJob.objects.get(task_name="website.send_newsletter_batch")
    newsletter.send_batch(**job.args)
    sent = OutgoingEmail.objects.get(template=newsletter.TEMPLATE)
    assert sent.to_address == VISITOR and sent.priority == OutgoingEmail.Priority.NEWSLETTER
    assert "Primera sortida a les Medes" in sent.body_text and "/butlleti/baixa/" in sent.body_text

    page.goto(_link_in(sent, live_server))
    expect(page.get_by_text("T'has donat de baixa")).to_be_visible()
    review("flux-butlleti-baixa")
    assert NewsletterSubscription.objects.get().status == "unsubscribed"
    page.goto(f"{live_server.url}{reverse('administration:website_newsletters')}")
    page.locator("main").get_by_role("link", name="Sortides de gener").click()
    expect(page.get_by_text("Baixes després de l'enviament")).to_be_visible()
    review("flux-butlleti-recomptes")
