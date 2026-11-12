"""Carnet del soci (T-M01-19; RN-M01-18, RN-M01-19, RN-M01-21, RN-M01-24, RN-M01-25, RN-M01-27;
decisions 069 i 070).

- **Testimoni (079, A-01; RN-M01-85; especificació a docs/planning.md#M01-079-qr):** es calcula
  amb una clau del servidor a partir del soci i de la versió del carnet (`card_keys.token`), i es
  torna a calcular cada vegada que cal mostrar el QR (`qr_token`, `qr_svg`). Només se'n desa
  l'empremta SHA-256 (`MemberCard.token_hash`), la versió i l'identificador de la clau: cap
  secret. Un carnet reemès té una versió nova i un QR diferent. No surt mai al registre
  d'activitat (RN-52). Els carnets anteriors (testimoni aleatori, sense `key_id`) es verifiquen
  igual, però el QR no es pot tornar a mostrar: el soci en demana un de nou.
- **Revocació des de l'administració (079, A-21; P21)** i **carnet nou a petició del soci**
  (RN-M01-25): `revoke_by_admin` i `request_new_card`.
- **Emissió (069, RN-M01-67; 072):** només a un soci actiu amb un «vàlid fins al»: un pagament
  confirmat, l'exempció per edat (P-57) o la renovació de Cluber d'un importat. Cap carnet per a
  un pendent ni amb pagaments parcials (tres quotes, P-61).
- **Validesa (RN-M01-18, 070 i 072):** carnet no revocat ∧ soci actiu ∧ «vàlid fins al» no
  passat. «Vàlid fins al» és el càlcul únic de `validity.valid_until` (079, RN-M01-86): el
  mateix que fan servir l'estat de la quota del llistat i la generació de renovacions.
  Un impagat té el carnet no revocat «No vàlid»: estat i validesa van separats (D1) i marcar o
  desmarcar l'impagat no toca el carnet (T-M01-12).
- **Revocació:** sempre amb motiu i registre. La criden els fluxos del canvi de tipus, la baixa i
  la petició del soci (RN-M01-25; T-M01-17 i T-M01-22), dins la seva transacció.

Cap altra app escriu en `MemberCard`: ho fa a través d'aquestes funcions.
"""

import hashlib
from dataclasses import dataclass
from datetime import date

import qrcode
import qrcode.image.svg
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.permissions import has_perm

from . import card_keys, roster, validity
from .fee_rules import local_today
from .models import Member, MemberCard

CARD_ISSUED = "members.card.issued"
# Decisió 081, punt 15 (RN-M01-101): dies que la còpia sense connexió del carnet es pot mostrar
# després de l'última comprovació. El service worker en té el mateix valor (DIES_COPIA, amb prova).
OFFLINE_COPY_DAYS = 30
CARD_REVOKED = "members.card.revoked"


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


# 079 (A-02, RN-M01-86): el càlcul de «vàlid fins al» és un de sol, a `validity.py`, i el
# comparteixen el carnet, l'estat de la quota i la generació. Aquí només en queden els noms.
valid_until = validity.valid_until
_paid_until = validity.paid_until
_has_partial_payments = validity.has_partial_payments
_birth_date = validity.birth_date
_exempt_until = validity.exempt_until
_cluber_until = validity.cluber_until


def is_exempt(member) -> bool:
    """Exempt per edat i sense cap quota (068, Q-002); `member` ve de `load_member`."""
    return _exempt_until(member) is not None


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


def years_of_membership(member, today=None) -> int | None:
    """RN-M01-21: anys sencers entre `joined_on` i avui. `None` sense data d'alta (Q-075)."""
    today = today or local_today()
    joined = member.joined_on
    if joined is None:
        return None
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
                    "Només té carnet un soci actiu amb la quota pagada o eximida, exempt per "
                    "edat o importat amb la renovació de Cluber."
                )
            )
        if active_card(loaded) is not None:
            raise CardNotAllowed(_("Aquest soci ja té un carnet; cal revocar-lo abans."))
        # 079 (RN-M01-85): versió següent del soci (amb la fila del soci bloquejada) i clau
        # activa. El testimoni es calcula; no es desa enlloc.
        last = MemberCard.objects.filter(member=loaded).aggregate(n=Max("version"))["n"] or 0
        key_id = card_keys.active_key_id()
        token = card_keys.token(loaded.pk, last + 1, key_id)
        card = MemberCard.objects.create(
            member=loaded, token_hash=token_hash(token), version=last + 1, key_id=key_id
        )
        audit.record(
            CARD_ISSUED,
            actor=by,
            target=card,
            details={"version": card.version, "key_id": key_id},
            request=request,
        )
    return token


