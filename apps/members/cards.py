"""Carnet del soci (T-M01-19; RN-M01-18, RN-M01-19, RN-M01-21, RN-M01-24, RN-M01-25, RN-M01-27;
decisions 069 i 070).

- **Testimoni:** aleatori de 256 bits (`secrets`). Només se'n desa l'empremta SHA-256
  (`MemberCard.token_hash`); el testimoni en clar el torna `issue_card` una sola vegada i no surt
  mai al registre d'activitat (RN-52).
- **Emissió (069, RN-M01-67; 072):** només a un soci actiu amb un «vàlid fins al»: un pagament
  confirmat, l'exempció per edat (P-57) o la renovació de Cluber d'un importat. Cap carnet per a
  un pendent ni amb pagaments parcials (tres quotes, P-61).
- **Validesa (RN-M01-18, 070 i 072):** carnet no revocat ∧ soci actiu ∧ «vàlid fins al» no
  passat. «Vàlid fins al» (`valid_until`) és la data més tardana d'aquestes:
  - els que paguen: un any des del pagament confirmat, fins al mateix dia de l'any següent
    (`roster.twelve_months_after`; el 29/02 passa al 28/02);
  - els exempts per edat sense cap quota: el 31/12 de l'últim any exempt (Q-002), mai el càlcul
    anterior;
  - els importats de Cluber: un any des de «Data alta/renovació» (`cluber_renewed_on`, Q-076)
    [A validar: tresorer].
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
from .fee_rules import first_fee_year, local_today
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
    generada abans de la data (T-M01-18) no ha de treure la validesa del període ja pagat."""
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


def _has_partial_payments(member) -> bool:
    return any(
        p.amount_cents < fee.charge.amount_cents
        for fee in member.annual_fees
        for p in fee.charge.payments.all()
    )


def _birth_date(member) -> date | None:
    """La de la persona (T-M01-33) o, si encara no hi és, la declarada a l'alta aprovada."""
    if member.person.birth_date:
        return member.person.birth_date
    joins = member.person.approved_joins
    return joins[0].birth_date if joins else None


def _exempt_until(member) -> date | None:
    """Q-002 (072): exempt per edat i sense cap quota, fins al 31/12 de l'últim any exempt (l'any
    abans del primer any de quota, 068). Passat aquest dia, ja no compta: cal la quota (Q-003)."""
    if member.annual_fees:
        return None
    birth = _birth_date(member)
    return date(first_fee_year(birth) - 1, 12, 31) if birth else None


def _cluber_until(member) -> date | None:
    """Q-076 (072): un any des de «Data alta/renovació» de Cluber [A validar: tresorer]."""
    renewed = member.cluber_renewed_on
    return roster.twelve_months_after(renewed) if renewed and member.cluber_id else None


def valid_until(member) -> date | None:
    """«Vàlid fins al» del soci (vegeu el docstring del mòdul). `None` si no en té cap o si hi ha
    pagaments parcials, que no tenen cap regla aprovada (P-61). `member` ve de `load_member`."""
    if _has_partial_payments(member):
        return None
    dates = [d for d in (_paid_until(member), _exempt_until(member), _cluber_until(member)) if d]
    return max(dates) if dates else None


def validity(member, card, today=None) -> CardValidity:
    """RN-M01-18, 070 i 072. `member` ve de `roster.with_fee_data`. «Fins al» és inclusiu: el dia
    de la renovació encara és vàlid (supòsit, per revisar)."""
    today = today or local_today()
    until = valid_until(member)
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
        .select_related("member__person")
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
    soci que no és actiu o sense cap «vàlid fins al» (069 i 072) i un que ja té carnet: per
    canviar-lo, `replace_card`."""
    with transaction.atomic():
        Member.objects.select_for_update(of=("self",)).get(pk=member.pk)
        loaded = load_member(member.pk)
        if loaded.status != Member.Status.ACTIVE or valid_until(loaded) is None:
            raise CardNotAllowed(
                _(
                    "Només té carnet un soci actiu amb la quota pagada, exempt per edat o "
                    "importat amb la renovació de Cluber."
                )
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
