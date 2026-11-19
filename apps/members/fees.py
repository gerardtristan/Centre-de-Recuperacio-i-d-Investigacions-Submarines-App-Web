"""Quotes i impagats (T-M01-18; P-M01-D, passos 5; HU-M01-12; RN-M01-09, decisió 040).

Implementat: la revisió de l'estat de les quotes dels socis actius i impagats (P10) i la marca
manual d'impagat, amb motiu, amb els serveis de la T-M01-12 (`mark_unpaid`, `unmark_unpaid`;
P9). L'estat de la quota (`roster.fee_state`) surt del càlcul únic de «vàlid fins al»
(`validity.py`; 079, RN-M01-86): el llistat, la fitxa, aquesta revisió, el carnet i la generació
diuen el mateix.

Retoc del 09/11/2026 (072):
- `issue_annual_fee`: quota anual íntegra amb número d'ordre (P-54, sortida E).
- `generate_due_fees`: cada dia genera la quota de renovació el dia del primer recordatori. El
  venciment és el «vàlid fins al» del soci (070: mateix dia de l'any següent al pagament; Cluber:
  un any des de «Data alta/renovació», 097, punt 1) o, per a un exempt, l'1 de gener
  del primer any de quota (Q-003). Res amb pagaments parcials ni amb una quota viva sense pagar.
- `send_due_reminders`: recordatoris als dies de VC-02 (Q-061; ajust, T-M01-32), un sol
  cop per quota i dia (`FeeReminder`); els posteriors al venciment, només si no s'ha pagat.
  Van a l'adreça de `recipients.email_for` (T-M01-41, RN-M01-78): un menor de 14 anys, o un de
  14 a 17 sense correu propi, els rep al correu del representant.

Decisió 079 (11/11/2026):
- `notify_fee_editors`: correu a qui pot editar les quotes quan paga un soci impagat o es retorna
  un rebut, només amb el número de soci i la quota (A-07, RN-M01-89).
- La marca d'impagat admet una data passada i mai una de futura (A-18): ho fa el servei
  d'estats (`services._check_effective_on`).
- El pagament a terminis és de la T-M01-49 (`instalments.py`; A-04, RN-M01-91; P-61).

T-M01-40 (12/11/2026; RN-M01-72 i RN-M01-94; decisió 085, J-2 i G-2):
- `exempt_fee`: exempció puntual d'una quota anual pendent, amb el permís P22
  («Eximir o anul·lar una quota», del Tresorer) i motiu. Anul·la el càrrec amb la categoria
  «exempció» i desa el període eximit (`FeeExemption`); un soci pendent passa a actiu amb
  carnet. La reautenticació la fa la vista, a la mateixa petició.
- `cancel_fee` passa a demanar el mateix permís P22 (072, quarta instrucció, punt 4: la pantalla
  d'anul·lar va «amb el mateix permís i el mateix motiu obligatori que l'exempció»). Abans
  demanava P8 amb edició (Q-057) i no tenia pantalla.
"""

import datetime
import logging

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from apps.core import audit, charges, mail
from apps.core.models import Charge, Person

from . import cards, recipients, roster, validity
from . import settings as values
from .fee_rules import first_fee_year, local_today
from .models import AnnualFee, FeeExemption, FeeReminder, Member, MemberRequest
from .validity import twelve_months_after

S = Member.Status
VIEW = roster.FEES  # P10
REVIEWED = (S.ACTIVE, S.UNPAID)  # els únics que es poden marcar o desmarcar (RN-M01-07)
GENERATED = "members.fee.generated"
GENERATE_ORIGIN = "members.generate_due_fees"
REMINDER_TEMPLATE = "recordatori-quota"
UNPAID_CHARGE = (Charge.Status.PENDING, Charge.Status.RETURNED)
logger = logging.getLogger(__name__)


def _issue_fee(
    member, *, kind, amount_cents, concept, period, due_on, by, instalment=0
) -> AnnualFee:
    """Quota sobre un càrrec «quota» a «General / Quotes de socis» (la 00 ho imposa; S-M04-06).
    P-54, sortida E (072): si les quotes d'aquest tipus i període estan anul·lades, se'n crea una
    de nova amb el número d'ordre següent; si n'hi ha cap de viva (pendent, pagada o retornada),
    es rebutja. Qui crida ja ha comprovat el permís i és dins la transacció que bloqueja el soci."""
    same = AnnualFee.objects.filter(member=member, period=period, kind=kind, instalment=instalment)
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
        member=member,
        period=period,
        kind=kind,
        instalment=instalment,
        sequence=sequence,
        charge=charge,
        due_on=due_on,
    )


