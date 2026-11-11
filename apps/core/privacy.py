"""RGPD d'una persona: exportació i anonimització (T-M01-22; spec 00, HU-18 i HU-19, RN-87 a
RN-91; decisió 028; P-M01-F).

**Qui fa què.** Aquí hi ha el que és de la 00 (persona, comptes, consentiments, correus, fitxers
i registre d'activitat) i l'ordre de tot plegat. Cada mòdul hi registra les seves funcions amb
`register` (contractes `<mòdul>.export_personal_data` i `<mòdul>.anonymise` de M01-8, M02-8…):
la 00 no importa cap mòdul.

**Exportació (CA-18.1, CA-M01-18).** `request_export` prepara un JSON amb les dades de la
persona a la mateixa petició (són poques files; no cal la cua) i el desa com a fitxer privat, que
caduca als 7 dies (V-08) i només s'obre amb una URL signada de 5 minuts (`files.signed_url`). En
demanar-ne una de nova, l'anterior caduca. Sense testimonis, empremtes ni secrets, i sense dades
d'altres persones (vegeu `EXPORT_NOTE`).

**Anonimització (CA-19.1 a CA-19.4, CA-M01-19).** `anonymise_person`, en una sola transacció:
1. la persona passa a «anonimitzada» amb la referència anònima i sense cap dada personal;
2. cada mòdul fa la seva part (el 01: baixa, carnets, sol·licituds i textos lliures);
3. els comptes es desactiven i se'n tanquen les sessions; les invitacions s'invaliden;
4. l'adreça dels correus enviats se substitueix i els fitxers sense obligació legal caduquen;
5. al registre d'activitat, el que identifica la persona se substitueix per la referència.
Si un pas falla, no queda res fet.

**Dades bloquejades (028, punt 2; 058, punt 7; CA-19.3).** Els càrrecs, els pagaments i les
quotes no s'esborren ni es modifiquen: queden lligats a la persona anonimitzada. La identitat que
hi surt es bloqueja abans d'anonimitzar (`locked_data.lock`, xifrada) i només es consulta amb M13
i un motiu (T-M00-04).

**Termini de conservació: PUNT D'EXTENSIÓ, sense codi (Q-14 [A verificar: gestoria]).** Quant de
temps es conserven les dades bloquejades no està decidit, i aquí no hi ha cap nombre d'anys ni
cap regla que el simuli. Quan es decideixi:
- la data d'inici és `ErasureRequest.executed_at` (ja es desa);
- el termini ha de ser un valor de configuració (`core.business_settings`), no una constant;
- la destrucció (CA-19.5, RN-90) és una tasca periòdica nova a `apps/core/tasks.py`
  (`core.destroy_expired_blocked_data`), que cridaria una funció d'aquest mòdul i deixaria una
  entrada al registre amb la referència anònima.
Tampoc no està decidit què es fa quan qui demana l'esborrat té càrrecs pendents (CA-19.7, Q-14):
`erasure.approve` no executa aquest cas.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from . import audit, files, locked_data, mail
from .models import OutgoingEmail, Person, PrivateFile
from .persons import ANONYMISED_NOT_EDITABLE, anonymous_ref_for

EXPORT_DOWNLOAD_NAME = "les-meves-dades-cris.json"


def _nothing(person) -> list:
    return []


@dataclass(frozen=True)
class Module:
    """Funcions RGPD d'un mòdul. `export(persona)` torna un diccionari; `anonymise(persona, by=,
    request=)` fa la part del mòdul amb la persona ja anonimitzada; `audit_targets(persona)`
    torna {tipus: identificadors} dels seus objectes **no econòmics** (els valors de les seves
    entrades del registre se substitueixen); `describe(persona)` torna frases sense dades
    personals per al resum de qui aprova; `blockers(persona)`, per què no es pot executar."""

    export: Callable
    anonymise: Callable
    audit_targets: Callable
    describe: Callable = _nothing
    blockers: Callable = _nothing


_MODULES: dict[str, Module] = {}


def register(name: str, module: Module) -> None:
    """El crida cada mòdul en carregar-se (`AppConfig.ready`). `name` és la clau de la seva
    secció a l'exportació."""
    _MODULES[name] = module


# --- Exportació -----------------------------------------------------------------------------


def export_note() -> str:
    return _(
        "Aquest fitxer conté les dades que la plataforma del C.R.I.S. guarda de tu. No hi ha "
        "les dades d'altres persones (per exemple, les del pare, la mare o el tutor legal d'una "
        "alta) ni els textos lliures que ha escrit l'administració (motius de resolucions i de "
        "canvis d'estat): els pots demanar a %(address)s."
    ) % {"address": settings.EMAIL_REPLY_TO}


def _person_data(person) -> dict:
    return {
        "nom": person.first_name,
        "cognoms": person.last_name,
        "correu_de_contacte": person.contact_email,
        "telefon": person.phone,
        "telefon_fix": person.landline,
        "adreca": person.address,
        "codi_postal": person.postal_code,
        "poblacio": person.city,
        "provincia": person.province,
        "tipus_de_document": person.get_id_document_type_display(),
        "numero_de_document": person.id_document_number,
        "data_de_naixement": person.birth_date,
        "llengua_preferida": person.preferred_language,
        "origen": person.get_origin_display(),
        "creat_el": person.created_at,
        "modificat_el": person.updated_at,
    }


def _consents(person) -> list[dict]:
    return [
        {
            "text": consent.legal_text.kind,
            "versio": consent.legal_text.version,
            "accio": consent.get_action_display(),
            "canal": consent.get_channel_display(),
            "qui_el_dona": consent.get_given_by_display(),
            "data": consent.created_at,
        }
        for consent in person.consents.select_related("legal_text").order_by("created_at", "id")
    ]


def _sent_emails(person) -> list[dict]:
    return [
        {
            "plantilla": email.template,
            "adreca": email.to_address,
            "estat": email.get_status_display(),
            "data": email.created_at,
        }
        for email in OutgoingEmail.objects.filter(person=person).order_by("created_at", "id")
    ]


def export_person(person) -> dict:
    """Totes les dades de la persona, i només les seves (CA-18.1). Cap testimoni, empremta ni
    secret: cada secció tria els camps un per un."""
    from apps.accounts import privacy as accounts_privacy

    data = {
        "generat_el": timezone.now(),
        "nota": export_note(),
        "persona": _person_data(person),
        "comptes": accounts_privacy.export(person),
        "consentiments": _consents(person),
        "sollicituds_d_esborrat": [
            {"data": item.created_at, "estat": item.get_status_display()}
            for item in person.erasure_requests.order_by("created_at", "id")
        ],
        "correus_enviats": _sent_emails(person),
    }
    for name, module in _MODULES.items():
        data[name] = module.export(person)
    return data


def live_export(person) -> PrivateFile | None:
    """L'exportació de la persona que encara es pot descarregar, si n'hi ha."""
    return (
        PrivateFile.objects.filter(
            owner=person,
            kind=PrivateFile.Kind.GDPR_EXPORT,
            deleted_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .order_by("-created_at")
        .first()
    )


def request_export(person, *, by, request=None) -> PrivateFile:
    """Prepara l'exportació de la persona i la desa com a fitxer privat (P-M01-F, passos 1 i 2).
    La sol·licitud queda al registre; la descàrrega, en demanar la URL signada
    (`files.signed_url`). El fitxer es desa l'últim: si alguna cosa falla abans, no en queda cap
    a l'emmagatzematge."""
    if person.status != Person.Status.ACTIVE:
        raise ValidationError(ANONYMISED_NOT_EDITABLE)
    content = json.dumps(
        export_person(person), cls=DjangoJSONEncoder, ensure_ascii=False, indent=2
    ).encode("utf-8")
    with transaction.atomic():
        files.expire_owner_files(person, kinds={PrivateFile.Kind.GDPR_EXPORT})
        audit.record(
            audit.Action.EXPORT_REQUESTED,
            actor=by,
            target=person,
            details={"kind": PrivateFile.Kind.GDPR_EXPORT},
            request=request,
        )
        return files.store(
            content,
            owner=person,
            kind=PrivateFile.Kind.GDPR_EXPORT,
            content_type="application/json",
            download_name=EXPORT_DOWNLOAD_NAME,
        )


# --- Anonimització --------------------------------------------------------------------------


def describe(person) -> list[str]:
    """Què farà l'esborrat, mòdul per mòdul, en frases sense dades personals."""
    return [line for module in _MODULES.values() for line in module.describe(person)]


def blockers(person) -> list[str]:
    """Per què no es pot executar ara l'esborrat d'aquesta persona (llista buida: es pot)."""
    from apps.accounts import privacy as accounts_privacy

    found = [line for module in _MODULES.values() for line in module.blockers(person)]
    account_blocker = accounts_privacy.erasure_blocker(person)
    return [*found, account_blocker] if account_blocker else found


_PERSONAL_TEXT_FIELDS = (
    "last_name",
    "contact_email",
    "phone",
    "address",
    "landline",
    "postal_code",
    "city",
    "province",
    "id_document_type",
    "id_document_number",
)


def anonymise_person(person, *, by, request=None) -> Person:
    """Anonimitza la persona i tot el que la identifica (vegeu el docstring del mòdul). Qui crida
    ja ha comprovat el permís, el conflicte d'interès i `blockers`. Torna la persona, ja amb la
    referència anònima."""
    from apps.accounts import privacy as accounts_privacy

    with transaction.atomic():
        locked = Person.objects.select_for_update().get(pk=person.pk)
        if locked.status != Person.Status.ACTIVE:
            raise ValidationError(_("Aquesta persona ja està anonimitzada."))
        before = audit.last_entry_id()
        known_addresses = {locked.contact_email, *accounts_privacy.addresses(locked)} - {""}

        # 0. La identitat que surt als registres econòmics es bloqueja, xifrada, abans de buidar-la
        # (028, punt 2; 058, punt 7; CA-19.3; T-M00-04). Només si en té.
        blocked = locked_data.lock(locked)

        # 1. La persona (CA-19.2). El nom passa a ser la referència: res no queda en blanc on
        # una pantalla el mostri. La llengua torna a la de reserva (061).
        locked.status = Person.Status.ANONYMISED
        locked.anonymous_ref = anonymous_ref_for(locked)
        locked.first_name = locked.anonymous_ref
        for name in _PERSONAL_TEXT_FIELDS:
            setattr(locked, name, "")
        locked.birth_date = None
        locked.preferred_language = settings.LANGUAGE_CODE
        locked.save()

        # 2. Els mòduls, amb la persona ja anonimitzada (els seus disparadors ho exigeixen).
        targets = {"core.person": [locked.pk]}
        for module in _MODULES.values():
            module.anonymise(locked, by=by, request=request)
            for label, ids in module.audit_targets(locked).items():
                targets.setdefault(label, []).extend(ids)

        # 3. Comptes, sessions i invitacions (CA-19.1; 079, punt 10).
        targets["accounts.account"] = accounts_privacy.anonymise(
            locked, by=by, known_addresses=known_addresses, request=request
        )
        # Enllaços de convidat (T-M00-02; CA-19.1): es revoquen els que encara funcionen.
        locked.guest_links.filter(revoked_at__isnull=True, replaced_by__isnull=True).update(
            revoked_at=timezone.now()
        )
        # 4. Correus enviats i fitxers sense obligació legal (RN-B8).
        mail.anonymise_recipient(locked, known_addresses)
        files.expire_owner_files(locked)
        # Sol·licituds d'esborrat anteriors: el motiu d'un rebuig és text lliure.
        locked.erasure_requests.exclude(rejection_reason="").update(
            rejection_reason=locked.anonymous_ref
        )
        targets["core.erasurerequest"] = list(locked.erasure_requests.values_list("pk", flat=True))
        # 5. Registre d'activitat (CA-19.4), només les entrades anteriors a l'esborrat.
        audit.substitute_identity(locked, targets, up_to=before)
        if blocked is not None:
            locked_data.record_locked(locked, by=by, request=request)
    return locked