def qr_token(card) -> str | None:
    """El testimoni del carnet, tornat a calcular (079, RN-M01-85), o `None` si no es pot: un
    carnet anterior a la 079 (sense `key_id`) o una clau que ja no és a la configuració. Es
    comprova contra l'empremta desada: mai no es mostra un testimoni que no sigui el del carnet."""
    if card is None or not card.key_id:
        return None
    token = card_keys.token(card.member_id, card.version, card.key_id)
    if token is None or not constant_time_compare(token_hash(token), card.token_hash):
        return None
    return token


def verification_url(token: str) -> str:
    return settings.PUBLIC_SITE_URL + reverse("members:card_verify", args=[token])


def qr_svg(card) -> str | None:
    """QR amb l'adreça de verificació pública, en SVG generat al servidor (cap servei extern).
    `None` si el testimoni no es pot tornar a calcular."""
    token = qr_token(card)
    if token is None:
        return None
    image = qrcode.make(
        verification_url(token), image_factory=qrcode.image.svg.SvgPathImage, box_size=8
    )
    return image.to_string(encoding="unicode")


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


# --- Revocació des de l'administració i carnet nou a petició del soci (079, RN-M01-92) -------

REVOKE_PERMISSION = "members.card.revoke"  # P21
LIST_PERMISSION = "members.list"  # P4
OWN_REQUEST_REASON = "Carnet nou a petició del soci."


def can_revoke(by, permissions=None) -> bool:
    return has_perm(by, REVOKE_PERMISSION, write=True, permissions=permissions) and has_perm(
        by, LIST_PERMISSION, permissions=permissions
    )


def revoke_by_admin(member, *, by, reason, request=None) -> MemberCard | None:
    """P21 (079, A-21): la secretaria revoca el carnet d'un soci amb motiu. Compte actiu, P21
    amb edició i P4 («no trobat» sense), conflicte d'interès registrat, motiu obligatori. No
    n'emet cap de nou: el soci el demana des de la seva pàgina (`request_new_card`)."""
    from .services import _check_account_active, ensure_not_own_member

    _check_account_active(by)
    if not can_revoke(by):
        raise Http404
    ensure_not_own_member(
        member, by, request=request, message=_("No pots revocar el teu propi carnet.")
    )
    return revoke_card(member, by=by, reason=reason, request=request)


def may_request_new_card(member) -> bool:
    """`member` ve de `load_member`: actiu i amb un «vàlid fins al» (el que demana `issue_card`)."""
    return member.status == Member.Status.ACTIVE and valid_until(member) is not None


def request_new_card(member, *, by, request=None) -> str:
    """RN-M01-25, «petició del soci»: revoca el carnet actual, si n'hi ha, i n'emet un de nou
    amb la clau activa. Qui crida ja ha comprovat que el soci és el de la sessió."""
    return replace_card(member, by=by, reason=OWN_REQUEST_REASON, request=request)


def reissue_for_key(key_id: str, *, by, reason) -> int:
    """Revoca i reemet tots els carnets no revocats emesos amb la clau `key_id` (buit: els
    anteriors a la 079), per a una clau filtrada o retirada (especificació del QR, punt 7).
    Els socis que ja no en poden tenir (no actius o sense «vàlid fins al») es queden amb el
    carnet revocat. Torna quants se n'han reemès."""
    reissued = 0
    members = Member.objects.filter(cards__revoked_at__isnull=True, cards__key_id=key_id)
    for member in members.distinct().order_by("pk"):
        with transaction.atomic():
            revoke_card(member, by=by, reason=reason)
            try:
                issue_card(member, by=by)
            except CardNotAllowed:
                continue
            reissued += 1
    return reissued
