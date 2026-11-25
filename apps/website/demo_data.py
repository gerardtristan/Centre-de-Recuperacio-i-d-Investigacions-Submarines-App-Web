"""Dades inventades del 07 per a `seed_demo_data` (T-M07-17). Mai en producció: les crida l'ordre,
que ja es nega a córrer fora de desenvolupament o amb una base que no és buida.

Missatges de contacte en cada estat (nou, respost i tancat, aquests dos pels serveis de la safata,
amb el registre), subscripcions al butlletí confirmada, pendent i de baixa (pels serveis de
subscripció) i un butlletí en esborrany. Els missatges nous es desen sense el formulari públic
perquè no passin pel límit per origen; cap dada real.
"""

from django.db.models import Max

from apps.core import consents

from . import contact, newsletter
from .models import ContactMessage, ContactReason, Newsletter

MESSAGES = (
    ("Cursos", "Nil Inventat", "nil.inventat@example.org", "Quan comença el curs d'iniciació?"),
    ("Quotes", "Rita Inventada", "rita.inventada@example.org", "Puc pagar la quota en dos cops?"),
    ("Sortides", "Pau Inventat", "pau.inventat@example.org", "Hi ha places per a les Medes?"),
)
SUBSCRIBERS = (
    "subscrit.confirmat@example.org",
    "subscrit.pendent@example.org",
    "subscrit.baixa@example.org",
)


def create(*, secretary, admin) -> dict:
    """`secretary` té WP5 i rep tots els motius inicials (P-486); `admin`, el que redacta."""
    privacy = consents.current_text("privacy")
    rows = [
        ContactMessage.objects.create(
            reason=ContactReason.objects.get(name=reason),
            name=name,
            email=email,
            body=body,
            privacy_text=privacy,
        )
        for reason, name, email, body in MESSAGES
    ]
    contact.reply(rows[1], actor=secretary, answer="Sí: parla amb la tresoreria (inventat).")
    contact.close(rows[2], actor=secretary, reason="Resolt per telèfon")

    text = consents.current_text(newsletter.TEXT_KIND)
    confirmed, pending, gone = (
        newsletter.subscribe(email, legal_text=text)[0] for email in SUBSCRIBERS
    )
    newsletter.confirm(confirmed.token)
    newsletter.unsubscribe(gone.token)

    # El butlletí és apagat (P-42): `save_draft` el rebutjaria; l'esborrany es desa directament.
    number = (Newsletter.objects.aggregate(last=Max("number"))["last"] or 0) + 1
    Newsletter.objects.create(
        number=number, subject="Sortides de primavera (inventat)", created_by=admin,
        body="Aquest any farem tres sortides a la Costa Brava.\n\nInscripcions aviat.",
    )  # fmt: skip
    return {"messages": len(rows), "subscriptions": len(SUBSCRIBERS), "drafts": 1}
