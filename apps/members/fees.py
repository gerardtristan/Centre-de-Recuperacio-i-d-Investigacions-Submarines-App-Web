"""Quotes i impagats (T-M01-18; P-M01-D, passos 5; HU-M01-12; RN-M01-09, decisió 040).

Implementat: la revisió de l'estat de les quotes dels socis actius i impagats (P10) i la marca
manual d'impagat, amb motiu, amb els serveis de la T-M01-12 (`mark_unpaid`, `unmark_unpaid`;
P9). L'estat de la quota és el de la T-M01-15 (`roster.fee_state`), sense canvis.

Retoc del 09/11/2026 (072):
- `issue_annual_fee`: quota anual íntegra amb número d'ordre (P-54, sortida E).
- `generate_due_fees`: cada dia genera la quota de renovació el dia del primer recordatori. El
  venciment és el «vàlid fins al» del soci (070: mateix dia de l'any següent al pagament; Cluber:
  un any des de «Data alta/renovació», [A validar: tresorer]) o, per a un exempt, l'1 de gener
  del primer any de quota (Q-003). Res amb pagaments parcials ni amb una quota viva sense pagar.
- `send_due_reminders`: recordatoris als dies de `MEMBER_FEE_REMINDER_OFFSETS` (Q-061), un sol
  cop per quota i dia (`FeeReminder`); els posteriors al venciment, només si no s'ha pagat.

**No implementat:** els terminis (P-61, resta oberta; a més, 3 × 32 € = 96 € i la regla «sempre
sumen la quota anual» no coincideixen, vegeu el diari) i la data de la marca d'impagat.
"""

import datetime

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from apps.core import audit, charges, mail
from apps.core.models import Charge, Person

from . import cards, roster
from .fee_rules import first_fee_year, local_today
from .models import AnnualFee, FeeReminder, Member

S = Member.Status
VIEW = roster.FEES  # P10
REVIEWED = (S.ACTIVE, S.UNPAID)  # els únics que es poden marcar o desmarcar (RN-M01-07)
GENERATED = "members.fee.generated"
GENERATE_ORIGIN = "members.generate_due_fees"
REMINDER_TEMPLATE = "recordatori-quota"
UNPAID_CHARGE = (Charge.Status.PENDING, Charge.Status.RETURNED)


def issue_annual_fee(member, *, period: int, due_on: datetime.date, by) -> AnnualFee:
    """Quota anual íntegra del tipus del soci (070; RN-M01-13: l'import del tipus quan es crea),
    sobre un càrrec «quota» a «General» (la 00 ho imposa). P-54, sortida E (072): si les quotes
    d'aquest període estan anul·lades, se'n crea una de nova amb el número d'ordre següent; si n'hi
    ha cap de viva (pendent, pagada o retornada), es rebutja. Qui crida ja ha comprovat el permís
    i és dins la transacció que bloqueja el soci."""
    same = AnnualFee.objects.filter(member=member, period=period, kind=AnnualFee.Kind.ANNUAL)
    if same.exclude(charge__status=Charge.Status.CANCELLED).exists():
        raise ValidationError(_("Aquest soci ja té una quota d'aquest període."))
    sequence = (same.aggregate(n=Max("sequence"))["n"] or 0) + 1
    charge = charges.create_charge(
        member.person,
        kind=Charge.Kind.FEE,
        amount_cents=member.type.annual_fee_cents,
        concept=str(_("Quota de soci %(period)s") % {"period": period}),
        origin="members",
        by=by,
    )
    return AnnualFee.objects.create(
        member=member,
        period=period,
        kind=AnnualFee.Kind.ANNUAL,
        sequence=sequence,
        charge=charge,
        due_on=due_on,
    )


class FeeFilterForm(forms.Form):
    estat = forms.ChoiceField(
        label=_("Estat del soci"),
        required=False,
        choices=[("", _("Tots")), (S.ACTIVE, S.ACTIVE.label), (S.UNPAID, S.UNPAID.label)],
    )
    quota = forms.ChoiceField(
        label=_("Estat de la quota"),
        required=False,
        choices=[("", _("Totes")), (roster.PENDING, _("Pendent"))],
    )


