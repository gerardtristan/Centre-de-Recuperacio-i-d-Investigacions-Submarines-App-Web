"""Avisos del M01 a l'inici de l'àrea de socis (T-M01-35; RN-M01-55, CA-M01-43). La 00 no
importa cap mòdul: la plantilla d'inici carrega aquesta etiqueta."""

from django import template

from .. import birth_date

register = template.Library()


@register.inclusion_tag("members/_birth_date_notice.html", takes_context=True)
def birth_date_notice(context):
    user = context.get("user")
    person = getattr(user, "person", None) if getattr(user, "is_authenticated", False) else None
    return {"show": person is not None and birth_date.missing_for(person)}


def session_member(context):
    """El soci de la persona de la sessió, només al compte personal: el d'administrador no és la
    porta del soci (decisions 015 i 018). Sense soci, cap."""
    from ..models import Member

    user = context.get("user")
    person = getattr(user, "person", None) if getattr(user, "is_authenticated", False) else None
    if person is None or getattr(user, "kind", None) != "personal":
        return None
    return Member.objects.filter(person=person).first()


@register.simple_tag(takes_context=True)
def member_home(context):
    """Inici de l'àrea de socis (T-DX-17 i T-DX-60; design-system §6.18): la quota, el carnet, els
    pendents, els pagaments recents, la història i la llicència, només del soci de la sessió i
    amb els mateixos càlculs que «Les meves quotes», «Com pago la quota» i «El meu carnet». Sense
    soci (o amb el compte d'administrador), None."""
    from apps.core.models import Charge
    from apps.payments.models import FeeMethod
    from apps.payments.preferences import fee_payment_method

    from .. import cards, roster, services
    from .. import settings as member_settings
    from ..fee_rules import local_today
    from ..models import AnnualFee
    from ..views.personal import _fee_row
    from .vigencia import in_fee_warning_window

    member = session_member(context)
    if member is None:
        return None
    loaded = cards.load_member(member.pk)
    today = local_today()
    fee = roster.fee_state(loaded, today)
    card = cards.active_card(loaded)
    years = cards.years_of_membership(loaded, today)
    classic = member_settings.classic_member_years()  # VC-04: 0, sense insígnia
    method = fee_payment_method(member)
    rows = [
        _fee_row(f)
        for f in AnnualFee.objects.filter(member=member)
        .select_related("charge")
        .prefetch_related("charge__payments__cancellation")
        .order_by("-period", "-id")
    ]
    return {
        "member": loaded,
        "fee": fee,
        "countdown": fee is not None and in_fee_warning_window(fee.until),
        "method": method,
        "method_label": FeeMethod(method).label if method else "",
        "card": card,
        "validity": cards.validity(loaded, card, today) if card else None,
        "pending": [r for r in rows if r["fee"].charge.status == Charge.Status.PENDING],
        "recent": [r for r in rows if r["fee"].charge.status == Charge.Status.PAID][:3],
        "years": years,
        # El mateix que el carnet (RN-M01-23): mai amb una data d'alta aproximada.
        "classic": bool(classic)
        and years is not None
        and not loaded.joined_on_is_approximate
        and years >= classic,
        "licence": services.licence_record(loaded.person),
    }
