"""Altes pendents: aprovar i rebutjar (T-M01-14; P-M01-A passos 4, 5a i 5b; CA-M01-03 a 05;
RN-M01-05 i RN-M01-06; decisions 039, 059 i 067).

Serveis autoritzats amb P3 (`members.requests.approve_join`). Cada servei comprova el compte, el
permís i el conflicte d'interès ABANS d'obrir la transacció (contracte de `services.py`): així
l'intent rebutjat queda registrat encara que l'operació no es faci.

Aprovar:
- Persona sense soci: soci «pendent» amb el número `últim + 1` del comptador, bloquejat amb
  `SELECT … FOR UPDATE` (RN-M01-05, CA-M01-04), la llavor de l'avatar amb `new_avatar_seed`,
  l'entrada inicial de l'historial i el registre d'activitat amb el valor anterior. Si el número
  que tocaria ja és d'un altre soci, es rebutja: no se salta cap número ni se'n reutilitza cap.
- Persona amb un soci de baixa: readmissió amb `_readmit` (067), mateix registre i mateix número;
  el comptador no avança. Tot, i l'aprovació de la sol·licitud, en una sola transacció.
- **Quota i exempts (retoc del 09/11/2026, 072):**
  - qui ha de pagar queda «pendent» amb la quota anual íntegra del tipus (070), creada amb
    `fees.issue_annual_fee` (número d'ordre de la P-54, sortida E), venciment el dia de
    l'aprovació; passa a actiu quan es confirma el pagament (`services.on_fee_paid`);
  - un exempt per edat (068, P-57 opció 1) passa a «actiu» en aprovar-lo, sense quota ni càrrec
    de 0 €, amb el motiu «Sense quota exigible (RN-M01-65)» i amb carnet (Q-001, Q-002).
- **Acceptacions (Q-044):** les del sol·licitant passen a `core.Consent` amb la versió exacta que
  va acceptar i la referència a la sol·licitud; les del representant es queden a la sol·licitud,
  excepte el butlletí i les imatges d'un menor de 14 anys, que van a la persona del menor amb el
  representant com a qui els dona (072, opció A; T-M01-41).
- **Representant (Q-043, opció 2):** per aprovar l'alta d'un menor, cal confirmar que s'ha
  comprovat el document del representant; queda al registre (sense cap còpia del document).
- **Contacte nou (Q-042, opció 1):** si la sol·licitud porta un correu o un telèfon diferents dels
  de la persona existent, qui aprova decideix si els actualitza (`persons.update`, amb registre).
- **No fa:** la invitació per activar el compte personal. Als menors de 14 anys no se'ls envia
  cap invitació (Q-012); la dels adults continua oberta (no hi ha cap mecanisme especificat).
  Tampoc copia la data de naixement a la persona (T-M01-35).
- **No aprova** (es pot rebutjar): una sol·licitud sense data de naixement; la d'un menor sense
  document (RN-M01-70: com es detecten els duplicats no està decidit); una readmissió amb un tipus
  diferent del que tenia el soci; la d'una persona que ja és sòcia i no és de baixa. Si el
  document coincideix amb una persona existent, cal confirmar que s'ha comprovat la identitat
  (supòsit provisional, [A validar]).

Rebutjar: amb motiu (CA-M01-05), sense soci ni número; s'avisa la persona per correu, sense cap
dada seva ni el motiu (text provisional, [A validar]), a l'adreça de `recipients.email_for`
(RN-M01-78: el representant d'un menor de 14 anys, o d'un de 14 a 17 sense correu propi).
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit, consents, mail, persons
from apps.core.models import Consent
from apps.core.permissions import has_perm

from . import cards, fees, recipients
from .fee_rules import first_fee_year
from .join import OPTIONAL_TEXTS
from .models import (
    JoinAcceptance,
    Member,
    MemberRequest,
    MembershipNumberCounter,
    MemberStatusChange,
    new_avatar_seed,
)
from .services import (
    OWN_MEMBER_REJECTED,
    OwnMemberChange,
    _change_status,
    _check_account_active,
    _readmit,
)

__all__ = ["approval_blocker", "approve_join", "reject_join", "needs_identity_check"]

APPROVE_PERMISSION = "members.requests.approve_join"  # P3
APPROVED = "members.join_request.approved"
REJECTED = "members.join_request.rejected"
MEMBER_CREATED = "members.member_created"
REJECTION_TEMPLATE = "alta-rebutjada"
EXEMPT_REASON = "Sense quota exigible (RN-M01-65)"

S = Member.Status
R = MemberRequest.Status


def needs_identity_check(join_request) -> bool:
    """El document coincidia amb una persona existent (CA-M01-02): la sol·licitud va a aquella
    persona, però l'ha pogut enviar qualsevol."""
    return any(w.get("match") == "document" for w in join_request.duplicate_warning or [])


