"""«Vàlid fins al» del soci: l'únic càlcul de fins quan està al corrent (decisió 079, A-02;
RN-M01-86; RN-M01-18 i RN-M01-19; decisions 068, 070 i 072).

El fan servir el carnet (`cards`), l'estat de la quota del llistat, la fitxa i la revisió de
quotes (`roster.fee_state`), la generació de renovacions (`fees`) i els serveis per a altres
mòduls (`services`). Abans hi havia tres respostes que podien no coincidir (P-71).

«Vàlid fins al» és la data més tardana d'aquestes:
- els que paguen: un any des del pagament confirmat, fins al mateix dia de l'any següent
  (`twelve_months_after`; el 29/02 passa al 28/02);
- els exempts per edat sense cap quota: el 31/12 de l'últim any exempt (Q-002);
- els importats de Cluber: un any des de «Data alta/renovació» (Q-076; 097, punt 1);
- una quota eximida (RN-M01-72 i RN-M01-94; T-M01-40): un any des del venciment de la quota,
  mentre no s'hagi emès una quota posterior del mateix període (que és com es desfà).
- els terminis de la quota de ple dret (T-M01-49; 097, P-61 punt 1): un any des del pagament del
  primer termini, però mai més enllà del venciment del primer termini sense pagar.
Amb pagaments parcials d'una quota no n'hi ha cap.

Funcions pures sobre un soci carregat amb `roster.with_fee_data` (quotes anuals, càrrecs,
pagaments i altes aprovades): no escriuen res. L'impagat continua sent una marca manual del
tresorer (RN-M01-09, 040) i no surt d'aquí.
"""

from datetime import date

from django.utils import timezone

from apps.core.charges import active_payments
from apps.core.models import Charge

from .fee_rules import first_fee_year


def twelve_months_after(day: date) -> date:
    """070: 12 mesos des del pagament confirmat. De data a data; si el mes de venciment no té
    aquell dia (29 de febrer), l'últim del mes (Codi civil, art. 5.1)."""
    try:
        return day.replace(year=day.year + 1)
    except ValueError:
        return day.replace(year=day.year + 1, day=28)


def has_partial_payments(member) -> bool:
    return any(
        p.amount_cents < fee.charge.amount_cents
        for fee in member.annual_fees
        for p in active_payments(fee.charge)
    )


def paid_until(member) -> date | None:
    """Data de renovació del darrer pagament confirmat (070): 12 mesos després. `None` si no n'hi
    ha cap o si alguna quota té pagaments parcials. Una quota de renovació generada abans de la
    data i encara pendent no treu la validesa del període ja pagat."""
    paid_on = []
    for fee in member.annual_fees:
        payments = active_payments(fee.charge)
        if any(p.amount_cents < fee.charge.amount_cents for p in payments):
            return None
        if fee.charge.status != Charge.Status.PAID:
            continue
        if len(payments) != 1 or payments[0].paid_at is None:
            return None
        paid_on.append(timezone.localdate(payments[0].paid_at))
    return twelve_months_after(max(paid_on)) if paid_on else None


def birth_date(member) -> date | None:
    """La de la persona (T-M01-33) o, si encara no hi és, la declarada a l'alta aprovada."""
    if member.person.birth_date:
        return member.person.birth_date
    joins = member.person.approved_joins
    return joins[0].birth_date if joins else None


def exempt_until(member) -> date | None:
    """Q-002 (072): exempt per edat i sense cap quota, fins al 31/12 de l'últim any exempt (l'any
    abans del primer any de quota, 068). Passat aquest dia, ja no compta: cal la quota (Q-003)."""
    if member.annual_fees:
        return None
    birth = birth_date(member)
    return date(first_fee_year(birth) - 1, 12, 31) if birth else None


def cluber_until(member) -> date | None:
    """Q-076 (072; 097, punt 1): un any des de «Data alta/renovació» de Cluber."""
    renewed = member.cluber_renewed_on
    return twelve_months_after(renewed) if renewed and member.cluber_id else None


def exempted_until(member) -> date | None:
    """RN-M01-72 i RN-M01-94: final del període de la darrera quota eximida que continua vigent.
    Una exempció deixa de comptar quan hi ha una quota posterior del mateix període (així es
    desfà, P-54 sortida E; també passa amb la quota d'una readmissió el mateix any)."""
    last = {}
    for fee in member.annual_fees:
        last[fee.period] = max(last.get(fee.period, 0), fee.sequence)
    dates = [
        fee.exemption.valid_until
        for fee in member.annual_fees
        if fee.sequence == last[fee.period] and getattr(fee, "exemption", None) is not None
    ]
    return max(dates) if dates else None


def instalments_until(member) -> date | None:
    """097 (P-61, punt 1): el carnet val mentre els terminis estan al dia. Per a cada període amb
    el primer termini pagat, la renovació (12 mesos després d'aquell pagament, 070) o, si és abans,
    el venciment d'un termini pendent o retornat. Els anul·lats no compten."""
    plans = {}
    for fee in member.instalment_fees:
        if fee.charge.status != Charge.Status.CANCELLED:
            plans.setdefault(fee.period, []).append(fee)
    ends = []
    for plan in plans.values():
        first = next((f for f in plan if f.instalment == 1), None)
        payments = active_payments(first.charge) if first else []
        if first is None or first.charge.status != Charge.Status.PAID or len(payments) != 1:
            continue
        if payments[0].paid_at is None:
            continue
        unpaid = [f.due_on for f in plan if f.charge.status != Charge.Status.PAID]
        ends.append(min([twelve_months_after(timezone.localdate(payments[0].paid_at)), *unpaid]))
    return max(ends) if ends else None


def valid_until(member) -> date | None:
    """«Vàlid fins al» del soci, o `None` si no en té cap o si hi ha pagaments parcials."""
    if has_partial_payments(member):
        return None
    candidates = (
        paid_until(member),
        exempt_until(member),
        cluber_until(member),
        exempted_until(member),
        instalments_until(member),
    )
    dates = [d for d in candidates if d]
    return max(dates) if dates else None


def waived_now(member, today: date) -> bool:
    """El «vàlid fins al» vigent surt només d'una quota eximida (no d'un pagament)."""
    until = exempted_until(member)
    return (
        until is not None
        and today <= until
        and valid_until(member) == until
        and until not in (paid_until(member), cluber_until(member))
    )


def exempt_now(member, today: date) -> bool:
    """El «vàlid fins al» vigent surt només de l'exempció per edat."""
    until = exempt_until(member)
    return until is not None and today <= until and valid_until(member) == until
