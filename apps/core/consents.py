"""Textos legals i consentiments amb versió i canal (spec 00, HU-17, CA-17.1 a CA-17.3, RN-80).

- Publicar un text crea la versió següent del seu tipus; les anteriors no canvien (CA-17.2).
- Donar o retirar un consentiment afegeix una fila; l'estat és el de l'última (CA-17.3).
- Q-16 és oberta: no hi ha llista fixa de tipus i una versió nova no obliga a tornar a donar
  el consentiment; `has_consent` mira l'última fila, de qualsevol versió.
- Decisió 061: una traducció és una fila més de la versió vigent; si no n'hi ha, es mostra el
  català. Publicar traduccions i decidir si cal una fila nova en acceptar la mateixa versió en
  una altra llengua queda per a la primera traducció real (P-49).

Qui pot registrar un consentiment presencial ho comprova la vista que crida el servei (p. ex.
l'alta presencial, P2); publicar, aquí mateix (M12).
"""

import hashlib

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from . import audit, texts
from .models import Consent, LegalText
from .permissions import has_perm
from .persons import language_for

PUBLISHED = "legal_texts.published"
GRANTED = "consents.granted"
WITHDRAWN = "consents.withdrawn"


PUBLISH_PERMISSION = "core.legal_texts.publish"  # M12
# Tipus que es publiquen a la plataforma, amb el nom que veu la persona (una sola llista: també
# la fan servir l'alta i el perfil). Només aquests surten a la pantalla de M12 (T-M00-08b).
KINDS = {
    "privacy": gettext_lazy("Política de privacitat"),
    "membership_terms": gettext_lazy("Condicions de soci"),
    "guardian_authorization": gettext_lazy("Autorització del pare, la mare o el tutor legal"),
    "newsletter": gettext_lazy("Butlletí del club"),
    "images": gettext_lazy("Ús d'imatges (fotos i vídeos)"),
    "sepa_mandate": gettext_lazy("Text del mandat SEPA"),
    "mandate_campaign_invitation": gettext_lazy("Invitació de la campanya de mandats"),
    # T-M02-34 (RN-M02-35; P-33): la casella dels convidats a les activitats sense edat mínima.
    "adult_declaration": gettext_lazy("Declaració «Soc major d'edat» (activitats)"),
}
# Textos que només porta una importació (071, punt 15): són el que es va acceptar a Cluber i no
# es publiquen mai des de la plataforma.
IMPORTED_IMAGES_KIND = "cluber_images"
IMPORTED_KINDS = frozenset({IMPORTED_IMAGES_KIND})


def normalise(content: str) -> str:
    return texts.normalise_lines(content).strip()


def digest(content: str, note: str = "") -> str:
    """Empremta del que s'ha revisat (text i nota): es publica només això."""
    reviewed = f"{normalise(content)}\0{note.strip()}"
    return hashlib.sha256(reviewed.encode()).hexdigest()


def next_version(kind: str) -> int:
    """La versió següent del tipus, comptant totes les llengües."""
    return (LegalText.objects.filter(kind=kind).aggregate(Max("version"))["version__max"] or 0) + 1


def validate_content(content: str) -> None:
    if not normalise(content):
        raise ValidationError(_("El text no pot ser buit."))
    # Text pla: es mostra escapat, mai com a plantilla; l'HTML no hi té lloc (T-M00-08b).
    if texts.looks_like_html(content):
        raise ValidationError(_("El text no pot portar etiquetes HTML: és text pla."))


@transaction.atomic
def publish_text(kind: str, content: str, *, by, note: str = "") -> LegalText:
    if not has_perm(by, PUBLISH_PERMISSION, write=True):
        raise Http404
    if kind in IMPORTED_KINDS:
        raise ValidationError(_("Aquest text ve d'una importació i no se'n publiquen versions."))
    validate_content(content)
    # shortcut: dues publicacions simultànies del mateix tipus xoquen amb la restricció
    # d'unicitat i una falla sense desar res; amb un sol administrador que publica, n'hi ha prou.
    note = note.strip()
    text = LegalText(
        kind=kind,
        version=next_version(kind),
        content=normalise(content),
        published_by=by,
        note=note,
    )
    text.full_clean()
    text.save()
    audit.record(
        PUBLISHED,
        actor=by,
        target=text,
        reason=note,
        details={"kind": kind, "version": text.version},
    )
    return text


def current_text(kind: str, language: str | None = None) -> LegalText | None:
    """Versió vigent del tipus: la traducció a `language` si existeix i, si no, l'original en
    català. Mai una traducció d'una versió anterior."""
    texts = LegalText.objects.filter(kind=kind)
    latest = texts.filter(language=settings.LANGUAGE_CODE).order_by("-version").first()
    if latest is None or language in (None, latest.language):
        return latest
    return texts.filter(version=latest.version, language=language).first() or latest


def _last(person, kind) -> Consent | None:
    return (
        Consent.objects.filter(person=person, legal_text__kind=kind)
        .select_related("legal_text")
        .order_by("-created_at", "-id")
        .first()
    )


