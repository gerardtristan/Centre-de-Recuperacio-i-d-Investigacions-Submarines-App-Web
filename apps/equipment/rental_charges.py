"""Càrrec del lloguer al participant (T-M03-11 i la part de càrrecs de la T-M03-16; RN-M03-11
[A validar: junta i tresorer, S-M03-03]; CA-M03-13, 14 i 19).

Tot va darrere de l'interruptor `equipment.rental_charges_enabled`, **apagat** (D2: diners que veu
un soci). Apagat, un lloguer no crea cap càrrec i res d'aquí no fa res.

- `charge_for(assignment)`: en confirmar un lloguer amb preu per al participant, un càrrec a part
  de tipus «inscripció» amb aquest preu i el departament i el centre de cost de l'activitat. El
  cobra el 05b com qualsevol càrrec d'inscripció.
  El participant en rep l'avís per la cua (`notify`): amb un compte personal actiu, el correu
  `avis-carrec-lloguer` amb l'enllaç a la pantalla de pagament; sense (un convidat web o del
  taulell), l'enllaç de convidat del càrrec (00).
- `void_for(assignment, reason)`: en cancel·lar l'assignació, s'anul·la el càrrec si és pendent i
  no hi ha cap pagament en curs. Un càrrec ja pagat no es toca: la devolució és P-531.
- `unpaid(activity)`: els càrrecs de lloguer pendents, motiu per no tancar l'activitat (CA-M03-19).
"""

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils.translation import gettext as _

from apps.accounts.invitations import has_active_personal_account
from apps.activities.deadlines import paying
from apps.core import audit, business_settings, charges, guest_links, mail
from apps.core.models import Charge
from apps.members import recipients

from .models import EquipmentAssignment

SWITCH = "equipment.rental_charges_enabled"
ORIGIN = "equipment"
CHARGED = "equipment.rental_charged"
NOTICE_TEMPLATE = "avis-carrec-lloguer"
NOTICE_ACTOR = audit.system("equipment.rental_charges")


def enabled() -> bool:
    return bool(business_settings.get(SWITCH))


@transaction.atomic
def charge_for(assignment, *, by) -> Charge | None:
    if (
        not enabled()
        or assignment.origin != EquipmentAssignment.Origin.RENTED
        or not assignment.participant_price_cents
        or assignment.charge_id
    ):
        return None
    activity = assignment.activity
    concept = _("Lloguer de material: %(type)s (%(activity)s)") % {
        "type": assignment.equipment_type.name, "activity": activity.title,
    }  # fmt: skip
    charge = charges.create_charge(
        assignment.enrolment.person,
        kind=Charge.Kind.ENROLMENT,
        amount_cents=assignment.participant_price_cents,
        concept=concept[: Charge._meta.get_field("concept").max_length],
        origin=ORIGIN,
        by=by,
        department=activity.department,
        cost_centre=activity.cost_centre,
    )
    assignment.charge = charge
    assignment.save(update_fields=["charge"])
    audit.record(
        CHARGED, actor=by, target=assignment,
        details={"charge": charge.pk, "amount_cents": charge.amount_cents},
    )  # fmt: skip
    notify(assignment, charge)
    return charge


def notify(assignment, charge) -> bool:
    """L'avís del càrrec al participant, a la cua i dins de la mateixa transacció."""
    person = assignment.enrolment.person
    if not has_active_personal_account(person):  # el canal no ho diu: el taulell és DESK
        if not person.contact_email:
            return False
        guest_links.create(person, charge, by=NOTICE_ACTOR)  # envia l'enllaç per pagar-lo
        return True
    to = recipients.email_for(person)
    if not to:
        return False
    context = {
        "title": assignment.activity.title,
        "equipment": assignment.equipment_type.name,
        "amount": charges.euros(charge.amount_cents),
        "link": settings.PUBLIC_SITE_URL + reverse("payments:charge", args=[charge.pk]),
    }
    return mail.queue_email(NOTICE_TEMPLATE, to=to, person=person, context=context) is not None


def void_for(assignment, reason, *, by) -> bool:
    charge = assignment.charge
    if charge is None:
        return False
    charge.refresh_from_db()
    if charge.status != Charge.Status.PENDING or paying(charge):
        return False
    charges.cancel(charge, reason, by=by)
    return True


def unpaid(activity):
    return EquipmentAssignment.objects.filter(
        activity=activity, charge__status=Charge.Status.PENDING
    ).exclude(status=EquipmentAssignment.Status.CANCELLED)
