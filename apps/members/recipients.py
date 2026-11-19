"""Destinatari de les comunicacions d'una persona (T-M01-41; RN-M01-78, CA-M01-77; 074 punts 13
i 14; 072, Q-011 opció 3 i quarta instrucció, punt 3).

- Menor de 14 anys: sempre el correu del representant.
- De 14 a 17 anys sense correu propi: el del representant.
- La resta (també amb l'edat desconeguda): el correu de contacte de la persona.

Totes les comunicacions que van a una persona passen per aquí (rebut de l'alta, rebuig,
recordatoris de quota i baixa). Si no hi ha cap adreça, no s'envia res.
"""

import logging

from apps.core.persons import age_on

from . import fee_rules
from .models import MemberRequest

logger = logging.getLogger(__name__)


def address_for(age: int | None, own_email: str, guardian_email: str) -> str:
    """La regla, sense tocar dades (també per al rebut, amb les adreces escrites al formulari)."""
    if age is not None and fee_rules.is_minor(age):
        # FULL_TYPE_MIN_AGE: els 14 anys complerts, el mateix llindar de la RN-M01-64.
        if age < fee_rules.FULL_TYPE_MIN_AGE or not own_email:
            return guardian_email
    return own_email


def email_for(person, *, join_request=None, today=None, log=True) -> str:
    """Adreça on s'envia una comunicació de `person`, o "" si no n'hi ha cap.

    El representant i la data de naixement (si la persona no en té) surten de les altes
    **aprovades** de la persona, la més recent primer: una sol·licitud que ningú no ha revisat no
    pot desviar els correus d'una persona existent. Per a una comunicació sobre una sol·licitud
    concreta (el rebuig), `join_request` és aquella sol·licitud. `log=False`: només es consulta
    (una llista de pantalla), no s'intenta cap enviament."""
    if join_request is not None:
        joins = [join_request]
    else:
        joins = MemberRequest.objects.filter(
            person=person, kind=MemberRequest.Kind.JOIN, status=MemberRequest.Status.APPROVED
        ).order_by("-created_at", "-pk")
    joins = list(joins)
    birth = person.birth_date or next((j.birth_date for j in joins if j.birth_date), None)
    guardian = next((j.guardian_email for j in joins if j.guardian_email), "")
    today = today or fee_rules.local_today()
    age = age_on(birth, today) if birth and birth <= today else None
    address = address_for(age, person.contact_email, guardian)
    if not address and log:
        logger.info("Comunicació no enviada: la persona %s no té cap adreça.", person.pk)
    return address
