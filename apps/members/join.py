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

T-M01-41 (072: Q-011, Q-017, Q-031 i Q-044; 074: punts 13 a 16, RN-M01-78):
- Butlletí i imatges (OPTIONAL_TEXTS): caselles opcionals, desmarcades, només si hi ha un text
  vigent publicat d'aquell tipus. Una casella marcada és una acceptació més de la sol·licitud: la
  dona el representant d'un menor de 14 anys i, a partir dels 14, la mateixa persona (posició del
  responsable, [A validar: assessor de protecció de dades, Q-016] abans de posar-ho en servei).
  En aprovar l'alta passen a `core.Consent` (`admissions`), excepte el butlletí d'un menor de
  14 anys, que es queda a la sol·licitud (072: les imatges són l'única excepció a la Q-044).
- Menors: el correu i el telèfon del representant són obligatoris; els del menor, opcionals.
- El rebut va a l'adreça de `receipt_address` (la regla de `recipients`, amb les adreces escrites).
- Passaport: només a l'alta presencial, també el del representant; la web el rebutja.
"""

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404

from apps.core import audit, consents, mail
from apps.core.models import LegalText, Person
from apps.core.normalization import normalize_email, normalize_phone
from apps.core.permissions import has_perm
from apps.core.persons import create_or_get

from . import fee_rules, recipients
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
    "guardian_email",
    "guardian_phone",
)
# Consentiments opcionals (Q-031): cadascun amb la seva casella `accept_<tipus>`.
OPTIONAL_TEXTS = ("newsletter", "images")
# L'únic que el representant d'un menor de 14 anys dona a la persona del menor (072, Q-044 opció A).
GUARDIAN_CONSENT_TEXT = "images"
RECEIPT_TEMPLATE = "rebut-sollicitud-alta"
IN_PERSON_PERMISSION = "members.create_in_person"  # P2

# Textos PROVISIONALS del butlletí i de les imatges (074, punt 16; esborrany
# `docs/esborranys/textos-legals.md`, seccions 4 i 5). [A validar: Q-16 i Q-028, gestoria i
# assessor de protecció de dades.] No serveixen per recollir consentiments reals: no es
# publiquen amb cap migració; només els publiquen les proves i l'ordre de dades de prova.
PROVISIONAL_OPTIONAL_TEXTS = {
    "newsletter": (
        "TEXT PROVISIONAL [A validar: Q-16 i Q-028]. Vull rebre el butlletí del C.R.I.S. al "
        "correu. És opcional: sense aquest consentiment també es pot ser soci i es reben els "
        "avisos de la condició de soci. Es pot retirar en qualsevol moment des del perfil o amb "
        "l'enllaç de cada butlletí."
    ),
    "images": (
        "TEXT PROVISIONAL [A validar: Q-16 i Q-028]. Autoritzo el C.R.I.S. a publicar fotos i "
        "vídeos on surt la persona sòcia, presos en activitats del club, a [A validar: on es "
        "publiquen]. És opcional i es pot retirar en qualsevol moment des del perfil: les "
        "publicacions noves deixaran d'incloure-la. Per a un menor de 14 anys, el consentiment "
        "el dona el pare, la mare o el tutor legal."
    ),
}


@dataclass
class JoinOutcome:
    request: MemberRequest | None  # None: la persona ja tenia una alta pendent
    person_created: bool
    duplicate: bool  # mateix document o possible duplicat (avís per a la secretaria)


def current_texts() -> dict[str, LegalText] | None:
    """Versions vigents dels textos obligatoris, i dels opcionals que en tinguin, o None si en
    falta cap d'obligatori: sense tots, el formulari no es pot fer servir."""
    texts = {kind: consents.current_text(kind) for kind in REQUIRED_TEXTS}
    if not all(texts.values()):
        return None
    # Els opcionals, només si n'hi ha un de vigent: sense text, no hi ha casella.
    optional = {kind: consents.current_text(kind) for kind in OPTIONAL_TEXTS}
    return texts | {kind: text for kind, text in optional.items() if text}


def receipt_address(data: dict) -> str:
    """On va el rebut: la regla de `recipients` amb les adreces escrites al formulari (RN-M01-78),
    mai les d'una persona existent (CA-M01-02)."""
    age = fee_rules.age_today(data["birth_date"], data.get("on"))
    return recipients.address_for(
        age,
        normalize_email(data.get("contact_email", "")),
        normalize_email(data.get("guardian_email", "")) if fee_rules.is_minor(age) else "",
    )


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
    al formulari web (visitant sense identificar). L'alta presencial exigeix P2 també aquí, no
    només a la vista (T-M01-37): sense permís, «no trobat»."""
    if channel != MemberRequest.Channel.WEB and not has_perm(by, IN_PERSON_PERMISSION):
        raise Http404
    fields = {
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "id_document_type": data["id_document_type"],
        "id_document_number": data["id_document_number"],
        "contact_email": data.get("contact_email", ""),
        "phone": data.get("phone", ""),
        "address": data.get("address", ""),
    }
    birth_date = data["birth_date"]
    age = fee_rules.age_today(birth_date, data.get("on"))  # el mateix dia que el formulari
    minor = fee_rules.is_minor(age)
    guardian = {name: data.get(name, "") if minor else "" for name in GUARDIAN_DATA}
    guardian["guardian_email"] = normalize_email(guardian["guardian_email"])
    guardian["guardian_phone"] = normalize_phone(guardian["guardian_phone"])
    # El formulari ja ho valida; el servei ho torna a comprovar (RN-M01-62, RN-M01-64; Q-011).
    if not minor and not data.get("id_document_number"):
        raise ValidationError("Alta d'un adult sense document d'identitat.")
    if not minor and not (data.get("contact_email") and data.get("phone")):
        raise ValidationError("Alta d'un adult sense correu o telèfon.")
    if minor and not (all(guardian.values()) and data.get("guardian_authorization")):
        raise ValidationError("Alta d'un menor sense les dades o l'autorització del representant.")
    if not fee_rules.may_choose(data["membership_type"].code, age):
        raise ValidationError("Tipus de soci no permès per l'edat.")
    web = channel == MemberRequest.Channel.WEB
    passport = Person.DocumentType.PASSPORT
    if web and passport in (fields["id_document_type"], guardian["guardian_id_document_type"]):
        raise ValidationError("El passaport només s'admet a l'alta presencial (Q-017).")
    origin = Person.Origin.WEB if web else Person.Origin.IN_PERSON
    person, created, check = create_or_get(origin=origin, **fields)
    # D'un en un per persona: dues sol·licituds alhora no en creen dues de pendents.
    Person.objects.select_for_update().filter(pk=person.pk).first()
    pending = MemberRequest.objects.filter(
        person=person, kind=MemberRequest.Kind.JOIN, status=MemberRequest.Status.PENDING
    ).exists()

    warning = _warnings(check, person, fields["contact_email"])
    # Q-042 (072): si la persona ja existia, el contacte escrit no la modifica; es desa a la
    # sol·licitud si és diferent, i la secretaria decideix en aprovar.
    new_contact = {}
    if not created:
        email, phone = normalize_email(fields["contact_email"]), normalize_phone(fields["phone"])
        if email and email != person.contact_email:
            new_contact["new_contact_email"] = email
        if phone and phone != person.phone:
            new_contact["new_contact_phone"] = phone
    join_request = None
    if not pending:
        join_request = MemberRequest.objects.create(
            kind=MemberRequest.Kind.JOIN,
            person=person,
            requested_type=data["membership_type"],
            channel=channel,
            duplicate_warning=warning,
            birth_date=birth_date,
            **new_contact,
            **guardian,
        )
        # Qui accepta: la persona adulta o, per a un menor, el representant (RN-M01-63).
        accepted_by = (
            JoinAcceptance.AcceptedBy.GUARDIAN if minor else JoinAcceptance.AcceptedBy.APPLICANT
        )
        kinds = (*GENERAL_TEXTS, GUARDIAN_TEXT) if minor else GENERAL_TEXTS
        # Opcionals: només les caselles marcades (mai per defecte). Un menor de 14 anys, pel
        # representant (Q-044, opció A); de 14 a 17, el mateix menor (RN-M01-78) [A validar:
        # assessor de protecció de dades, Q-016].
        optional_by = (
            JoinAcceptance.AcceptedBy.GUARDIAN
            if age < fee_rules.FULL_TYPE_MIN_AGE
            else JoinAcceptance.AcceptedBy.APPLICANT
        )
        accepted = [(kind, accepted_by) for kind in kinds] + [
            (kind, optional_by) for kind in OPTIONAL_TEXTS if data.get(f"accept_{kind}") is True
        ]
        for kind, who in accepted:
            text = consents.current_text(kind)
            if text is None:
                raise ValidationError(f"No hi ha cap text vigent de «{kind}».")
            JoinAcceptance.objects.create(
                request=join_request,
                legal_text=text,
                accepted_by=who,
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
    to = receipt_address(data)
    if send_receipt and to:
        # A l'adreça escrita i sense cap dada de la persona: el mateix text tant si el document
        # ja existia com si no (CA-M01-02).
        mail.queue_email(RECEIPT_TEMPLATE, to=to)
    return JoinOutcome(join_request, created, bool(warning))