def has_consent(person, kind: str) -> bool:
    last = _last(person, kind)
    return last is not None and last.action == Consent.Action.GRANTED


def _record(person, text, action, channel, by, request, old=None) -> Consent:
    from apps.accounts.models import Account

    # CA-17.1: el presencial el registra un compte concret; l'importat de Cluber, el compte que
    # confirma la importació (071, punt 15). Al web, el compte si n'hi ha (el perfil, T-M01-16).
    recorded = channel in (Consent.Channel.IN_PERSON, Consent.Channel.CLUBER)
    recorder = by if isinstance(by, Account) else None
    if recorded and recorder is None:
        raise ValidationError(_("Aquest consentiment necessita el compte que el registra."))
    consent = Consent.objects.create(
        person=person, legal_text=text, action=action, channel=channel, recorded_by=recorder
    )
    audit.record(
        GRANTED if action == Consent.Action.GRANTED else WITHDRAWN,
        actor=by,
        target=person,
        field=f"consent:{text.kind}",
        old=old,
        new=action,
        details={"version": text.version, "channel": channel},
        request=request,
    )
    return consent


@transaction.atomic
def grant(person, kind: str, *, channel: str, by=None, request=None) -> Consent:
    """Atorga el consentiment amb la versió vigent del text. `by` és qui actua: un compte, un
    convidat (`audit.guest`) o ningú (visitant del formulari web)."""
    text = current_text(kind, language_for(person))
    if text is None:
        raise ValidationError(
            _("No hi ha cap text publicat del tipus «%(kind)s».") % {"kind": kind}
        )
    last = _last(person, kind)
    if last and last.action == Consent.Action.GRANTED and last.legal_text_id == text.pk:
        return last
    old = last.action if last else None
    return _record(person, text, Consent.Action.GRANTED, channel, by, request, old)


@transaction.atomic
def grant_accepted(
    person,
    text: LegalText,
    *,
    channel: str,
    recorded_by=None,
    by=None,
    request=None,
    source=None,
    given_by=Consent.GivenBy.PERSON,
) -> Consent:
    """Atorga el consentiment amb la versió exacta que la persona va acceptar en una altra
    operació (p. ex. la sol·licitud d'alta, Q-044 de la 072), no amb la vigent. `recorded_by` és
    el compte que va registrar l'acceptació presencial; `by`, qui fa l'operació ara (l'actor del
    registre); `source`, una referència sense dades personals per al registre (p. ex. la
    sol·licitud); `given_by`, qui el dona (el representant d'un menor de 14 anys, T-M01-41). Si
    l'últim consentiment d'aquest tipus ja és aquesta versió atorgada, no fa res."""
    if channel == Consent.Channel.IN_PERSON and recorded_by is None:
        raise ValidationError(_("Aquest consentiment necessita el compte que el registra."))
    last = _last(person, text.kind)
    if last and last.action == Consent.Action.GRANTED and last.legal_text_id == text.pk:
        return last
    consent = Consent.objects.create(
        person=person,
        legal_text=text,
        action=Consent.Action.GRANTED,
        channel=channel,
        recorded_by=recorded_by if channel == Consent.Channel.IN_PERSON else None,
        given_by=given_by,
    )
    audit.record(
        GRANTED,
        actor=by,
        target=person,
        field=f"consent:{text.kind}",
        new=Consent.Action.GRANTED,
        details={
            "version": text.version,
            "channel": channel,
            "given_by": given_by,
            **(source or {}),
        },
        request=request,
    )
    return consent


@transaction.atomic
def withdraw(person, kind: str, *, channel: str, by=None, request=None) -> Consent | None:
    """Retira el consentiment: fila nova lligada a la versió que s'havia acceptat; l'anterior
    no canvia i l'efecte és immediat (CA-17.3). Sense consentiment actiu, no fa res."""
    last = _last(person, kind)
    if last is None or last.action != Consent.Action.GRANTED:
        return None
    return _record(
        person, last.legal_text, Consent.Action.WITHDRAWN, channel, by, request, last.action
    )


def imported_text(kind: str, content: str, *, language: str, by) -> LegalText:
    """Text que porta una importació, com una versió del seu tipus (071, punt 15): la mateixa
    versió si el contingut no ha canviat; si no, la següent. Sense M12: el publica el servei
    d'importació que el crida, dins de la seva transacció i amb el seu permís."""
    content = content.strip()
    texts = LegalText.objects.filter(kind=kind, language=language)
    same = texts.filter(content=content).order_by("-version").first()
    if same is not None:
        return same
    last = LegalText.objects.filter(kind=kind).aggregate(Max("version"))["version__max"] or 0
    text = LegalText.objects.create(
        kind=kind, version=last + 1, language=language, content=content, published_by=by
    )
    audit.record(PUBLISHED, actor=by, target=text, details={"kind": kind, "version": text.version})
    return text


def grant_imported(person, text: LegalText, *, by) -> Consent:
    """Consentiment atorgat que ve de Cluber, lligat al text de l'exportació (071, punt 15)."""
    return _record(person, text, Consent.Action.GRANTED, Consent.Channel.CLUBER, by, None)
