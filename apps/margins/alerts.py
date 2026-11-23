"""Avís de marge baix (T-M09-13; RN-M09-14, CA-M09-12).

Quan es desa la previsió d'una activitat (els costos previstos, T-M09-09) i el marge previst queda
per sota del llindar (`margin.low_margin_threshold_cents`, VC-31; d'inici 0 €, S-M09-04), el
responsable de l'activitat i el tresorer reben un correu. Un sol avís per cada previsió: si el
marge previst no canvia, no se'n repeteix cap (`LowMarginAlert`). L'avís a l'app arribarà amb les
notificacions de l'app; ara, només el correu."""

from apps.core import audit, business_settings, mail
from apps.core.charges import euros
from apps.core.permissions import accounts_with_perm
from apps.members import recipients

from . import services
from .models import LowMarginAlert

THRESHOLD = "margin.low_margin_threshold_cents"  # VC-31
TEMPLATE = "avis-marge-baix"
PAY_EXPENSES = "expenses.pay"  # MG2: qui rep els avisos del tresorer (P-473)
ALERT_SENT = "margins.low_margin_alert_sent"


def check_forecast(activity) -> bool:
    """A la transacció de qui desa la previsió. Torna si s'ha enviat l'avís."""
    margin = services.activity_margin(activity).margin_cents
    threshold = business_settings.get(THRESHOLD)
    if margin >= threshold:
        return False
    last = LowMarginAlert.objects.filter(activity=activity).order_by("-pk").first()
    if last is not None and last.margin_cents == margin:
        return False
    LowMarginAlert.objects.create(activity=activity, margin_cents=margin, threshold_cents=threshold)
    context = {"activity": activity.title, "margin": euros(margin), "threshold": euros(threshold)}
    sent = set()
    responsible = recipients.email_for(activity.responsible)
    if responsible:
        mail.queue_email(TEMPLATE, to=responsible, person=activity.responsible, context=context)
        sent.add(responsible)
    for account in accounts_with_perm(PAY_EXPENSES, write=True):
        address = account.notification_email
        if address and address not in sent:
            mail.queue_email(TEMPLATE, to=address, person=account.person, context=context)
            sent.add(address)
    audit.record(
        ALERT_SENT,
        actor=audit.system("margins"),
        target=activity,
        details={"margin": margin, "threshold": threshold, "emails": len(sent)},
    )
    return True
