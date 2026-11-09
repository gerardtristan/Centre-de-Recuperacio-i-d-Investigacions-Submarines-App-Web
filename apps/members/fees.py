"""Quotes i impagats (T-M01-18; P-M01-D, passos 5; HU-M01-12; RN-M01-09, decisió 040).

Implementat: la revisió de l'estat de les quotes dels socis actius i impagats (P10) i la marca
manual d'impagat, amb motiu, amb els serveis de la T-M01-12 (`mark_unpaid`, `unmark_unpaid`;
P9). L'estat de la quota és el de la T-M01-15 (`roster.fee_state`), sense canvis.

**No implementat, perquè depèn de decisions obertes** (docs/planning.md, fila de la T-M01-18):
generar i renovar quotes (P-54, P-61, P-29, P-57; CA-M01-10 i 11) i els recordatoris
(RN-M01-14 [A validar], dies dels ajustos S-M01-04 i RN-M01-46, venciment P-29 i P-61). Aquí no
es crea cap quota ni cap càrrec.
"""

import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from apps.core import charges
from apps.core.models import Charge

from . import roster
from .fee_rules import local_today
from .models import AnnualFee, Member

S = Member.Status
VIEW = roster.FEES  # P10
REVIEWED = (S.ACTIVE, S.UNPAID)  # els únics que es poden marcar o desmarcar (RN-M01-07)


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
