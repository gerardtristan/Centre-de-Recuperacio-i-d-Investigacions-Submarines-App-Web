"""Navegació comuna de l'administració (T-M01-46; sistema de disseny §6.1 i §6.2).

El menú es construeix al servidor amb els permisos del compte: una entrada només hi surt si el
compte té el permís que la ruta declara (`apps/members/permissions.py` per a les rutes del 01;
`BASE_ROUTES` per a les de la 00). No és cap control: cada vista torna a comprovar el permís.
Només ajuda a no ensenyar enllaços que respondrien «no trobat».

- Sense una sessió vàlida de l'administració no hi ha menú i no es fa cap consulta.
- Es calcula com a màxim una vegada per petició, i només si la plantilla el fa servir (un
  fragment d'HTMX no el demana). Els permisos són els de `request_permissions`, els mateixos
  que ja ha calculat la vista.
"""

from dataclasses import dataclass

from django.urls import reverse
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy as _

from apps.core.business_settings import section_code
from apps.core.permission_catalog import CATALOG, SCOPE_ALL
from apps.core.permissions import has_perm, request_permissions, scope_for
from apps.core.under_construction import PERMISSION as UNDER_CONSTRUCTION
from apps.members.permissions import READ, ROUTES, WRITE
from apps.previews.screens import discover

from .security import AREA_ADMIN
from .sessions import session_area_is_valid

# Rutes de la 00 que surten al menú. Com a `ROUTES`, cada grup són els permisos que calen tots
# alhora; aquí n'hi pot haver més d'un, i n'hi ha prou amb un grup (el registre d'activitat es
# veu sencer amb M6 o només la part de socis amb P20). És el que comprova cada vista.
BASE_ROUTES = {
    "administration:home": ((),),
    "administration:accounts": ((("core.accounts.reset_credentials", READ),),),
    "administration:permission_matrix": ((("core.permissions.edit", READ),),),  # M3b (T-RP-03)
    "administration:audit_log": (
        (("core.audit.view", READ),),
        (("members.audit.view", READ),),
    ),
    "administration:gdpr_requests": ((("core.gdpr.handle", READ),),),  # M11 (T-M01-22)
    "administration:guest_links": ((("core.guest_links.manage", READ),),),  # M5 (T-M00-02)
    "administration:locked_data": ((("core.locked_data.view", READ),),),  # M13 (T-M00-04)
    "administration:treasury_accounts": ((("treasury.view", READ),),),  # T1 (T-M04-15)
    "administration:treasury_movements": ((("treasury.view", READ),),),
    "administration:treasury_reconciliation": ((("treasury.view", READ),),),  # T1 (T-M04-15)
    "administration:bank_statement": ((("core.bank_statement.import", READ),),),  # M9 (T-M00-01)
    "administration:payments_list": ((("payments.view", READ),),),  # B6 (T-M05b-16)
    "administration:licences": ((("licences.list", READ),),),  # LC4 (T-M06-09)
    "administration:activities": ((("activities.manage", READ),),),  # AC7 (T-M02-06)
    "administration:places": ((("activities.places.view", READ),),),  # AC21 (T-M02-39)
    "administration:catalogue": ((("activities.catalogue.manage", WRITE),),),  # AC6 (T-M02-05b)
    "administration:filings": ((("activities.filings.manage", READ),),),  # AC26 (T-M02-44b)
    # MG1 amb l'abast «tot»: amb «les seves activitats» no es pot registrar sense repartiment.
    "administration:expense_new": ((("expenses.record", WRITE, SCOPE_ALL),),),  # T-M09-06
    "administration:expenses_without_invoice": ((("expenses.pay", READ),),),  # MG2 (T-M09-15)
    "administration:grants_calendar": ((("grants.view", READ),),),  # AJ3 (T-M09A-05)
    "administration:margin_periods": ((("expenses.periods.close", READ),),),  # MG11 (T-M09-16)
    "administration:licences_prices": ((("licences.prices", READ),),),  # LC8 (T-M06-02)
    "administration:payments_remittances": ((("payments.remittances", READ),),),  # B3
    "administration:payments_mandates": ((("payments.mandates.view", READ),),),  # A4 (T-M05a-14)
    "administration:payments_campaign": ((("payments.mandates.view", READ),),),  # A4 (T-M05a-13b)
    # T-M03-19: n'hi ha prou amb un dels tres informes (MT4, MT11 o MT12).
    "administration:equipment_reports": (
        (("equipment.stock.view", READ),),
        (("equipment.reviews.manage", READ),),
        (("equipment.costs.view", READ),),
    ),
    "administration:equipment_usage_rates": ((("settings.section.equipment", READ),),),  # VC-28
    # T-M02-16b: AC9; l'instructor només hi veu les seves sessions (ho filtra la vista).
    "administration:attendance_sessions": ((("activities.attendance.record", READ),),),
    # Només amb el permís (DX1), encara que SHOW_UNDER_CONSTRUCTION ensenyi les pantalles a tothom.
    "administration:previews:index": (((UNDER_CONSTRUCTION, READ),),),  # T-DX-50
    # T-AJ-02: n'hi ha prou amb veure un apartat d'ajustos (RN-RP-22).
    "administration:settings": tuple(
        ((code, READ),) for code in CATALOG if code.startswith(section_code(""))
    ),
}

