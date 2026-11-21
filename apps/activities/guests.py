"""Inscripció de qui no és soci: convidat pel formulari públic o presencial amb AC5 (T-M02-14;
RN-M02-11, decisió 021, RN-30 a RN-33 de la 00; CA-M02-10 i CA-M02-11).

`enrol_guest(activitat, dades, by=None)`:

- **Convidat** (`by=None`): el visitant del formulari públic, sense compte. La vista és pública i
  ho declara; aquí l'actor del registre és «sense identificar».
- **Presencial** (`by` = un compte amb AC5): qui atén la persona al club. El consentiment queda
  registrat amb aquest compte.

En tots dos casos: l'activitat ha de ser oberta a no socis (si no, el missatge diu com fer-se
soci, CA-M02-10); dades mínimes (nom, cognoms, correu i, si l'activitat té edat mínima, la data
de naixement, RN-M01-53); política de privacitat acceptada amb la versió vigent; la persona es
crea amb `persons.create_or_get` (mai es fusiona amb cap altra, encara que el correu coincideixi)
i s'inscriu amb `enrolment.enrol` (preu de no soci, requisits i places). Si queda pendent de
pagament, rep al correu l'enllaç de convidat de la 00 per pagar el càrrec, que només obre aquell
càrrec (CA-M02-11, CA-02.2). La resposta no diu mai si el correu ja era d'algú.

**Fora d'aquesta peça:** la casella «Soc major d'edat» (T-M02-34), les pantalles i el límit de
peticions del formulari públic (vistes).
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext as _

from apps.core import audit, consents, guest_links, persons
from apps.core.models import Consent, Person

from . import enrolment as enrolments
from . import permissions
from .models import Enrolment

PRIVACY = "privacy"
LINK_ACTOR = audit.system("activities.guest_enrolment")
FIELDS = ("first_name", "last_name", "contact_email", "phone", "birth_date")


def _clean(activity, data) -> dict:
    fields = {key: data.get(key) for key in FIELDS if data.get(key) not in (None, "")}
    for key in ("first_name", "last_name", "contact_email"):
        if not str(fields.get(key, "")).strip():
            raise ValidationError(_("Cal el nom, els cognoms i el correu electrònic."))
    if activity.min_age and fields.get("birth_date") is None:
        raise ValidationError(_("Aquesta activitat té edat mínima: cal la data de naixement."))
    persons.check_birth_date(fields.get("birth_date"))
    if data.get("accept_privacy") is not True:
        raise ValidationError(_("Cal acceptar la política de privacitat."))
    return fields


def enrol_guest(activity, data, *, by=None, now=None, request=None) -> Enrolment:
    """Crea la persona i la inscriu. `data`: els camps de `FIELDS` i `accept_privacy`."""
    desk = by is not None
    if desk:
        permissions.require(by, permissions.ENROL_IN_PERSON)
    text = consents.current_text(PRIVACY)
    if text is None:
        raise ValidationError(_("Ara no es poden fer inscripcions. Torna-ho a provar més tard."))
    with transaction.atomic():
        locked = enrolments.lock(activity)
        if not enrolments.is_open(locked, now):
            raise enrolments.ActivityNotOpen(_("Aquesta activitat no té les inscripcions obertes."))
        if not locked.open_to_non_members:
            raise enrolments.NonMembersNotAllowed(
                _(
                    "Aquesta activitat és només per a socis. Si vols participar-hi, primer t'has "
                    "de fer soci del club."
                )
            )
        fields = _clean(locked, data)
        person, _created, _check = persons.create_or_get(origin=Person.Origin.GUEST, **fields)
        actor = by if desk else audit.ANONYMOUS
        consents.grant_accepted(
            person,
            text,
            channel=Consent.Channel.IN_PERSON if desk else Consent.Channel.WEB,
            recorded_by=by,
            by=actor,
            request=request,
        )
        channel = Enrolment.Channel.DESK if desk else Enrolment.Channel.GUEST
        row = enrolments.enrol(
            locked, person, channel=channel, actor=actor, now=now, request=request
        )
        if row.charge_id:
            guest_links.create(person, row.charge, by=LINK_ACTOR, request=request)
    return row