def rows_for_review(data, today=None):
    """(soci, estat de la quota) dels socis actius i impagats, amb els filtres vàlids. L'estat de
    la quota es calcula en Python (`roster.fee_state`): per això el filtre «pendent» també."""
    today = today or local_today()
    members = Member.objects.filter(status__in=REVIEWED).select_related("person", "type")
    if data.get("estat") in REVIEWED:
        members = members.filter(status=data["estat"])
    members = roster.with_fee_data(members).order_by("member_number", "pk")
    rows = [(member, roster.fee_state(member, today)) for member in members]
    if data.get("quota") == roster.PENDING:
        rows = [(m, fee) for m, fee in rows if fee and fee.kind == roster.PENDING]
    return rows


def parse_date(value) -> datetime.date | None:
    """Data efectiva del formulari (AAAA-MM-DD). Si no és vàlida, `None`: el servei la rebutja
    amb el seu missatge, després d'haver registrat un possible conflicte d'interès."""
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


# --- Generació i recordatoris (retoc del 09/11/2026, 072) -----------------------------------


def _lead_days() -> int:
    offsets = settings.MEMBER_FEE_REMINDER_OFFSETS
    return max(0, -min(offsets)) if offsets else 0


def next_fee_due(member) -> datetime.date | None:
    """Venciment de la propera quota del soci, o `None` si no se n'ha de generar cap ara.
    `member` ve de `cards.load_member` (quotes, càrrecs i pagaments precarregats)."""
    if cards._has_partial_payments(member):
        return None  # P-61: cap regla per als pagaments parcials
    if any(fee.charge.status in UNPAID_CHARGE for fee in member.annual_fees):
        return None  # ja n'hi ha una de viva sense pagar
    dates = [d for d in (cards._paid_until(member), cards._cluber_until(member)) if d]
    if dates:
        return max(dates)
    if not member.annual_fees:
        birth = cards._birth_date(member)
        if birth:
            return datetime.date(first_fee_year(birth), 1, 1)  # Q-003
    return None


def generate_due_fees(today=None, *, by=None) -> list[AnnualFee]:
    """Genera les quotes que vencen d'aquí al primer recordatori (CA-M01-10 reformulada amb la
    070). Idempotent: una quota viva sense pagar impedeix generar-ne una altra."""
    today = today or local_today()
    by = by or audit.system(GENERATE_ORIGIN)
    lead = datetime.timedelta(days=_lead_days())
    members = roster.with_fee_data(
        Member.objects.select_related("person", "type").filter(
            status__in=REVIEWED, person__status=Person.Status.ACTIVE
        )
    )
    created = []
    for member in members:
        due = next_fee_due(member)
        if due is None or today < due - lead:
            continue
        with transaction.atomic():
            Member.objects.select_for_update(of=("self",)).get(pk=member.pk)
            fresh = cards.load_member(member.pk)
            if next_fee_due(fresh) != due:
                continue
            try:
                fee = issue_annual_fee(fresh, period=due.year, due_on=due, by=by)
            except ValidationError:
                continue  # ja hi ha una quota viva d'aquell període
            audit.record(GENERATED, actor=by, target=fee, details={"due_on": due.isoformat()})
        created.append(fee)
    return created


def _euros(cents: int) -> str:
    return f"{cents // 100},{cents % 100:02d} €"


def send_due_reminders(today=None) -> int:
    """Envia el recordatori més recent que toca a cada quota pendent i que encara no s'ha enviat
    (Q-061). Si la tasca no ha corregut un dia, el recordatori es recupera mentre no arriba el
    següent; els anteriors perduts no s'envien tard."""
    today = today or local_today()
    offsets = settings.MEMBER_FEE_REMINDER_OFFSETS
    pending = AnnualFee.objects.filter(
        kind=AnnualFee.Kind.ANNUAL,
        charge__status=Charge.Status.PENDING,
        member__status__in=REVIEWED,
    ).select_related("member__person", "charge")
    sent = 0
    for fee in pending:
        reached = [o for o in offsets if fee.due_on + datetime.timedelta(days=o) <= today]
        if not reached:
            continue
        offset = reached[-1]
        with transaction.atomic():
            _, created = FeeReminder.objects.get_or_create(
                fee=fee, offset_days=offset, defaults={"sent_on": today}
            )
            if not created:
                continue
            person = fee.member.person
            if person.contact_email:
                mail.queue_email(
                    REMINDER_TEMPLATE,
                    to=person.contact_email,
                    person=person,
                    context={
                        "due_on": fee.due_on,
                        "amount": _euros(fee.charge.amount_cents),
                        "overdue": offset > 0,
                    },
                )
        sent += 1
    return sent