# Ruta de l'entrada, text i les altres pantalles que en pengen (també la marquen com a actual).
ENTRIES = (
    ("administration:home", _("Inici"), ()),
    (
        "administration:members_list",
        _("Llistat de socis"),
        (
            "administration:member_detail",
            "administration:member_edit",
            "administration:member_join_date",
            "administration:licence_add",
            "administration:licence_edit",
            "administration:member_leave_create",
            # T-DX-76 (V5): les subpàgines de la fitxa del soci.
            "administration:member_birth_date_check",
            "administration:member_card_revoke",
            "administration:member_fee_cancel",
            "administration:member_fee_choose_instalments",
            "administration:member_fee_exempt",
            "administration:member_fee_instalments",
            "administration:member_invite",
            "administration:member_totp_reset",
            "administration:members_export",
            "administration:treasury_manual_payment",  # s'obre des de la fitxa
        ),
    ),
    (
        "administration:join_requests",
        _("Altes pendents"),
        ("administration:join_approve", "administration:join_reject"),
    ),
    ("administration:join_in_person", _("Alta presencial"), ()),
    (
        "administration:member_requests",
        _("Sol·licituds de socis"),
        ("administration:member_request_detail",),
    ),
    ("administration:licence_bulk_confirm", _("Llicències pendents de confirmar"), ()),
    (
        "administration:licences",
        _("Llicències"),
        (
            "administration:licences_activate",
            "administration:licences_file",
            "administration:licences_export",
            "administration:licences_unconfirmed",  # T-M06-24b
            "administration:licences_confirm",
        ),
    ),  # T-M06-09 (vistes v1); text i lloc per revisar amb DISSENY
    ("administration:licences_prices", _("Llicències: tipus i preus"), ()),  # T-M06-02 (v2)
    (
        "administration:activities",
        _("Cursos i sortides"),
        (
            "administration:activity_course_add",
            "administration:activity_outing_add",
            "administration:activity_detail",
            "administration:activity_edit",
        ),
    ),  # T-M02-06; revisat amb DISSENY (23/11): fitxa, alta i edició són filles del llistat
    (
        "administration:places",
        _("Llocs"),
        ("administration:place_add", "administration:place_detail"),
    ),  # T-M02-39; text i lloc per revisar amb DISSENY
    (
        "administration:catalogue",
        _("Catàleg de cursos"),
        ("administration:catalogue_entry_add", "administration:catalogue_entry"),
    ),  # T-M02-05b; text i lloc per revisar amb DISSENY
    (
        "administration:filings",
        _("Homologacions"),
        (
            "administration:filing_detail",
            "administration:filing_filed",
            "administration:filing_done",
            "administration:filing_reject",
            "administration:filing_request",
            "administration:filings_csv",
        ),
    ),  # T-M02-44b; text i lloc per revisar amb DISSENY
    (
        "administration:attendance_sessions",
        _("Passar llista"),
        (
            "administration:attendance_roll",
            "administration:attendance_roll_session",
            "administration:assessment_sheet",  # T-M02-17b: s'obre des de la llista
            "administration:course_outcomes",  # T-M02-19b: també
            "administration:course_certificate",
            "administration:reinforcement_list",  # T-M02-18b: també
            "administration:reinforcement_propose",
        ),
    ),  # T-M02-16b; text i lloc provisionals per a DISSENY
    (
        "administration:membership_types",
        _("Tipus de soci"),
        ("administration:membership_type_edit",),
    ),  # T-DX-56 (T-M01-52)
    (
        "administration:fees",
        _("Quotes i impagats"),
        (
            "administration:fee_mark_unpaid",
            "administration:fee_unmark_unpaid",
            "administration:fee_payment_reviewed",
        ),
    ),
    # T-DX-49: les pantalles que s'obren des d'una entrada la deixen marcada com a actual.
    (
        "administration:equipment_reports",
        _("Material: informes"),
        ("administration:equipment_activity_cost",),
    ),  # T-M03-19; text i lloc provisionals per a DISSENY
    ("administration:equipment_usage_rates", _("Cost d'ús del material"), ()),  # T-M03-22; DISSENY
    ("administration:expense_new", _("Despesa nova"), ()),  # T-M09-06; text i lloc: DISSENY
    (
        "administration:expenses_without_invoice",
        _("Despeses sense factura"),
        # El marge d'una activitat no té entrada pròpia (porta l'activitat a l'adreça): penja
        # d'aquí fins que l'enllaci la fitxa de l'activitat (vistes del 02). Lloc: DISSENY.
        (
            "administration:activity_margin",
            "administration:activity_margin_planned",
            "administration:activity_margin_close",
        ),
    ),  # T-M09-15; text i lloc per revisar amb DISSENY
    (
        "administration:margin_periods",
        _("Tancament de períodes"),
        (
            "administration:margin_period_create",
            "administration:margin_period_close",
            "administration:margin_period_reopen",
        ),
    ),  # T-M09-16; text i lloc revisats per DISSENY (#494)
    ("administration:grants_calendar", _("Calendari d'ajuts"), ()),  # T-M09A-05; lloc: DISSENY
    (
        "administration:treasury_accounts",
        _("Tresoreria: comptes i saldos"),
        (
            "administration:treasury_transfer",
            "administration:treasury_cash_count",
            "administration:treasury_settlements",
            "administration:treasury_settlement_confirm",
        ),
    ),
    (
        "administration:treasury_movements",
        _("Tresoreria: moviments"),
        ("administration:treasury_export", "administration:treasury_reverse"),
    ),
    (
        "administration:treasury_reconciliation",
        _("Tresoreria: conciliació"),
        (
            "administration:treasury_confirm_line",
            "administration:treasury_undo_reconciliation",
            "administration:treasury_review",
            "administration:treasury_exclude_line",
            "administration:treasury_match_line",
            "administration:treasury_match_movements",
            "administration:treasury_confirm_settlement_line",
            "administration:treasury_undo_exclusion",
            "administration:treasury_settlement_review_close",
        ),
    ),  # T-DX-44
    (
        "administration:payments_list",
        _("Pagaments: llistat"),
        ("administration:payments_review_close", "administration:payments_charge_review_close"),
    ),  # T-DX-47
    (
        "administration:payments_remittances",
        _("Pagaments: remeses"),
        (
            "administration:payments_remittance",
            "administration:payments_remittance_file",
            "administration:payments_remittance_notices",
            "administration:payments_remittance_sent",
            "administration:payments_remittance_settle",
            # Els retornats s'obren des de les remeses (V19).
            "administration:payments_returns",
            "administration:payments_returns_file",
            "administration:payments_returns_file_confirm",
            "administration:payments_return_decision",
        ),
    ),  # T-DX-47
    (
        "administration:payments_mandates",
        _("Pagaments: mètodes i mandats"),
        ("administration:payments_mandate_revoke",),
    ),  # T-DX-43
    ("administration:payments_campaign", _("Pagaments: campanya de mandats"), ()),  # T-DX-46
    (
        "administration:bank_statement",
        _("Tresoreria: extracte bancari"),
        ("administration:bank_statement_confirm", "administration:bank_statement_undo"),
    ),
    ("administration:cluber_preview", _("Importació de Cluber: prova"), ()),
    (
        "administration:guest_links",
        _("Enllaços de convidat"),
        ("administration:guest_link_send", "administration:guest_link_revoke"),
    ),
    (
        "administration:gdpr_requests",
        _("Sol·licituds RGPD"),
        (
            "administration:gdpr_request_detail",
            "administration:gdpr_in_person",
            "administration:gdpr_notes_export",
        ),
    ),
    (
        "administration:locked_data",
        _("Dades bloquejades"),
        ("administration:locked_data_detail",),
    ),
    (
        "administration:accounts",
        _("Comptes d'administrador"),
        (
            "administration:reset_credentials",
            "administration:account_roles",  # T-DX-55
            "administration:account_deactivate",  # T-RP-02d
        ),
    ),
    ("administration:permission_matrix", _("Rols i permisos"), ()),  # T-RP-03
    ("administration:audit_log", _("Registre d'activitat"), ()),
    (
        "administration:settings",
        _("Ajustos"),
        (
            "administration:settings_section",
            "administration:setting_detail",
            "administration:legal_texts",  # s'obren des dels ajustos
            "administration:legal_text_detail",
        ),
    ),
    (
        "administration:previews:index",
        _("Pantalles en construcció"),
        tuple(f"administration:previews:{name}" for name, _module in discover()),
    ),  # T-DX-50
)

