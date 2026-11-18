"""Desar un mandat SEPA amb l'IBAN xifrat (T-M05a-08; RN-M05a-02, 03, 05 i 06; decisió 044).

La signatura (text vigent i reautenticació de RN-M05a-12) és a `mandate_views`, que crida
`create_mandate` (T-M05a-09). Cap missatge d'error, registre ni entrada del registre d'activitat
porta l'IBAN.
"""

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext
from django.views.decorators.debug import sensitive_variables

from apps.accounts.models import Account
from apps.core import audit, business_settings, mail
from apps.core.models import Setting
from apps.core.permissions import has_perm
from apps.members import recipients
from apps.members.models import Member

from . import crypto, preferences, processing
from .models import (
    DirectDebitItem,
    DirectDebitRemittance,
    FeeMethod,
    MandateBankAccount,
    SepaMandate,
)

SIGNED_TEMPLATE = "mandat-signat"  # G3
EXPIRED_TEMPLATE = "mandat-caducat"
REVOKED_TEMPLATE = "mandat-revocat"
REVOKED_IN_REMITTANCE_TEMPLATE = "avis-mandat-revocat-remesa"  # RN-M05a-09 (T-M05a-10b)
REVOKED_IN_REMITTANCE = "payments.mandate.revoked_in_remittance"
REVOKE = "payments.mandates.revoke"  # A6 (M05a-4)
MEMBER_REQUEST = "a petició del soci"  # motiu de la revocació des del compte personal
IBAN_FORMAT = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}")
# P-123 (095, provisional fins que el banc ho confirmi): països admesos al mandat, un ajust que
# edita el Tresorer; de bon principi, tota la zona SEPA (`payments/0024`).
# La clau no diu «iban»: el registre d'activitat rebutja els camps amb aquest nom (RN-52).
IBAN_COUNTRIES = "payments.mandate_countries"
COUNTRY = re.compile(r"[A-Z]{2}")
# Codis de país de l'IBAN (registre ISO 13616) dels països i territoris de la zona SEPA amb IBAN
# propi [A verificar: banc]. Els que fan servir l'IBAN d'un altre país (Åland amb FI) ja hi són.
SEPA_COUNTRIES = frozenset(
    "AD AL AT BE BG CH CY CZ DE DK EE ES FI FR GB GI GR HR HU IE IS IT LI LT LU LV MC MD ME MK "
    "MT NL NO PL PT RO SE SI SK SM VA".split()
)

# Països amb IBAN del registre ISO 13616 (SWIFT) [A verificar: registre vigent]: la llista
# admesa en pot tenir qualsevol (p. ex. RS, si el banc l'admet), però no un codi que no existeix.
IBAN_REGISTRY = frozenset(
    "AD AE AL AT AZ BA BE BG BH BI BR BY CH CR CY CZ DE DJ DK DO EE EG ES FI FK FO FR GB GE GI "
    "GL GR GT HN HR HU IE IL IQ IS IT JO KW KZ LB LC LI LT LU LV LY MC MD ME MK MN MR MT MU NI "
    "NL NO OM PK PL PS PT QA RO RS RU SA SC SD SE SI SK SM SO ST SV TL TN TR UA VA VG XK YE".split()
)


class CountryNotAllowed(ValidationError):
    """L'IBAN és vàlid, però el país no és a la llista admesa (P-123)."""


def validate_iban(value: str) -> str:
    """L'IBAN normalitzat (sense espais, en majúscules) si el format i els dígits de control
    (mòdul 97, ISO 13616) són correctes. L'error no porta el valor (RN-M05a-05)."""
    iban = re.sub(r"\s+", "", value or "").upper()
    if IBAN_FORMAT.fullmatch(iban):
        digits = "".join(str(int(char, 36)) for char in iban[4:] + iban[:4])
        if int(digits) % 97 == 1:
            return iban
    raise ValidationError(gettext("L'IBAN no és vàlid. Revisa'l i torna-ho a provar."))


def check_countries(value: str) -> None:
    """La comprovació de l'ajust, que `apps.PaymentsConfig.ready` registra a la peça d'ajustos:
    almenys un país, codis de dues lletres de països amb IBAN i sense repetir."""
    found = business_settings.split_list(value)
    if not found:
        raise ValidationError(gettext("Hi ha d'haver almenys un país."))
    if not all(COUNTRY.fullmatch(code) for code in found):
        raise ValidationError(
            gettext(
                "Cada país és el codi de dues lletres de l'IBAN (per exemple, ES). Separa'ls amb "
                "comes, espais o punts i comes."
            )
        )
    if unknown := sorted(set(found) - IBAN_REGISTRY):
        raise ValidationError(
            gettext("Aquest codi no és cap país amb IBAN: %(codes)s.")
            % {"codes": ", ".join(unknown)}
        )
    if len(set(found)) != len(found):
        raise ValidationError(gettext("La llista no pot tenir països repetits."))


def iban_countries() -> set[str]:
    """Els països admesos, amb el valor vigent avui (P-123). Sense l'ajust, la zona SEPA."""
    try:
        return set(business_settings.split_list(business_settings.get(IBAN_COUNTRIES)))
    except Setting.DoesNotExist:
        return set(SEPA_COUNTRIES)


def check_country(iban: str) -> None:
    """`CountryNotAllowed` si el país de l'IBAN (ja validat) no és a la llista admesa (P-123).
    L'error no porta el valor."""
    if iban[:2] not in iban_countries():
        raise CountryNotAllowed(
            gettext("El banc del club no admet IBAN d'aquest país per domiciliar.")
        )