def _is_own(join_request, by) -> bool:
    return by.person_id == join_request.person_id


def approval_blocker(join_request) -> str | None:
    """Motiu pel qual no es pot aprovar, o None. El mateix text a la pantalla i al servei."""
    if join_request.kind != MemberRequest.Kind.JOIN or join_request.status != R.PENDING:
        return _("Aquesta sol·licitud ja no està pendent.")
    if join_request.birth_date is None:
        return _("No es pot aprovar sense la data de naixement.")
    person = join_request.person
    if join_request.guardian_id_document_number and not person.id_document_number:
        return _(
            "Encara no es pot aprovar l'alta d'un menor sense document: falta decidir com es "
            "detecten els duplicats (RN-M01-70). Es pot rebutjar."
        )
    member = Member.objects.filter(person=person).select_related("type").first()
    if member is not None:
        if member.status != S.LEFT:
            return _("Aquesta persona ja és sòcia.")
        if member.type_id != join_request.requested_type_id:
            return _(
                "Encara no es pot readmetre amb un tipus diferent del que tenia "
                "(%(old)s): falta decidir-ho. Es pot rebutjar."
            ) % {"old": member.type.name}
    return None


def _authorise(join_request, by, request, operation) -> None:
    # Ordre: compte actiu, permís (sense permís, «no trobat»), conflicte d'interès registrat.
    _check_account_active(by)
    if not has_perm(by, APPROVE_PERMISSION):
        raise Http404
    if _is_own(join_request, by):
        audit.record(
            OWN_MEMBER_REJECTED,
            actor=by,
            target=join_request,
            details={"operation": operation},
            request=request,
        )
        raise OwnMemberChange(_("No pots resoldre la teva pròpia sol·licitud d'alta."))


def _next_number() -> int:
    counter = MembershipNumberCounter.objects.select_for_update().get(pk=1)
    number = counter.last_number + 1
    # 039: mai el número d'un altre soci, actiu o de baixa. Un comptador desfasat es corregeix a
    # mà, no saltant números en silenci.
    if Member.objects.filter(member_number=number).exists():
        raise ValidationError(
            _("El número %(n)s ja és d'un altre soci: cal revisar el comptador.") % {"n": number}
        )
    counter.last_number = number
    counter.save(update_fields=["last_number"])
    return number


def _create_member(join_request, *, by, today, request) -> Member:
    number = _next_number()
    member = Member.objects.create(
        person=join_request.person,
        member_number=number,
        type=join_request.requested_type,
        status=S.PENDING,
        joined_on=today,
        avatar_seed=new_avatar_seed(),  # l'únic punt que la genera (lectura de la 060)
    )
    MemberStatusChange.objects.create(
        member=member,
        from_status="",
        to_status=S.PENDING,
        from_type=None,
        to_type=member.type,
        effective_on=today,
        actor_account=by,
    )
    audit.record_changes(
        MEMBER_CREATED,
        actor=by,
        target=member,
        changes={
            "member_number": (None, number),
            "status": ("", S.PENDING),
            "type": (None, member.type.code),
            "joined_on": (None, today),
        },
        request=request,
    )
    return member


def needs_guardian_check(join_request) -> bool:
    """Alta d'un menor (porta les dades del representant): Q-043, opció 2."""
    return bool(join_request.guardian_id_document_number)


def is_exempt(join_request, today) -> bool:
    """Exempt per edat el dia de l'aprovació (068, RN-M01-65)."""
    return today.year < first_fee_year(join_request.birth_date)


def _check_approvable(join_request, identity_checked, guardian_checked) -> None:
    blocker = approval_blocker(join_request)
    if blocker is None and needs_identity_check(join_request) and not identity_checked:
        blocker = _("Cal confirmar que has comprovat la identitat de la persona.")
    if blocker is None and needs_guardian_check(join_request) and not guardian_checked:
        blocker = _("Cal confirmar que has comprovat el document del representant.")
    if blocker:
        raise ValidationError(blocker)


def _grant_applicant_acceptances(join_request, *, by, request) -> int:
    """Q-044: les acceptacions del sol·licitant, amb la versió que va acceptar. Excepció (072,
    opció A; T-M01-41): els consentiments opcionals (butlletí i imatges) que el representant
    dona per a un menor de 14 anys van a la persona del menor, amb el representant com a qui
    els dona. Les altres acceptacions del representant es queden a la sol·licitud."""
    by_guardian = JoinAcceptance.AcceptedBy.GUARDIAN
    accepted = JoinAcceptance.objects.filter(
        Q(accepted_by=JoinAcceptance.AcceptedBy.APPLICANT)
        | Q(accepted_by=by_guardian, legal_text__kind__in=OPTIONAL_TEXTS),
        request=join_request,
    ).select_related("legal_text", "recorded_by")
    for acceptance in accepted:
        consents.grant_accepted(
            join_request.person,
            acceptance.legal_text,
            channel=acceptance.channel,
            recorded_by=acceptance.recorded_by,
            by=by,
            request=request,
            source={"join_request": join_request.pk},
            given_by=(
                Consent.GivenBy.GUARDIAN
                if acceptance.accepted_by == by_guardian
                else Consent.GivenBy.PERSON
            ),
        )
    return len(accepted)