def issue_annual_fee(
    member, *, period: int, due_on: datetime.date, by, fee_type=None, on=None
) -> AnnualFee:
    """Quota anual íntegra del tipus del soci (070; RN-M01-13 i 45: el preu vigent el dia `on`
    en què es crea, avui si no se'n dona cap). `fee_type`: el tipus demanat per a la renovació,
    si no és el del soci (073)."""
    return _issue_fee(
        member,
        kind=AnnualFee.Kind.ANNUAL,
        amount_cents=values.annual_fee_cents(fee_type or member.type, on),
        concept=str(_("Quota de soci %(period)s") % {"period": period}),
        period=period,
        due_on=due_on,
        by=by,
    )


def supplement_cents(member, target_type) -> int:
    """Q-049 (072): la diferència entre les quotes dels dos tipus (55 € de simpatitzant a ple
    dret), amb els imports vigents quan s'aprova el canvi."""
    return values.annual_fee_cents(target_type) - values.annual_fee_cents(member.type)


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
EXEMPT_PERMISSION = "members.fees.exempt"  # P22, eximir o anul·lar una quota (RN-M01-72; 085)
CANCELLED_FEE = "members.fee.cancelled"
EXEMPTED_FEE = "members.fee.exempted"
EXEMPTION = Charge.CancelCategory.EXEMPTION


def _reject_returned(charge) -> None:
    """RN-67 (spec 00): què es fa amb un càrrec retornat és de la 05b (Q-22); avui no té cap
    transició. Es diu clar, en lloc de l'error genèric de la taula de transicions."""
    if charge.status == Charge.Status.RETURNED:
        raise ValidationError(
            _(
                "Una quota retornada encara no es pot eximir ni anul·lar: es resoldrà amb el "
                "mòdul de cobraments."
            )
        )


def can_exempt(by, permissions=None) -> bool:
    """Per mostrar o no l'acció: el control és el dels serveis (`exempt_fee`, `cancel_fee`)."""
    from apps.core.permissions import has_perm

    return has_perm(by, EXEMPT_PERMISSION, write=True, permissions=permissions)


def _require_exempt_permission(by) -> None:
    from django.http import Http404

    from apps.accounts.models import Account
    from apps.core.permissions import has_perm

    if not isinstance(by, Account) or not has_perm(by, EXEMPT_PERMISSION, write=True):
        raise Http404


def cancel_fee(fee, *, by, reason, request=None) -> AnnualFee:
    """Anul·la (perdona) una quota pendent, amb motiu (Q-057 de la 072). Ho pot fer
    qui té P22 amb edició, el mateix permís que l'exempció (072, quarta instrucció, punt 4; 085,
    G-2). Sempre és una anul·lació del càrrec, mai un esborrat (RN-67). No dona cap dret: per
    deixar el període com a resolt, `exempt_fee`."""
    _require_exempt_permission(by)
    return cancel_fee_checked(fee, by=by, reason=reason, request=request)


