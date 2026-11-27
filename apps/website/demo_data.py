"""Dades inventades del 07 per a `seed_demo_data` (T-M07-17). Mai en producció: les crida l'ordre,
que ja es nega a córrer fora de desenvolupament o amb una base que no és buida.

Missatges de contacte en cada estat (nou, respost i tancat, aquests dos pels serveis de la safata,
amb el registre), subscripcions al butlletí confirmada, pendent i de baixa (pels serveis de
subscripció) i un butlletí en esborrany. Els missatges nous es desen sense el formulari públic
perquè no passin pel límit per origen; cap dada real.
"""

import re

from django.conf import settings

from apps.core import consents

from . import contact, media, newsletter
from .models import ContactMessage, ContactReason, Newsletter

# Fotos reals del club per a plantilles, mostres i captures (decisió 107; T-M07-20b). Només en
# local: les carrega aquesta ordre, que no corre fora de desenvolupament ni amb dades.
PHOTOS = settings.BASE_DIR / "static" / "img" / "web" / "cris1954"
_ENTRY = re.compile(r"^\s*-\s*fitxer:\s*(.+)$|^\s+(\w+):\s*(.+)$")

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
    Newsletter.objects.create(
        number=newsletter._next_number(), created_by=admin,
        subject="Sortides de primavera (inventat)",
        body="Aquest any farem tres sortides a la Costa Brava.\n\nInscripcions aviat.",
    )  # fmt: skip
    photos = load_photos(admin)
    return {"messages": len(rows), "subscriptions": len(SUBSCRIBERS), "drafts": 1,
            "photos": len(photos)}  # fmt: skip


def _entries(text: str) -> list[dict]:
    """Les entrades de `fotos.yml`. shortcut: només el format pla d'aquest fitxer (sense PyYAML);
    si es complica, cal la llibreria."""
    entries = []
    for line in text.splitlines():
        match = _ENTRY.match(line)
        if match and match.group(1):
            entries.append({"fitxer": match.group(1).strip()})
        elif match and entries:
            entries[-1][match.group(2)] = match.group(3).strip().strip('"').strip("«»")
    return entries


def load_photos(actor) -> list:
    """Les fotos de `fotos.yml` a la biblioteca de la web, amb l'autor, el permís, el text
    alternatiu i si hi surten persones (amb el seu permís d'imatge, 107). Sense el fitxer, cap."""
    index = PHOTOS / "fotos.yml"
    if not index.exists():
        return []
    assets = []
    for entry in _entries(index.read_text(encoding="utf-8")):
        path = PHOTOS / entry["fitxer"]
        if path.suffix.lower() not in (".jpg", ".jpeg", ".png") or not path.exists():
            continue
        people = entry.get("persones") == "sí"
        assets.append(media.store_image(
            path.read_bytes(), actor=actor, alt_text=entry.get("alt", "")[:300],
            shows_people=people, people_consent=people, author=entry.get("autor", "C.R.I.S."),
            licence_note=entry.get("permis", "")[:300],
        ))  # fmt: skip
    return assets
