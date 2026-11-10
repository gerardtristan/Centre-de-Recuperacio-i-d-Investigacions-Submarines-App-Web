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
  Van a l'adreça de `recipients.email_for` (T-M01-41, RN-M01-78): un menor de 14 anys, o un de
  14 a 17 sense correu propi, els rep al correu del representant.

**No implementat:** els terminis (P-61, resta oberta; el preu a terminis, 96 € amb un recàrrec que
decideix la junta, és de la 072, quarta instrucció) i la data de la marca d'impagat.
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

from . import cards, recipients, roster
from .fee_rules import first_fee_year, local_today
from .models import AnnualFee, FeeReminder, Member

S = Member.Status
VIEW = roster.FEES  # P10
REVIEWED = (S.ACTIVE, S.UNPAID)  # els únics que es poden marcar o desmarcar (RN-M01-07)
GENERATED = "members.fee.generated"
GENERATE_ORIGIN = "members.generate_due_fees"
REMINDER_TEMPLATE = "recordatori-quota"
UNPAID_CHARGE = (Charge.Status.PENDING, Charge.Status.RETURNED)


def _issue_fee(member, *, kind, amount_cents, concept, period, due_on, by) -> AnnualFee:
    """Quota sobre un càrrec «quota» a «General» (la 00 ho imposa). P-54, sortida E (072): si les
    quotes d'aquest tipus i període estan anul·lades, se'n crea una de nova amb el número d'ordre
    següent; si n'hi ha cap de viva (pendent, pagada o retornada), es rebutja. Qui crida ja ha
    comprovat el permís i és dins la transacció que bloqueja el soci."""
    same = AnnualFee.objects.filter(member=member, period=period, kind=kind)
    if same.exclude(charge__status=Charge.Status.CANCELLED).exists():
        raise ValidationError(_("Aquest soci ja té una quota d'aquest tipus i període."))
    sequence = (same.aggregate(n=Max("sequence"))["n"] or 0) + 1
    charge = charges.create_charge(
        member.person,
        kind=Charge.Kind.FEE,
        amount_cents=amount_cents,
        concept=concept,
        origin="members",
        by=by,
    )
    return AnnualFee.objects.create(
        member=member, period=period, kind=kind, sequence=sequence, charge=charge, due_on=due_on
    )


def issue_annual_fee(member, *, period: int, due_on: datetime.date, by) -> AnnualFee:
    """Quota anual íntegra del tipus del soci (070; RN-M01-13: l'import del tipus quan es
    crea)."""
    return _issue_fee(
        member,
        kind=AnnualFee.Kind.ANNUAL,
        amount_cents=member.type.annual_fee_cents,
        concept=str(_("Quota de soci %(period)s") % {"period": period}),
        period=period,
        due_on=due_on,
        by=by,
    )


def supplement_cents(member, target_type) -> int:
    """Q-049 (072): la diferència entre les quotes dels dos tipus (55 € de simpatitzant a ple
    dret), amb els imports vigents quan s'aprova el canvi."""
    return target_type.annual_fee_cents - member.type.annual_fee_cents


def issue_type_change_supplement(member, target_type, *, period, due_on, by) -> AnnualFee:
    """Suplement del canvi a ple dret (Q-049). El canvi és efectiu quan es paga (Q-050)."""
    cents = supplement_cents(member, target_type)
    if cents <= 0:
        raise ValidationError(_("Aquest canvi de tipus no té cap suplement a pagar."))
    return _issue_fee(
        member,
        kind=AnnualFee.Kind.TYPE_CHANGE_SUPPLEMENT,
        amount_cents=cents,
        concept=str(_("Suplement de canvi a %(type)s") % {"type": target_type.name}),
        period=period,
        due_on=due_on,
        by=by,
    )


EDIT_PERMISSION = "members.fees.generate"  # P8, el permís d'edició de quotes (Q-057)
CANCELLED_FEE = "members.fee.cancelled"


def cancel_fee(fee, *, by, reason, request=None) -> AnnualFee:
    """Anul·la (perdona) una quota pendent o retornada, amb motiu (Q-057 de la 072): ho pot fer
    qui té permís d'edició de quotes (P8 amb edició); amb només lectura, no. Sempre és una
    anul·lació del càrrec, mai un esborrat (RN-67)."""
    from django.http import Http404

    from apps.accounts.models import Account
    from apps.core.permissions import has_perm

    if not isinstance(by, Account) or not has_perm(by, EDIT_PERMISSION, write=True):
        raise Http404
    return cancel_fee_checked(fee, by=by, reason=reason, request=request)


def cancel_fee_checked(fee, *, by, reason, request=None) -> AnnualFee:
    """Nucli de `cancel_fee`, sense el permís: qui el crida l'ha comprovat abans (només
    `cancel_fee`, P8, i el suplement vençut, P7a o P8; RN-M01-82). Compte actiu, motiu,
    conflicte d'interès i anul·lació del càrrec amb el registre de qui i el motiu."""
    from .services import _check_account_active, ensure_not_own_member

    _check_account_active(by)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal el motiu per anul·lar la quota."))
    ensure_not_own_member(fee.member, by, request=request)
    with transaction.atomic():
        locked = AnnualFee.objects.select_related("charge").get(pk=fee.pk)
        if locked.charge.status not in UNPAID_CHARGE:
            raise ValidationError(_("Només es pot anul·lar una quota pendent o retornada."))
        charges.cancel(locked.charge, reason, by=by)
        audit.record(CANCELLED_FEE, actor=by, target=locked, reason=reason, request=request)
    fee.refresh_from_db()
    return fee


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
            to = recipients.email_for(person, today=today)  # RN-M01-78; 072, quarta instr., 3
            if to:
                mail.queue_email(
                    REMINDER_TEMPLATE,
                    to=to,
                    person=person,
                    context={
                        "due_on": fee.due_on,
                        "amount": _euros(fee.charge.amount_cents),
                        "overdue": offset > 0,
                    },
                )
        sent += 1
    return sent