def exempt_fee(fee, *, by, reason, request=None) -> FeeExemption:
    """Exempció puntual d'una quota (RN-M01-72 i RN-M01-94; CA-M01-65 a 67). P22 amb edició i
    motiu; la reautenticació és de la vista.

    - Només una quota anual amb el càrrec pendent i sense cap pagament a mitges. Una de pagada
      no: seria una devolució (05b). Una de retornada, tampoc encara: RN-67 deixa les
      transicions des de «retornat» a la 05b (Q-22). Un suplement s'anul·la, no s'eximeix.
    - El càrrec queda anul·lat amb la categoria «exempció»; mai un pagament de 0 €.
    - El període eximit va del venciment de la quota (data d'aprovació en una alta; data de
      renovació en un soci que ja ho és) fins al mateix dia de l'any següent. Si ja ha acabat,
      eximir-la no donaria cap dret: es rebutja i cal anul·lar-la.
    - Soci pendent → actiu, amb carnet (com quan paga). Actiu → continua actiu i, si no té
      carnet, se n'emet un. Impagat → continua impagat: la marca és manual (040). Baixa → no.
    """
    from .services import _change_status, _check_account_active, ensure_not_own_member

    _require_exempt_permission(by)
    _check_account_active(by)
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal el motiu per eximir la quota."))
    ensure_not_own_member(fee.member, by, request=request)
    today = local_today()
    with transaction.atomic():
        member = Member.objects.select_for_update(of=("self",)).get(pk=fee.member_id)
        locked = AnnualFee.objects.select_related("charge").get(pk=fee.pk)
        if locked.kind != AnnualFee.Kind.ANNUAL:
            raise ValidationError(
                _("Només es pot eximir una quota anual. Un suplement s'anul·la, no s'eximeix.")
            )
        _reject_returned(locked.charge)
        if locked.charge.status != Charge.Status.PENDING:
            raise ValidationError(
                _("Només es pot eximir una quota pendent. Una de pagada seria una devolució.")
            )
        if charges.active_payments(locked.charge):
            raise ValidationError(
                _("Aquesta quota té pagaments a mitges: no es pot eximir (terminis, P-61).")
            )
        if member.status == Member.Status.LEFT:
            raise ValidationError(
                _("Aquesta persona és baixa: la quota es pot anul·lar, però no eximir.")
            )
        until = twelve_months_after(locked.due_on)
        if until < today:
            raise ValidationError(
                _(
                    "El període d'aquesta quota ja ha acabat: eximir-la no donaria cap dret. "
                    "Si no s'ha de cobrar, anul·la-la."
                )
            )
        charges.cancel(locked.charge, reason, by=by, category=EXEMPTION)
        exemption = FeeExemption.objects.create(
            fee=locked, starts_on=locked.due_on, valid_until=until, granted_by=by
        )
        audit.record(
            EXEMPTED_FEE,
            actor=by,
            target=locked,
            reason=reason,
            details={
                "starts_on": locked.due_on.isoformat(),
                "valid_until": until.isoformat(),
                "member_status": member.status,
            },
            request=request,
        )
        if member.status == Member.Status.PENDING:
            _change_status(
                member,
                Member.Status.ACTIVE,
                by=by,
                effective_on=today,
                reason=_("Quota eximida."),
                request=request,
            )
            cards.replace_card(member, by=by, reason=_("Carnet nou en eximir-se la quota."))
        elif member.status == Member.Status.ACTIVE:
            if cards.active_card(member) is None:
                cards.issue_card(member, by=by, request=request)
    return exemption


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
        _reject_returned(locked.charge)
        if locked.charge.status != Charge.Status.PENDING:
            raise ValidationError(_("Només es pot anul·lar una quota pendent."))
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
    offsets = values.fee_reminder_offsets()
    return max(0, -min(offsets)) if offsets else 0


def next_fee_due(member) -> datetime.date | None:
    """Venciment de la propera quota del soci, o `None` si no se n'ha de generar cap ara.
    `member` ve de `cards.load_member` (quotes, càrrecs i pagaments precarregats)."""
    if cards._has_partial_payments(member):
        return None  # P-61: cap regla per als pagaments parcials
    if any(
        fee.charge.status in UNPAID_CHARGE for fee in [*member.annual_fees, *member.instalment_fees]
    ):
        return None  # ja n'hi ha una de viva sense pagar (o un termini, T-M01-49)
    candidates = (
        cards._paid_until(member),
        cards._cluber_until(member),
        validity.exempted_until(member),  # RN-M01-72: la renovació arriba en acabar l'exempció
        validity.instalments_until(member),  # T-M01-49: tots pagats, 12 mesos després del 1r
    )
    dates = [d for d in candidates if d]
    if dates:
        return max(dates)
    if not member.annual_fees:
        birth = cards._birth_date(member)
        if birth:
            return datetime.date(first_fee_year(birth), 1, 1)  # Q-003
    return None