def _update_contact(join_request, *, by, request) -> list[str]:
    """Q-042: només si qui aprova ho ha triat i la sol·licitud porta contacte nou."""
    values = {}
    if join_request.new_contact_email:
        values["contact_email"] = join_request.new_contact_email
    if join_request.new_contact_phone:
        values["phone"] = join_request.new_contact_phone
    if not values:
        return []
    return persons.update(join_request.person, by=by, request=request, **values)


def approve_join(
    join_request,
    *,
    by,
    identity_checked=False,
    guardian_checked=False,
    update_contact=False,
    request=None,
) -> Member:
    """Aprova una alta pendent (P-M01-A, pas 5a, sense la invitació)."""
    _authorise(join_request, by, request, "approve_join")
    today = timezone.localdate()
    with transaction.atomic():
        _check_account_active(by, lock=True)
        former = Member.objects.filter(person_id=join_request.person_id).first()
        readmission = former is not None and former.status == S.LEFT
        if readmission:
            # 067: `_readmit` bloqueja el soci i després la sol·licitud, i torna a validar; per
            # no invertir l'ordre dels bloquejos, aquí la sol·licitud no es bloqueja abans.
            current = MemberRequest.objects.select_related("person").get(pk=join_request.pk)
            _check_approvable(current, identity_checked, guardian_checked)
            member = _readmit(former, current, by=by, effective_on=today, request=request)
        else:
            current = (
                MemberRequest.objects.select_for_update(of=("self",))
                .select_related("person", "requested_type")
                .get(pk=join_request.pk)
            )
            _check_approvable(current, identity_checked, guardian_checked)
            member = _create_member(current, by=by, today=today, request=request)

        member = Member.objects.select_related("person", "type").get(pk=member.pk)
        exempt = is_exempt(current, today)
        fee = None
        if exempt:
            # Q-001: actiu en aprovar-lo, sense quota, i amb carnet (Q-002, fins al 31/12).
            _change_status(member, S.ACTIVE, by=by, effective_on=today, reason=EXEMPT_REASON)
        else:
            fee = fees.issue_annual_fee(member, period=today.year, due_on=today, by=by)
        granted = _grant_applicant_acceptances(current, by=by, request=request)
        contact = _update_contact(current, by=by, request=request) if update_contact else []

        audit.record(
            APPROVED,
            actor=by,
            target=current,
            field="status",
            old=R.PENDING,
            new=R.APPROVED,
            details={
                "member_id": member.pk,
                "readmission": readmission,
                "identity_checked": needs_identity_check(current),
                "guardian_checked": needs_guardian_check(current),
                "exempt": exempt,
                "annual_fee_id": fee.pk if fee else None,
                "consents_granted": granted,
                "contact_updated": contact,
            },
            request=request,
        )
        current.status = R.APPROVED
        current.member = member
        current.resolved_by = by
        current.resolved_at = timezone.now()
        current.effective_on = today
        current.save(
            update_fields=["status", "member", "resolved_by", "resolved_at", "effective_on"]
        )
        if exempt:
            cards.replace_card(member, by=by, reason=_("Carnet d'un soci exempt per edat."))
    member.refresh_from_db()
    return member


def reject_join(join_request, *, by, reason, request=None) -> MemberRequest:
    """Rebutja una alta pendent amb motiu (P-M01-A, pas 5b; CA-M01-05)."""
    _authorise(join_request, by, request, "reject_join")
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal el motiu del rebuig."))
    with transaction.atomic():
        _check_account_active(by, lock=True)
        current = (
            MemberRequest.objects.select_for_update(of=("self",))
            .select_related("person")
            .get(pk=join_request.pk)
        )
        if current.kind != MemberRequest.Kind.JOIN or current.status != R.PENDING:
            raise ValidationError(_("Aquesta sol·licitud ja no està pendent."))
        audit.record_changes(
            REJECTED,
            actor=by,
            target=current,
            changes={"status": (current.status, R.REJECTED)},
            reason=reason,
            request=request,
        )
        current.status = R.REJECTED
        current.resolution_reason = reason
        current.resolved_by = by
        current.resolved_at = timezone.now()
        current.save(update_fields=["status", "resolution_reason", "resolved_by", "resolved_at"])
        person = current.person
        to = recipients.email_for(person, join_request=current)  # RN-M01-78
        if to:
            # Sense cap dada de la persona ni el motiu; dins la transacció: si es desfà, no surt.
            mail.queue_email(REJECTION_TEMPLATE, to=to, person=person)
    return current
