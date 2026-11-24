"""Catàleg d'indicadors del dashboard (T-M08-02; M08-6; RN-M08-03; CA-M08-05).

El catàleg és codi, no base de dades: la definició descriu exactament el càlcul i per això viu
amb el càlcul (P-488). Un indicador sense definició, panell, font, unitat o tipus no es pot
registrar (`Indicator` el rebutja en crear-se). A més de la definició, cada indicador té un text
d'ajuda editable (`dashboard.help_text.<codi>`, creat per la migració de l'app), que es mostra
sota la definició i mai la substitueix (RN-M08-03, opció B de P-488).

`source` és el servei de lectura del mòdul que dona la xifra (M08-2); el dashboard no recalcula
res (RN-M08-04). `detail_permission` i `detail_route` són l'enllaç al detall: el bloc només
enllaça si el compte té aquell permís, i el mòdul el torna a comprovar (RN-M08-05).
"""

from dataclasses import dataclass

from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _

from apps.core import business_settings

HELP_TEXT = "dashboard.help_text"  # família d'ajustos: `dashboard.help_text.<codi>` (P-488)
CODE_MAX_LENGTH = 60 - len(HELP_TEXT) - 1  # la clau d'un ajust té 60 caràcters com a màxim

PANELS = {
    "general": _("General"),
    "economic": _("Econòmic"),
    "activity": _("Activitat"),
    "members": _("Socis"),
    "communication": _("Comunicació"),
}
UNITS = {"count": _("Recompte"), "percent": _("Percentatge"), "cents": _("Import")}
# RN-M08-02: només els recomptes de persones amaguen els grups petits. «Altres» són places,
# material o dates: no diuen res de cap persona.
KINDS = {"people": _("Persones"), "money": _("Diners"), "other": _("Altres")}


class InvalidIndicator(ValueError):
    pass


@dataclass(frozen=True)
class Indicator:
    code: str
    panels: tuple[str, ...]
    name: str | Promise
    definition: str | Promise
    source: str
    unit: str
    kind: str
    detail_permission: str = ""
    detail_route: str = ""

    def __post_init__(self):
        problems = []
        if not (self.code.isidentifier() and self.code.islower()):
            problems.append("codi")
        if len(self.code) > CODE_MAX_LENGTH:
            problems.append("codi massa llarg")
        if not self.panels or not set(self.panels) <= PANELS.keys():
            problems.append("panell")
        for field in ("name", "definition", "source"):
            if not str(getattr(self, field)).strip():
                problems.append(field)
        if self.unit not in UNITS:
            problems.append("unitat")
        if self.kind not in KINDS:
            problems.append("tipus")
        if bool(self.detail_permission) != bool(self.detail_route):
            problems.append("permís i ruta del detall, tots dos o cap")
        if problems:
            raise InvalidIndicator(f"Indicador «{self.code}»: {', '.join(problems)}.")

    @property
    def help_key(self) -> str:
        return f"{HELP_TEXT}.{self.code}"

    def help_text(self, at=None) -> str:
        return business_settings.get(self.help_key, at)


def _catalog(*indicators: Indicator) -> dict[str, Indicator]:
    catalog = {}
    for indicator in indicators:
        if indicator.code in catalog:
            raise InvalidIndicator(f"Indicador «{indicator.code}» repetit.")
        catalog[indicator.code] = indicator
    return catalog


MEMBERS = ("members.list", "administration:members_list")  # P4
FEES = ("members.fees.view", "administration:fees")  # P10
LICENCES = ("licences.list", "administration:licences")  # LC4
ACTIVITY_REPORTS = ("activities.reports.view", "administration:activity_reports")  # AC20
EQUIPMENT_STOCK = ("equipment.stock.view", "administration:equipment_reports")  # MT4
EQUIPMENT_REVIEWS = ("equipment.reviews.manage", "administration:equipment_reports")  # MT11
GRANTS = ("grants.view", "administration:grants_calendar")  # AJ3
TREASURY = ("treasury.view", "administration:treasury_accounts")  # T1
WITHOUT_INVOICE = ("expenses.pay", "administration:expenses_without_invoice")  # MG2
MANDATES = ("payments.mandates.view", "administration:payments_campaign")  # A4


def _i(code, panels, name, definition, source, unit, kind, detail=("", "")):
    return Indicator(code, panels, name, definition, source, unit, kind, *detail)