def generate_due_fees(today=None, *, by=None) -> list[AnnualFee]:
    """Genera les quotes que vencen d'aquí al primer recordatori (CA-M01-10 reformulada amb la
    070). Idempotent: una quota viva sense pagar impedeix generar-ne una altra. Amb un pas a
    simpatitzant acceptat, la quota és la de simpatitzant i queda lligada a la sol·licitud (073,
    CA-M01-69); el tipus canvia el dia que venç (`member_requests.apply_due_downgrades`)."""
    from . import member_requests

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
            change = member_requests.accepted_downgrade(fresh)  # 073: renova com a simpatitzant
            try:
                fee = issue_annual_fee(
                    fresh,
                    period=due.year,
                    due_on=due,
                    by=by,
                    fee_type=change.requested_type if change else None,
                    on=today,
                )
            except ValidationError:
                continue  # ja hi ha una quota viva d'aquell període
            if change:
                member_requests.link_renewal_fee(change, fee, by=by)
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
    offsets = values.fee_reminder_offsets()
    pending = AnnualFee.objects.filter(
        kind__in=(AnnualFee.Kind.ANNUAL, AnnualFee.Kind.INSTALMENT),  # T-M01-49 (P-396)
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


# --- Avís previ de la renovació (073 i 085, T-6; RN-M01-73 i RN-M01-93; CA-M01-70) -----------

RENEWAL_NOTICE_TEMPLATE = "avis-renovacio"
RENEWAL_NOTICE_SENT = "members.renewal_notice.sent"


def _downgrade_state(member) -> str:
    """Per al text de l'avís: «accepted», «pending» o "" (es convida a demanar-lo)."""
    from .member_requests import accepted_downgrade, downgrades

    if accepted_downgrade(member) is not None:
        return "accepted"
    if downgrades(member).filter(status=MemberRequest.Status.PENDING).exists():
        return "pending"
    return ""


def _renewal_noticed(member, renews_on) -> bool:
    from apps.core.models import AuditEntry

    return AuditEntry.objects.filter(
        action=RENEWAL_NOTICE_SENT,
        target_type=Member._meta.label_lower,
        target_id=str(member.pk),
        details__renews_on=renews_on.isoformat(),
    ).exists()


def _notice_candidates(today) -> list:
    """(soci, data de renovació) dins la finestra de l'avís: socis de ple dret actius,
    `MEMBER_RENEWAL_NOTICE_MONTHS` abans de la renovació (085, T-6). Un dia perdut es recupera
    mentre la quota no s'ha generat; un cop generada, `next_fee_due` ja no torna data. Les
    baixes obertes (RN-M01-93, punt 6) les mira cada cridador dins el seu `try` per soci."""
    from apps.payments.expiry import months_after

    months = settings.MEMBER_RENEWAL_NOTICE_MONTHS
    members = roster.with_fee_data(
        Member.objects.select_related("person", "type").filter(
            status=S.ACTIVE, type__full_rights=True, person__status=Person.Status.ACTIVE
        )
    )
    found = []
    for member in members:
        try:
            due = next_fee_due(member)
        except Exception:
            logger.exception("Avís de renovació: data de renovació del soci %s", member.pk)
            continue
        if due is not None and months_after(due, -months) <= today < due:
            found.append((member, due))
    return found


def renewal_notices_without_address(today=None) -> list:
    """T-M01-43d: (soci, data de renovació) dels que haurien de rebre l'avís i no el reben
    perquè no tenen cap adreça (RN-M01-78). Un soci amb dades estranyes es registra i se salta:
    la pantalla no falla mai per un soci."""
    from .member_requests import open_leaves

    today = today or local_today()
    found = []
    for member, due in _notice_candidates(today):
        try:
            if open_leaves(member).exists() or _renewal_noticed(member, due):
                continue
            if not recipients.email_for(member.person, today=today, log=False):
                found.append((member, due))
        except Exception:
            logger.exception("Llista de l'avís de renovació: soci %s", member.pk)
    return found


def send_renewal_notices(today=None) -> int:
    """Avís de renovació als `_notice_candidates` sense cap baixa pendent ni programada
    (RN-M01-93, punt 6), una sola vegada per renovació: l'entrada del registre d'activitat
    (soci i data) és la marca. La safata d'avisos de l'app no existeix encara: només correu."""
    from .member_requests import open_leaves

    today = today or local_today()
    sent = 0
    for member, due in _notice_candidates(today):
        try:
            if open_leaves(member).exists():
                continue
            to = recipients.email_for(member.person, today=today)  # RN-M01-78
            if not to:
                # Sense adreça no es marca (surt si n'hi posen una a temps): la secretaria ho
                # veu a «Quotes i impagats» (`renewal_notices_without_address`, T-M01-43d).
                continue
            with transaction.atomic():
                Member.objects.select_for_update(of=("self",)).get(pk=member.pk)
                if _renewal_noticed(member, due):
                    continue
                audit.record(
                    RENEWAL_NOTICE_SENT,
                    actor=audit.system("members.send_renewal_notices"),
                    target=member,
                    details={"renews_on": due.isoformat()},
                )
                mail.queue_email(
                    RENEWAL_NOTICE_TEMPLATE,
                    to=to,
                    person=member.person,
                    context={"renews_on": due, "downgrade": _downgrade_state(member)},
                )
        except Exception:
            logger.exception("Avís de renovació del soci %s no enviat", member.pk)
            continue
        sent += 1
    return sent


# --- Avís al tresorer (079, A-07; RN-M01-89; P-M01-D, pas 6) ---------------------------------

NOTICE_TEMPLATE = "avis-quota-tresorer"
NOTICE_PAID_WHILE_UNPAID = "paid_while_unpaid"
NOTICE_RETURNED = "returned"
NOTICE_TRANSFER_REVERTED = "transfer_reverted"  # 045, P-110
NOTICE_DOWNGRADE_FULL_PRICE = "downgrade_full_price"  # 073, P-334 (T-M01-43)
NOTICE_DOWNGRADE_FEE_CANCELLED = "downgrade_fee_cancelled"  # T-M01-43
NOTICE_SENT = "members.fee.treasurer_notified"


def notify_fee_editors(fee, event: str) -> int:
    """Correu als comptes d'administrador amb el permís d'edició de les quotes (P8 amb edició,
    Q-057) i amb correu de notificació: només el número de soci, el període i el tipus de la
    quota; cap nom ni cap altra dada. Una adreça rep un sol correu. Torna quants n'ha posat a la
    cua; queda al registre d'activitat. Qui el crida és dins la transacció del canvi."""
    from apps.core.permissions import accounts_with_perm

    member = fee.member
    context = {
        "event": event,
        "member_number": member.member_number,
        "period": fee.period,
        "fee_kind": str(fee.get_kind_display()),
    }
    sent = set()
    for account in accounts_with_perm(EDIT_PERMISSION, write=True):
        address = account.notification_email
        if not address or address in sent:
            continue
        if mail.queue_email(NOTICE_TEMPLATE, to=address, person=account.person, context=context):
            sent.add(address)
    audit.record(
        NOTICE_SENT,
        actor=audit.system("members.notify_fee_editors"),
        target=fee,
        details={"event": event, "recipients": len(sent)},
    )
    return len(sent)


# --- Pagaments per revisar (079, A-17; RN-M01-89; CA-M01-98) ---------------------------------
#
# Un soci de baixa que paga una quota anterior a la baixa: `services.on_fee_paid` no falla ni
# canvia res; en deixa una entrada al registre d'activitat. La llista surt d'aquestes entrades i
# s'acaba quan qui pot editar les quotes marca el pagament com a revisat, amb una nota. No hi ha
# cap taula nova: l'estat és al registre, que no es pot modificar.

PAID_AFTER_LEAVING = "members.fee_paid_after_leaving"  # el mateix codi que `services`
PAYMENT_REVIEWED = "members.fee_payment_reviewed"


def _fee_ids(action) -> set[int]:
    from apps.core.models import AuditEntry

    ids = AuditEntry.objects.filter(
        action=action, target_type=AnnualFee._meta.label_lower
    ).values_list("target_id", flat=True)
    return {int(pk) for pk in ids}


def payments_to_review() -> list[AnnualFee]:
    """Quotes pagades per socis de baixa que encara ningú no ha revisat, per ordre de pagament."""
    pending = _fee_ids(PAID_AFTER_LEAVING) - _fee_ids(PAYMENT_REVIEWED)
    return list(
        AnnualFee.objects.filter(pk__in=pending)
        .select_related("member__person", "member__type", "charge")
        .prefetch_related("charge__payments__cancellation")
        .order_by("pk")
    )


def mark_payment_reviewed(fee, *, by, note, request=None) -> None:
    """Treu un pagament de la llista de revisió. Permís d'edició de les quotes (P8 amb edició;
    «no trobat» sense), compte actiu, conflicte d'interès registrat i nota obligatòria, que
    queda al registre d'activitat. No toca el càrrec ni el pagament: si cal una devolució, és
    del 05b."""
    from django.http import Http404

    from apps.core.permissions import has_perm

    from .services import _check_account_active, ensure_not_own_member

    _check_account_active(by)
    if not has_perm(by, EDIT_PERMISSION, write=True):
        raise Http404
    note = (note or "").strip()
    if not note:
        raise ValidationError(_("Cal una nota per marcar el pagament com a revisat."))
    ensure_not_own_member(fee.member, by, request=request)
    with transaction.atomic():
        AnnualFee.objects.select_for_update().get(pk=fee.pk)
        pending = _fee_ids(PAID_AFTER_LEAVING) - _fee_ids(PAYMENT_REVIEWED)
        if fee.pk not in pending:
            raise ValidationError(_("Aquest pagament ja no és a la llista de revisió."))
        audit.record(PAYMENT_REVIEWED, actor=by, target=fee, reason=note, request=request)