# T-DX-62 (sistema de disseny §6.1): el menú en 6 grups plegables (B15 i B16), en l'ordre de
# ENTRIES; «Inici» queda solt a dalt. Un grup sense cap entrada visible no surt.
GROUPS = (
    (
        _("Socis"),
        "users",
        (
            "administration:members_list",
            "administration:join_requests",
            "administration:join_in_person",
            "administration:member_requests",
            "administration:licence_bulk_confirm",
            "administration:licences",
            "administration:licences_prices",
            "administration:membership_types",
        ),
    ),
    (
        _("Activitats"),
        "calendar-days",
        (
            "administration:activities",
            "administration:attendance_sessions",
            "administration:filings",
            "administration:places",
            "administration:catalogue",
            "administration:equipment_reports",  # 03: DISSENY
        ),
    ),
    (
        _("Quotes i tresoreria"),
        "coins",
        (
            "administration:fees",
            "administration:treasury_accounts",
            "administration:treasury_movements",
            "administration:treasury_reconciliation",
            "administration:expense_new",
            "administration:expenses_without_invoice",
            "administration:margin_periods",
            "administration:grants_calendar",
        ),
    ),
    (
        _("Pagaments"),
        "credit-card",
        (
            "administration:payments_list",
            "administration:payments_remittances",
            "administration:payments_mandates",
            "administration:payments_campaign",
        ),
    ),
    (
        _("Importacions"),
        "upload",
        ("administration:bank_statement", "administration:cluber_preview"),
    ),
    (
        _("Seguretat i RGPD"),
        "shield-check",
        (
            "administration:guest_links",
            "administration:gdpr_requests",
            "administration:locked_data",
            "administration:accounts",
            "administration:permission_matrix",
            "administration:audit_log",
        ),
    ),
    (
        _("Ajustos"),
        "settings",
        (
            "administration:settings",
            "administration:equipment_usage_rates",  # T-M03-22; lloc per revisar amb DISSENY
            "administration:previews:index",
        ),
    ),
)

