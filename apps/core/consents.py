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

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.utils.translation import gettext as _

from . import audit
from .models import Consent, LegalText
from .permissions import has_perm
from .persons import language_for

PUBLISHED = "legal_texts.published"
GRANTED = "consents.granted"
WITHDRAWN = "consents.withdrawn"


@transaction.atomic
def publish_text(kind: str, content: str, *, by) -> LegalText:
    if not has_perm(by, "core.legal_texts.publish"):
        raise Http404
    if not content.strip():
        raise ValidationError(_("El text no pot ser buit."))
    # shortcut: dues publicacions simultànies del mateix tipus xoquen amb la restricció
    # d'unicitat i una falla sense desar res; amb un sol administrador que publica, n'hi ha prou.
    last = LegalText.objects.filter(kind=kind).aggregate(Max("version"))["version__max"] or 0
    text = LegalText(kind=kind, version=last + 1, content=content.strip(), published_by=by)
    text.full_clean()
    text.save()
    audit.record(PUBLISHED, actor=by, target=text, details={"kind": kind, "version": text.version})
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


def _record(person, text, action, channel, by, request) -> Consent:
    from apps.accounts.models import Account

    # CA-17.1: el presencial el registra un compte concret.
    recorder = by if channel == Consent.Channel.IN_PERSON else None
    if channel == Consent.Channel.IN_PERSON and not isinstance(by, Account):
        raise ValidationError(_("Un consentiment presencial necessita el compte que el registra."))
    consent = Consent.objects.create(
        person=person, legal_text=text, action=action, channel=channel, recorded_by=recorder
    )
    audit.record(
        GRANTED if action == Consent.Action.GRANTED else WITHDRAWN,
        actor=by,
        target=person,
        field=f"consent:{text.kind}",
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
    return _record(person, text, Consent.Action.GRANTED, channel, by, request)


@transaction.atomic
def withdraw(person, kind: str, *, channel: str, by=None, request=None) -> Consent | None:
    """Retira el consentiment: fila nova lligada a la versió que s'havia acceptat; l'anterior
    no canvia i l'efecte és immediat (CA-17.3). Sense consentiment actiu, no fa res."""
    last = _last(person, kind)
    if last is None or last.action != Consent.Action.GRANTED:
        return None
    return _record(person, last.legal_text, Consent.Action.WITHDRAWN, channel, by, request)
