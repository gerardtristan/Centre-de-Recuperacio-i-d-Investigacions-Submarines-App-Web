"""Avisos dels ajuts per la cua (T-M09A-06; RN-M09A-04, 05, 06 i 20; CA-M09A-01, 02 i 03).

La tasca diària (`tasks.send_reminders`) envia, al responsable de la sol·licitud i al tresorer:
- **tancament:** per a cada tram de `grants.deadline_reminder_days` (VC-36: 30, 14 i 7), les
  sol·licituds detectades o en preparació la convocatòria de les quals tanca just aquell dia de
  distància. Si `closes_on` canvia, l'avís es calcula sobre la data nova; si ja ha passat, no
  surt (només el dia exacte).
- **resposta:** el dia de la resposta prevista, si la sol·licitud encara és «presentada».
- **justificació:** els mateixos trams abans de la data de justificació (o de la pròrroga, si
  n'hi ha) de les concedides [A validar: junta, S-M09A-04].

Cada avís és una fila de `GrantReminder` (només INSERT) amb una restricció única: si la tasca
s'executa dues vegades el mateix dia, el segon intent no envia res. Els avisos dels requeriments
són de la T-M09A-15. L'avís a l'app arribarà amb les notificacions de l'app; ara, només el correu.
"""

import datetime
import logging

from django.db import IntegrityError, transaction
from django.db.models import F
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import audit, business_settings, mail
from apps.core.permissions import accounts_with_perm

from .models import GrantApplication, GrantReminder

logger = logging.getLogger(__name__)

DEADLINE_DAYS = "grants.deadline_reminder_days"  # VC-36
CLOSE_TEMPLATE = "avis-ajut-tancament"
RESPONSE_TEMPLATE = "avis-ajut-resposta"
JUSTIFY_TEMPLATE = "avis-ajut-justificacio"
# El «tresorer» dels avisos: qui configura els dies dels avisos (AJ10; d'inici el Tresorer i
# l'Administrador). Els destinataris surten de la matriu, mai d'un rol escrit al codi (P-503).
TREASURER = "grants.alert_days"
REMINDER_SENT = "grants.reminder_sent"
S = GrantApplication.Status


def _date(value) -> str:
    return value.strftime("%d/%m/%Y")


def addresses(responsible) -> dict[str, object]:
    """{adreça: persona}: els comptes d'administrador actius del responsable i el tresorer. Una
    adreça, un correu."""
    found = {}
    own = Account.objects.filter(
        person=responsible, kind=Account.Kind.ADMIN, status=Account.Status.ACTIVE
    ).exclude(notification_email="")
    for account in [*own.select_related("person"), *accounts_with_perm(TREASURER)]:
        if account.notification_email:
            found.setdefault(account.notification_email, account.person)
    return found


def remind(application, *, kind, due_on, template, context, responsible, requirement=None) -> bool:
    """Envia un avís un sol cop: la fila de `GrantReminder` i els correus van junts; si la fila ja
    hi és (restricció única), no s'envia res."""
    try:
        with transaction.atomic():
            reminder = GrantReminder.objects.create(
                application=application, requirement=requirement, kind=kind, due_on=due_on
            )
            sent = addresses(responsible)
            for address, person in sent.items():
                mail.queue_email(template, to=address, person=person, context=context)
            audit.record(
                REMINDER_SENT,
                actor=audit.system("grants.reminders"),
                target=reminder,
                details={"kind": kind, "due_on": due_on.isoformat(), "emails": len(sent)},
            )
    except IntegrityError:
        return False
    return True


def _context(application, **extra) -> dict:
    call = application.call
    name = f"{call.name} {call.edition_label}".strip()
    return {"call": name, "body": call.body, "application_id": application.pk, **extra}


def send_due(today: datetime.date | None = None) -> int:
    """Torna quants avisos s'han enviat avui."""
    today = today or timezone.localdate()
    sent = 0
    applications = GrantApplication.objects.select_related("call")
    justify_on = Coalesce("justification_extended_to", F("call__justification_due_on"))
    for days in sorted(set(business_settings.get(DEADLINE_DAYS, today)), reverse=True):
        target = today + datetime.timedelta(days=days)
        for application in applications.filter(
            status__in=(S.DETECTED, S.PREPARING), call__closes_on=target
        ):
            context = _context(application, closes_on=_date(target), days=days)
            sent += _safe(application, f"close_{days}", target, CLOSE_TEMPLATE, context)
        for application in applications.annotate(justify_on=justify_on).filter(
            status=S.GRANTED, justify_on=target
        ):
            context = _context(application, due_on=_date(target), days=days)
            sent += _safe(application, f"justify_{days}", target, JUSTIFY_TEMPLATE, context)
    for application in applications.filter(status=S.SUBMITTED, expected_response_on=today):
        context = _context(
            application,
            submitted_on=_date(application.submitted_on),
            expected_on=_date(today),
        )
        sent += _safe(application, "response", today, RESPONSE_TEMPLATE, context)
    return sent


def _safe(application, kind, due_on, template, context) -> int:
    try:
        return int(
            remind(
                application,
                kind=kind,
                due_on=due_on,
                template=template,
                context=context,
                responsible=application.responsible,
            )
        )
    except Exception:  # un avís que falla no atura els altres
        logger.exception("Avís d'ajut %s de la sol·licitud %s", kind, application.pk)
        return 0
