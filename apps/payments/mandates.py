"""Desar un mandat SEPA amb l'IBAN xifrat (T-M05a-08; RN-M05a-02, 03, 05 i 06; decisió 044).

La signatura (text vigent i reautenticació de RN-M05a-12) és a `mandate_views`, que crida
`create_mandate` (T-M05a-09). Cap missatge d'error, registre ni entrada del registre d'activitat
porta l'IBAN.
"""

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext

from apps.core import audit, mail
from apps.members import recipients
from apps.members.models import Member

from . import crypto
from .models import MandateBankAccount, SepaMandate

SIGNED_TEMPLATE = "mandat-signat"  # G3
EXPIRED_TEMPLATE = "mandat-caducat"
IBAN_FORMAT = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}")


def validate_iban(value: str) -> str:
    """L'IBAN normalitzat (sense espais, en majúscules) si el format i els dígits de control
    (mòdul 97, ISO 13616) són correctes. L'error no porta el valor (RN-M05a-05)."""
    iban = re.sub(r"\s+", "", value or "").upper()
    if IBAN_FORMAT.fullmatch(iban):
        digits = "".join(str(int(char, 36)) for char in iban[4:] + iban[:4])
        if int(digits) % 97 == 1:
            return iban
    raise ValidationError(gettext("L'IBAN no és vàlid. Revisa'l i torna-ho a provar."))


def next_reference(member: Member) -> str:
    """La referència que tindrà el mandat següent del soci (RN-M05a-03): mai se'n reutilitza
    cap, perquè els mandats no s'esborren."""
    ordinal = SepaMandate.objects.filter(member=member).count() + 1
    return f"CRIS{member.member_number:06d}M{ordinal:02d}"


@transaction.atomic
def create_mandate(
    member: Member,
    *,
    iban: str,
    holder_name: str,
    holder_is_member: bool,
    legal_text,
    account,
    creditor_identifier: str,
    evidence: dict,
) -> SepaMandate:
    """Desa un mandat actiu i l'IBAN xifrat. L'anterior actiu passa a revocat amb el motiu
    «substituït» (RN-M05a-02). La referència és la de RN-M05a-03 i no es reutilitza."""
    iban = validate_iban(iban)
    # Bloqueja el soci: dues signatures alhora no poden prendre el mateix ordinal.
    member = Member.objects.select_for_update().get(pk=member.pk)
    if member.member_number is None:
        raise ValueError("El soci encara no té número: no pot signar cap mandat.")
    reference = next_reference(member)
    now = timezone.now()
    for previous in SepaMandate.objects.filter(member=member, status=SepaMandate.Status.ACTIVE):
        previous.status = SepaMandate.Status.REVOKED
        previous.revoked_at, previous.revoked_reason, previous.revoked_by = (
            now,
            SepaMandate.REPLACED,
            account,
        )
        previous.save(update_fields=["status", "revoked_at", "revoked_reason", "revoked_by"])
        audit.record(
            "payments.mandate.revoked",
            actor=account,
            target=previous,
            reason=SepaMandate.REPLACED,
            details={"reference": previous.reference, "replaced_by": reference},
        )
    mandate = SepaMandate.objects.create(
        member=member,
        reference=reference,
        holder_name=holder_name,
        holder_is_member=holder_is_member,
        signed_at=now,
        creditor_identifier=creditor_identifier,
        legal_text=legal_text,
        signed_by_account=account,
        evidence=evidence,
    )
    version, ciphertext = crypto.encrypt(iban)
    MandateBankAccount.objects.create(
        mandate=mandate,
        iban_ciphertext=ciphertext,
        key_version=version,
        iban_country=iban[:2],
        iban_last4=iban[-4:],
    )
    audit.record(
        "payments.mandate.created",
        actor=account,
        target=mandate,
        details={"reference": reference, "legal_text": legal_text.pk},
    )
    return mandate


def mail_member(template: str, mandate: SepaMandate) -> None:
    """Correu al soci del mandat (al representant, si és menor: RN-M01-78), per la cua: el G3 en
    signar-lo (CA-M05a-04) i l'avís de caducitat (RN-M05a-08). Porta la referència,
    l'identificador de creditor, la data i l'IBAN emmascarat (P-121); mai l'IBAN sencer."""
    person = mandate.member.person
    to = recipients.email_for(person)
    if not to:
        return
    context = {
        "reference": mandate.reference,
        "creditor": mandate.creditor_identifier,
        "signed_on": timezone.localdate(mandate.signed_at),
        "masked_iban": str(mandate.bank_account),
        "link": settings.PUBLIC_SITE_URL + reverse("payments:mandate"),
    }
    mail.queue_email(template, to=to, person=person, context=context)
