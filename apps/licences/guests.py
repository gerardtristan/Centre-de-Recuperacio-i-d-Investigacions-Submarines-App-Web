"""Llicència per a una persona de fora, sense compte (T-M06-07b; P-M06-C, passos 3 i 4; RN-M06-03
i 04; decisió 021; RN-30 a RN-33 de la 00).

`request_as_guest(licence_type, data, ...)`:
- només amb `licences.non_members_enabled` (desactivada d'entrada; la vista respon «no trobat»);
- dades mínimes: nom, cognoms, correu i data de naixement (la federació la demana, RN-M01-47), i
  la política de privacitat vigent acceptada (consentiment de la 00 amb la versió del text);
- de moment, només majors d'edat el dia que la demana ([P-449](../../docs/decisions/pendents.md));
- la persona es crea amb `persons.create_or_get` (origen convidat; mai es fusiona amb cap altra,
  encara que el correu coincideixi) i la llicència és la de `services.place_request`: `requested`,
  amb el càrrec al preu de no soci (RN-M06-04);
- l'enllaç de convidat de la 00 va al correu i només obre aquell càrrec, per pagar-lo (05b).
La resposta no diu mai si el correu ja era d'algú.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit, business_settings, consents, guest_links, persons
from apps.core.models import Consent, Person

from . import services
from .models import Licence

PRIVACY = "privacy"
LINK_ACTOR = audit.system("licences.guest_request")
FIELDS = ("first_name", "last_name", "contact_email", "phone", "birth_date")
ADULT_AGE = 18  # majoria d'edat legal, no un valor del club (P-449)


def _clean(data, today) -> dict:
    fields = {key: data.get(key) for key in FIELDS if data.get(key) not in (None, "")}
    for key in ("first_name", "last_name", "contact_email", "birth_date"):
        if not str(fields.get(key, "")).strip():
            raise ValidationError(_("Cal el nom, els cognoms, el correu i la data de naixement."))
    persons.check_birth_date(fields["birth_date"], today)
    if persons.age_on(fields["birth_date"], today) < ADULT_AGE:
        raise ValidationError(
            _("De moment no es poden demanar llicències per a menors d'edat des d'aquí: escriu a "
              "la secretaria del club.")
        )  # fmt: skip
    if data.get("accept_privacy") is not True:
        raise ValidationError(_("Cal acceptar la política de privacitat."))
    return fields


def request_as_guest(
    licence_type, data, starts_on=None, *, request=None, send_link=True, today=None
) -> Licence:
    """`data`: els camps de `FIELDS` i `accept_privacy`. `send_link` és fals si el límit de
    destinatari del formulari no deixa enviar més correus a aquella adreça."""
    today = today or timezone.localdate()
    if not business_settings.get(services.NON_MEMBERS_ENABLED):
        raise services.NonMembersDisabled
    text = consents.current_text(PRIVACY)
    if text is None:
        raise ValidationError(_("Ara no es poden demanar llicències. Torna-ho a provar més tard."))
    fields = _clean(data, today)
    with transaction.atomic():
        person, _created, _check = persons.create_or_get(origin=Person.Origin.GUEST, **fields)
        consents.grant_accepted(
            person, text, channel=Consent.Channel.WEB, by=audit.ANONYMOUS, request=request
        )
        licence = services.place_request(
            person, licence_type, starts_on, actor=audit.ANONYMOUS, today=today
        )
        if send_link:
            guest_links.create(person, licence.charge, by=LINK_ACTOR, request=request)
    return licence