_REQUEST_CACHE_ATTR = "_cris_admin_nav"


@dataclass(frozen=True)
class Entry:
    name: str
    url: str
    label: str
    current: bool


@dataclass(frozen=True)
class Group:
    label: str
    icon: str
    entries: tuple[Entry, ...]

    @property
    def current(self) -> bool:
        """El grup de la pantalla actual surt obert."""
        return any(entry.current for entry in self.entries)


@dataclass(frozen=True)
class AdminNav:
    entries: tuple[Entry, ...]
    username: str
    totp_active: bool

    @property
    def sections(self):
        """Les entrades sense «Inici»: la llista de la pàgina d'inici de l'administració."""
        return self.entries[1:]

    @property
    def home(self) -> Entry:
        return self.entries[0]

    @property
    def groups(self) -> tuple[Group, ...]:
        """Els grups amb alguna entrada visible, en l'ordre del menú (T-DX-62)."""
        by_name = {entry.name: entry for entry in self.entries}
        groups = (
            Group(label, icon, tuple(by_name[n] for n in names if n in by_name))
            for label, icon, names in GROUPS
        )
        return tuple(group for group in groups if group.entries)


def route_needs(name):
    """Grups de permisos de la ruta `name`: n'hi ha prou amb un grup sencer."""
    return BASE_ROUTES[name] if name in BASE_ROUTES else (ROUTES[name]["GET"],)


def need_met(account, need, permissions=None) -> bool:
    """Un permís d'un grup: `(codi, escriure)` o `(codi, escriure, abast)` si cal un abast
    concret (per exemple, «tot»)."""
    code, write, *scope = need
    if not has_perm(account, code, write=write, permissions=permissions):
        return False
    return not scope or scope_for(account, code, permissions=permissions) == scope[0]


def _allowed(account, name, permissions) -> bool:
    return any(
        all(need_met(account, need, permissions) for need in group) for group in route_needs(name)
    )


def _build(request) -> AdminNav | None:
    if not hasattr(request, "session") or not session_area_is_valid(request, AREA_ADMIN):
        return None
    account = request.user
    permissions = request_permissions(request)
    current = getattr(request.resolver_match, "view_name", None)
    entries = tuple(
        Entry(name, reverse(name), label, current == name or current in children)
        for name, label, children in ENTRIES
        if _allowed(account, name, permissions)
    )
    return AdminNav(entries, account.get_username(), account.has_totp)


def admin_nav_for(request) -> AdminNav | None:
    if not hasattr(request, _REQUEST_CACHE_ATTR):
        setattr(request, _REQUEST_CACHE_ATTR, _build(request))
    return getattr(request, _REQUEST_CACHE_ATTR)


def admin_navigation(request):
    """Processador de context: `admin_nav` és `None` fora d'una sessió d'administració."""
    return {"admin_nav": SimpleLazyObject(lambda: admin_nav_for(request))}
