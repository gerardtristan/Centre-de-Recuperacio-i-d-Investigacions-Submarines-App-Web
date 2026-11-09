"""Carnet del soci (T-M01-19; RN-M01-18, RN-M01-19, RN-M01-21, RN-M01-24, RN-M01-25, RN-M01-27;
decisions 069 i 070).

- **Testimoni:** aleatori de 256 bits (`secrets`). Només se'n desa l'empremta SHA-256
  (`MemberCard.token_hash`); el testimoni en clar el torna `issue_card` una sola vegada i no surt
  mai al registre d'activitat (RN-52).
- **Emissió (069, RN-M01-67):** només a un soci actiu amb un pagament confirmat de la quota.
  Cap carnet per a un pendent, ni per a un exempt (P-57), ni amb pagaments parcials (tres
  quotes, P-61).
- **Validesa (RN-M01-18, 070):** carnet no revocat ∧ soci actiu ∧ «pagada fins al» no passat.
  «Vàlid fins al» = 12 mesos després del pagament confirmat (`_paid_until`), mai el 31/12.
  Un impagat té el carnet no revocat «No vàlid»: estat i validesa van separats (D1) i marcar o
  desmarcar l'impagat no toca el carnet (T-M01-12).
- **Revocació:** sempre amb motiu i registre. La criden els fluxos del canvi de tipus, la baixa i
  la petició del soci (RN-M01-25; T-M01-17 i T-M01-22), dins la seva transacció.

Cap altra app escriu en `MemberCard`: ho fa a través d'aquestes funcions.
"""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.models import Charge

from . import roster
from .fee_rules import local_today
from .models import Member, MemberCard

CARD_ISSUED = "members.card.issued"
CARD_REVOKED = "members.card.revoked"
TOKEN_BYTES = 32  # 256 bits (M01-6)


class CardNotAllowed(ValidationError):
    """El soci no pot tenir un carnet nou ara (069) o ja en té un de no revocat."""


@dataclass(frozen=True)
class CardValidity:
    valid: bool
    until: date | None  # «Vàlid fins al»: data de renovació (070), si n'hi ha


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def load_member(member_id):
    # Quotes anuals amb càrrec i pagaments (`roster.with_fee_data`), per a `_paid_until`.
    return roster.with_fee_data(Member.objects.select_related("person", "type")).get(pk=member_id)


def _paid_until(member) -> date | None:
    """Data de renovació del darrer pagament confirmat (070): 12 mesos després. `None` si no n'hi
    ha cap o si alguna quota té pagaments parcials (tres quotes, P-61: cap regla aprovada).

    No es fa servir `roster.fee_state` sencer perquè hi mana «pendent»: una quota de renovació
    generada abans de la data (T-M01-18) no ha de treure la validesa del període ja pagat.

    Socis importats de Cluber (decisió 071, en una altra branca; [A validar: tresorer]): aquí és
    on s'hauria d'afegir la seva data provisional, «Data alta/renovació» + 12 mesos."""
    paid_on = []
    for fee in member.annual_fees:
        payments = list(fee.charge.payments.all())
        if any(p.amount_cents < fee.charge.amount_cents for p in payments):
            return None
        if fee.charge.status != Charge.Status.PAID:
            continue
        if len(payments) != 1 or payments[0].paid_at is None:
            return None
        paid_on.append(timezone.localdate(payments[0].paid_at))
    return roster.twelve_months_after(max(paid_on)) if paid_on else None


def validity(member, card, today=None) -> CardValidity:
    """RN-M01-18 i 070. `member` ve de `roster.with_fee_data`. «Fins al» és inclusiu: el dia de
    la renovació encara és vàlid (supòsit, per revisar)."""
    today = today or local_today()
    until = _paid_until(member)
    valid = (
        card is not None
        and card.revoked_at is None
        and card.member_id == member.pk
        and member.status == Member.Status.ACTIVE
        and until is not None
        and today <= until
    )
    return CardValidity(valid, until)


def active_card(member) -> MemberCard | None:
    return MemberCard.objects.filter(member=member, revoked_at__isnull=True).first()


def valid_card_for_token(token, today=None) -> MemberCard | None:
    """Per a la verificació pública (T-M01-20). Torna el carnet només si és vàlid; un testimoni
    desconegut, revocat, d'un impagat o caducat dona el mateix `None` (RN-M01-27). Igualar el
    temps de resposta i limitar les peticions és de la vista (T-M01-20)."""
    card = (
        MemberCard.objects.filter(token_hash=token_hash(str(token or "")), revoked_at__isnull=True)
        .select_related("member")
        .first()
    )
    if card is None:
        return None
    return card if validity(load_member(card.member_id), card, today).valid else None


def years_of_membership(member, today=None) -> int:
    """RN-M01-21: anys sencers entre `joined_on` i avui."""
    today = today or local_today()
    joined = member.joined_on
    return today.year - joined.year - ((today.month, today.day) < (joined.month, joined.day))


def issue_card(member, *, by, request=None) -> str:
    """Emet un carnet i torna el testimoni en clar (l'únic moment en què existeix). Rebutja un
    soci que no és actiu o sense pagament confirmat (069) i un que ja té carnet: per canviar-lo,
    `replace_card`."""
    with transaction.atomic():
        Member.objects.select_for_update(of=("self",)).get(pk=member.pk)
        loaded = load_member(member.pk)
        if loaded.status != Member.Status.ACTIVE or _paid_until(loaded) is None:
            raise CardNotAllowed(
                _("Només té carnet un soci actiu amb el pagament de la quota confirmat.")
            )
        if active_card(loaded) is not None:
            raise CardNotAllowed(_("Aquest soci ja té un carnet; cal revocar-lo abans."))
        token = secrets.token_urlsafe(TOKEN_BYTES)
        card = MemberCard.objects.create(member=loaded, token_hash=token_hash(token))
        audit.record(CARD_ISSUED, actor=by, target=card, request=request)
    return token


def revoke_card(member, *, by, reason, request=None) -> MemberCard | None:
    """Revoca el carnet no revocat del soci amb motiu (RN-M01-25). Sense carnet, no fa res."""
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal un motiu per revocar el carnet."))
    with transaction.atomic():
        card = (
            MemberCard.objects.select_for_update()
            .filter(member=member, revoked_at__isnull=True)
            .first()
        )
        if card is None:
            return None
        card.revoked_at = timezone.now()
        card.revoked_reason = reason
        card.save(update_fields=["revoked_at", "revoked_reason"])
        audit.record(
            CARD_REVOKED,
            actor=by,
            target=card,
            field="revoked_at",
            old=None,
            new=card.revoked_at.isoformat(),
            reason=reason,
            request=request,
        )
    return card


def replace_card(member, *, by, reason, request=None) -> str:
    """Revoca el carnet actual (si n'hi ha) i n'emet un de nou, tot o res (RN-M01-25)."""
    with transaction.atomic():
        revoke_card(member, by=by, reason=reason, request=request)
        return issue_card(member, by=by, request=request)