# Indicadors inicials (M08-6, F §8.4). Definicions de RN-M08-10 (P-488).
CATALOG = _catalog(
    # General
    _i("active_members", ("general",), _("Socis actius"),
       _("Socis amb l'estat «actiu» el darrer dia del període."),
       "members.stats", "count", "people", MEMBERS),
    _i("new_members", ("general",), _("Altes del període"),
       _("Socis amb la data d'alta dins del període."),
       "members.stats", "count", "people", MEMBERS),
    _i("unpaid_members", ("general", "members"), _("Socis impagats"),
       _("Socis amb l'estat «impagat» el darrer dia del període (RN-M01-07)."),
       "members.stats", "count", "people", FEES),
    _i("free_places", ("general",), _("Places lliures a les properes activitats"),
       _("Places totals menys inscripcions confirmades de les activitats obertes que "
         "comencen després d'avui."),
       "activities.stats", "count", "other", ACTIVITY_REPORTS),
    _i("licences_to_renew", ("general", "members"), _("Llicències per renovar"),
       _("Llicències vigents que caduquen dins dels dies de «per renovar» de les "
         "llicències (VC-41)."),
       "licences.expiring", "count", "people", LICENCES),
    _i("equipment_to_review", ("general",), _("Material per revisar"),
       _("Equips amb una revisió prevista abans del final del període."),
       "equipment.stock", "count", "other", EQUIPMENT_REVIEWS),
    _i("grants_closing", ("general",), _("Ajuts que tanquen aviat"),
       _("Dates de les convocatòries d'ajuts dins dels dies d'avís dels ajuts (VC-36)."),
       "grants.calendar", "count", "other", GRANTS),
    # Econòmic
    _i("activity_margin", ("economic",), _("Marge de les activitats realitzades"),
       _("Suma dels marges (ingressos − despeses − cost de material) de les activitats "
         "acabades dins del període."),
       "margins.activity_margin", "cents", "money"),
    _i("department_income", ("economic",), _("Ingressos per departament"),
       _("Ingressos de cada departament dins del període; la suma dels departaments és el "
         "total."),
       "margins.department_report", "cents", "money"),
    _i("department_expenses", ("economic",), _("Despeses per departament"),
       _("Despeses de cada departament dins del període; la suma dels departaments és el "
         "total."),
       "margins.department_report", "cents", "money"),
    _i("grants_granted", ("economic",), _("Ajuts concedits per departament"),
       _("Import concedit dels ajuts resolts dins del període, per departament."),
       "grants.granted_by_department", "cents", "money", GRANTS),
    _i("expenses_without_invoice", ("economic",), _("Despeses sense factura"),
       _("Nombre de despeses del període que encara no tenen factura."),
       "expenses.expenses_for", "count", "other", WITHOUT_INVOICE),
    _i("expenses_without_invoice_amount", ("economic",), _("Import de les despeses sense factura"),
       _("Suma de les despeses del període que encara no tenen factura."),
       "expenses.expenses_for", "cents", "money", WITHOUT_INVOICE),
    _i("treasury_balances", ("economic",), _("Saldos de tresoreria"),
       _("Saldo de cada compte el darrer dia del període."),
       "treasury.balance", "cents", "money", TREASURY),
    # Activitat
    _i("occupancy", ("activity",), _("Ocupació de cursos i sortides"),
       _("Places ocupades (inscripcions confirmades) / places totals de les activitats del "
         "període."),
       "activities.stats", "percent", "people", ACTIVITY_REPORTS),
    _i("attendance", ("activity",), _("Assistència"),
       _("Assistències registrades / inscrits confirmats de les sessions fetes dins del "
         "període."),
       "activities.stats", "percent", "people", ACTIVITY_REPORTS),
    _i("weekly_enrolments", ("activity",), _("Inscripcions per setmana"),
       _("Inscripcions confirmades de cada setmana del període."),
       "activities.stats", "count", "people", ACTIVITY_REPORTS),
    _i("equipment_in_use", ("activity",), _("Material en ús"),
       _("Equips prestats o assignats a una activitat el darrer dia del període."),
       "equipment.stock", "count", "other", EQUIPMENT_STOCK),
    # Socis
    _i("joins_and_leaves", ("members",), _("Altes i baixes per mes"),
       _("Socis amb la data d'alta i socis que passen a «baixa» en cada mes del període."),
       "members.stats", "count", "people", MEMBERS),
    _i("active_by_type", ("members",), _("Socis actius per tipus"),
       _("Socis amb l'estat «actiu» el darrer dia del període, per tipus de soci."),
       "members.stats", "count", "people", MEMBERS),
    _i("retention", ("members",), _("Retenció"),
       _("1 − baixes del període / socis actius el primer dia del període."),
       "members.stats", "percent", "people", MEMBERS),
    _i("signed_mandates", ("members",), _("Mandats signats"),
       _("Mandats signats durant la campanya de mandats; només mentre hi ha campanya."),
       "payments.campaign_status", "count", "people", MANDATES),
    # Comunicació
    _i("confirmed_subscribers", ("communication",), _("Subscriptors confirmats"),
       _("Subscriptors del butlletí que han confirmat el correu."),
       "website.counts", "count", "people"),
    _i("pending_contact_messages", ("communication",), _("Missatges de contacte pendents"),
       _("Missatges del formulari de contacte que encara no s'han respost."),
       "website.counts", "count", "other"),
    _i("conference_attendees", ("communication",), _("Assistents a conferències"),
       _("Assistents a les conferències fetes dins del període (quan existeixi l'11)."),
       "history.attendees", "count", "people"),
)  # fmt: skip


def name_of(code: str) -> str:
    """El nom de la fila de l'ajust d'ajuda (família `dashboard.help_text`)."""
    indicator = CATALOG.get(code)
    return str(indicator.name) if indicator else code