def validate_mandate_iban(value: str) -> str:
    """`validate_iban` i, a més, el país admès (P-M05a-B, pas 2; estat «País no admès» del
    wireframe). La crida `create_mandate`; la vista ja ho mira abans de la reautenticació, i
    aquí es torna a mirar per si la llista ha canviat entremig. Les remeses no ho tornen a
    mirar: un mandat signat continua valent encara que el país es tregui de la llista."""
    iban = validate_iban(value)
    check_country(iban)
    return iban


def next_reference(member: Member) -> str:
    """La referència que tindrà el mandat següent del soci (RN-M05a-03): mai se'n reutilitza
    cap, perquè els mandats no s'esborren."""
    ordinal = SepaMandate.objects.filter(member=member).count() + 1
    return f"CRIS{member.member_number:06d}M{ordinal:02d}"


def _revoke(mandate: SepaMandate, reason: str, by, now, **details) -> None:
    mandate.status = SepaMandate.Status.REVOKED
    mandate.revoked_at, mandate.revoked_reason, mandate.revoked_by = now, reason, by
    mandate.save(update_fields=["status", "revoked_at", "revoked_reason", "revoked_by"])
    audit.record(
        "payments.mandate.revoked",
        actor=by,
        target=mandate,
        reason=reason,
        details={"reference": mandate.reference, **details},
    )


def _is_own(account, member) -> bool:
    # Només el compte personal: un compte d'administrador no té accions pròpies (059, punt 4.2).
    personal = getattr(account, "kind", None) == Account.Kind.PERSONAL
    return personal and account.person_id == member.person_id


@transaction.atomic
def revoke_mandate(member: Member, *, by, reason: str = MEMBER_REQUEST) -> SepaMandate | None:
    """Revoca el mandat actiu del soci (P-M05a-C): ell mateix des del compte personal o el tresorer
    a petició escrita, amb el motiu (A6). Passa a «revocat» amb la data i el motiu, i la
    preferència, si era la domiciliació (o no n'hi havia), passa a «pagar cada vegada». El soci
    rep un correu (`mandat-revocat`), a la mateixa transacció, per la cua. Torna el mandat, o
    None si no n'hi havia cap d'actiu. Funciona encara que la signatura estigui apagada (P-127):
    un soci sempre ha de poder revocar. Ningú més, sense A6: «no trobat» (T-M05a-25)."""
    if not (_is_own(by, member) or has_perm(by, REVOKE, write=True)):
        raise Http404
    mandate = (
        SepaMandate.objects.select_for_update()
        .filter(member=member, status=SepaMandate.Status.ACTIVE)
        .first()
    )
    if mandate is None:
        return None
    _revoke(mandate, reason, by, timezone.now())
    mail_member(REVOKED_TEMPLATE, mandate)
    preference = preferences.current(member)
    if preference is None or preference.method == FeeMethod.DIRECT_DEBIT:
        preferences.set_preference(member, FeeMethod.PAY_EACH_TIME, by=by)
    _warn_if_at_the_bank(mandate, by)
    return mandate


def _warn_if_at_the_bank(mandate: SepaMandate, by) -> None:
    """RN-M05a-09 (L-M05a-04, L-M05b-03): si un rebut del mandat és en una remesa que ja pot ser
    al banc (enviada, o avisada amb el fitxer descarregat), el banc el presentarà igualment: avís
    a qui té la tresoreria i registre. Avisada sense fitxer, no cal: el fitxer ja no es pot
    generar (`sepa_xml.MandateNoLongerActive`). Un mandat només es revoca una vegada: un sol
    avís. Només referències internes, cap IBAN ni cap nom."""
    S = DirectDebitRemittance.Status
    at_the_bank = Q(remittance__status=S.SENT_TO_BANK) | (
        Q(remittance__status=S.NOTIFIED) & ~Q(remittance__file_hash="")
    )
    remittances = sorted(
        {
            item.remittance
            for item in DirectDebitItem.objects.filter(
                at_the_bank, mandate=mandate, status=DirectDebitItem.Status.INCLUDED
            ).select_related("remittance")
        },
        key=lambda remittance: remittance.pk,
    )
    if not remittances:
        return
    processing.notify_treasurers(
        REVOKED_IN_REMITTANCE_TEMPLATE,
        {
            "reference": mandate.reference,
            "remittances": [
                {"period": r.period, "collection_date": r.collection_date} for r in remittances
            ],
        },
    )
    audit.record(
        REVOKED_IN_REMITTANCE,
        actor=by,
        target=mandate,
        details={"reference": mandate.reference, "remittances": [r.pk for r in remittances]},
    )


# Un error dins (la clau, la base de dades) no posa l'IBAN a l'informe d'error: s'amaguen totes
# les variables d'aquest marc i dels de sota, i els arguments (CA-M05a-06; T-M05a-17).
@sensitive_variables()
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
    iban = validate_mandate_iban(iban)
    # Bloqueja el soci: dues signatures alhora no poden prendre el mateix ordinal.
    member = Member.objects.select_for_update().get(pk=member.pk)
    if member.member_number is None:
        raise ValueError("El soci encara no té número: no pot signar cap mandat.")
    reference = next_reference(member)
    now = timezone.now()
    for previous in SepaMandate.objects.filter(member=member, status=SepaMandate.Status.ACTIVE):
        _revoke(previous, SepaMandate.REPLACED, account, now, replaced_by=reference)
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
    signar-lo (CA-M05a-04), la revocació (P-M05a-C) i l'avís de caducitat (RN-M05a-08). Porta la
    referència, l'identificador de creditor, la data i l'IBAN emmascarat (P-121); mai l'IBAN
    sencer."""
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
