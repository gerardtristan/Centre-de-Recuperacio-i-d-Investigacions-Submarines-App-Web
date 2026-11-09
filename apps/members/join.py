"""Sol·licitud d'alta: formulari web «Fer-se soci» (P1) i alta presencial (P2). T-M01-13;
P-M01-A passos 1 a 3b; CA-M01-01 i CA-M01-02; RN-M01-02 i RN-M01-03.

- Es crea (o es troba pel document) la persona i la sol·licitud «pendent», amb la data de
  naixement i, si és menor, les dades del representant (068). **No** es crea cap soci, número,
  quota, activació ni carnet (T-M01-14, T-M01-18).
- **Regla uniforme (06/11/2026, CA-M01-01):** cap `core.Consent` a la persona, ni nova ni
  existent. Les acceptacions queden a la sol·licitud (`JoinAcceptance`) amb el text i la versió,
  qui les fa (sol·licitant adult o representant d'un menor), per a qui i el canal. Què se'n fa en
  aprovar l'alta és de la T-M01-14. Abans d'aquesta regla, es creaven consentiments a la persona.
- Mateix document: la sol·licitud va a la persona existent, que no es modifica ni rep cap
  acceptació; l'avís és per a la secretaria (`duplicate_warning`) i el visitant veu la mateixa
  resposta (CA-M01-02, RN-M01-66). Correu o nom i telèfon iguals: persona nova i avís; mai es
  fusionen (V-03).
- Si la persona ja té una alta pendent, no se'n crea cap altra ni cap acceptació; la resposta
  al visitant és la mateixa.
- Textos legals: els tipus de REQUIRED_TEXTS; l'autorització del representant només s'accepta
  per a un menor. Els que crea `seed_demo_data` són **de prova**: amb aquests textos no es pot
  posar en producció (checklist H1, Q-16).
"""

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.core import audit, consents, mail
from apps.core.models import LegalText, Person
from apps.core.normalization import normalize_email
from apps.core.persons import create_or_get

from . import fee_rules
from .models import JoinAcceptance, MemberRequest

# Tots publicats perquè el formulari es pugui fer servir [A validar: quins són obligatoris, Q-16].
REQUIRED_TEXTS = ("privacy", "membership_terms", "guardian_authorization")
GENERAL_TEXTS = ("privacy", "membership_terms")
GUARDIAN_TEXT = "guardian_authorization"
GUARDIAN_DATA = (
    "guardian_first_name",
    "guardian_last_name",
    "guardian_id_document_type",
    "guardian_id_document_number",
)
RECEIPT_TEMPLATE = "rebut-sollicitud-alta"


@dataclass
class JoinOutcome:
    request: MemberRequest | None  # None: la persona ja tenia una alta pendent
    person_created: bool
    duplicate: bool  # mateix document o possible duplicat (avís per a la secretaria)


def current_texts() -> dict[str, LegalText] | None:
    """Versions vigents dels textos obligatoris, o None si en falta cap: sense tots, el
    formulari no es pot fer servir."""
    texts = {kind: consents.current_text(kind) for kind in REQUIRED_TEXTS}
    return texts if all(texts.values()) else None


def _warnings(check, person, email: str) -> list[dict]:
    """Coincidències per a la secretaria: només el motiu i l'identificador intern."""
    found = []
    if check.same_document is not None:
        found.append({"match": "document", "person_id": person.pk})
    email = normalize_email(email)
    for other in check.possible:
        match = "email" if email and other.contact_email == email else "name_phone"
        found.append({"match": match, "person_id": other.pk})
    return found


@transaction.atomic
def submit(data: dict, *, channel: str, by=None, request=None, send_receipt=True) -> JoinOutcome:
    """`data` és el `cleaned_data` del formulari. `by`: el compte de l'alta presencial, o None
    al formulari web (visitant sense identificar)."""
    fields = {
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "id_document_type": data["id_document_type"],
        "id_document_number": data["id_document_number"],
        "contact_email": data["contact_email"],
        "phone": data["phone"],
        "address": data.get("address", ""),
    }
    birth_date = data["birth_date"]
    age = fee_rules.age_today(birth_date, data.get("on"))  # el mateix dia que el formulari
    minor = fee_rules.is_minor(age)
    guardian = {name: data.get(name, "") if minor else "" for name in GUARDIAN_DATA}
    # El formulari ja ho valida; el servei ho torna a comprovar (RN-M01-62, RN-M01-64).
    if not minor and not data.get("id_document_number"):
        raise ValidationError("Alta d'un adult sense document d'identitat.")
    if minor and not (all(guardian.values()) and data.get("guardian_authorization")):
        raise ValidationError("Alta d'un menor sense les dades o l'autorització del representant.")
    if not fee_rules.may_choose(data["membership_type"].code, age):
        raise ValidationError("Tipus de soci no permès per l'edat.")
    web = channel == MemberRequest.Channel.WEB
    origin = Person.Origin.WEB if web else Person.Origin.IN_PERSON
    person, created, check = create_or_get(origin=origin, **fields)
    # D'un en un per persona: dues sol·licituds alhora no en creen dues de pendents.
    Person.objects.select_for_update().filter(pk=person.pk).first()
    pending = MemberRequest.objects.filter(
        person=person, kind=MemberRequest.Kind.JOIN, status=MemberRequest.Status.PENDING
    ).exists()

    warning = _warnings(check, person, fields["contact_email"])
    join_request = None
    if not pending:
        join_request = MemberRequest.objects.create(
            kind=MemberRequest.Kind.JOIN,
            person=person,
            requested_type=data["membership_type"],
            channel=channel,
            duplicate_warning=warning,
            birth_date=birth_date,
            **guardian,
        )
        # Qui accepta: la persona adulta o, per a un menor, el representant (RN-M01-63).
        accepted_by = (
            JoinAcceptance.AcceptedBy.GUARDIAN if minor else JoinAcceptance.AcceptedBy.APPLICANT
        )
        kinds = (*GENERAL_TEXTS, GUARDIAN_TEXT) if minor else GENERAL_TEXTS
        for kind in kinds:
            JoinAcceptance.objects.create(
                request=join_request,
                legal_text=consents.current_text(kind),
                accepted_by=accepted_by,
                channel=channel,
                recorded_by=None if web else by,
            )
        audit.record(
            audit.Action.JOIN_REQUEST_CREATED,
            actor=by,
            target=join_request,
            details={
                "channel": channel,
                "person_created": created,
                "duplicate_warning": bool(warning),
            },
            request=request,
        )
    if send_receipt:
        # A l'adreça escrita i sense cap dada de la persona: el mateix text tant si el document
        # ja existia com si no (CA-M01-02).
        mail.queue_email(RECEIPT_TEMPLATE, to=fields["contact_email"])
    return JoinOutcome(join_request, created, bool(warning))
