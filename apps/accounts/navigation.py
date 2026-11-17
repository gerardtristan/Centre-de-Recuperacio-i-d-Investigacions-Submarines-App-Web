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
from apps.core.permission_catalog import CATALOG
from apps.core.permissions import has_perm, request_permissions
from apps.members.permissions import READ, ROUTES

from .security import AREA_ADMIN
from .sessions import session_area_is_valid

# Rutes de la 00 que surten al menú. Com a `ROUTES`, cada grup són els permisos que calen tots
# alhora; aquí n'hi pot haver més d'un, i n'hi ha prou amb un grup (el registre d'activitat es
# veu sencer amb M6 o només la part de socis amb P20). És el que comprova cada vista.
BASE_ROUTES = {
    "administration:home": ((),),
    "administration:accounts": ((("core.accounts.reset_credentials", READ),),),
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
    "administration:payments_remittances": ((("payments.remittances", READ),),),  # B3
    "administration:payments_mandates": ((("payments.mandates.view", READ),),),  # A4 (T-M05a-14)
    "administration:payments_campaign": ((("payments.mandates.view", READ),),),  # A4 (T-M05a-13b)
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
        ),
    ),
    ("administration:join_requests", _("Altes pendents"), ()),
    ("administration:join_in_person", _("Alta presencial"), ()),
    (
        "administration:member_requests",
        _("Sol·licituds de socis"),
        ("administration:member_request_detail",),
    ),
    ("administration:licence_bulk_confirm", _("Llicències pendents de confirmar"), ()),
    ("administration:fees", _("Quotes i impagats"), ()),
    ("administration:treasury_accounts", _("Tresoreria: comptes i saldos"), ()),
    ("administration:treasury_movements", _("Tresoreria: moviments"), ()),
    ("administration:treasury_reconciliation", _("Tresoreria: conciliació"), ()),  # T-DX-44
    ("administration:bank_statement", _("Tresoreria: extracte bancari"), ()),
    ("administration:payments_list", _("Pagaments: llistat"), ()),  # T-DX-47
    ("administration:payments_remittances", _("Pagaments: remeses"), ()),  # T-DX-47
    ("administration:payments_mandates", _("Pagaments: mètodes i mandats"), ()),  # T-DX-43
    ("administration:payments_campaign", _("Pagaments: campanya de mandats"), ()),  # T-DX-46
    ("administration:cluber_preview", _("Importació de Cluber: prova"), ()),
    ("administration:guest_links", _("Enllaços de convidat"), ()),
    (
        "administration:gdpr_requests",
        _("Sol·licituds RGPD"),
        ("administration:gdpr_request_detail",),
    ),
    (
        "administration:locked_data",
        _("Dades bloquejades"),
        ("administration:locked_data_detail",),
    ),
    (
        "administration:accounts",
        _("Comptes d'administrador"),
        ("administration:reset_credentials",),
    ),
    ("administration:audit_log", _("Registre d'activitat"), ()),
    (
        "administration:settings",
        _("Ajustos"),
        ("administration:settings_section", "administration:setting_detail"),
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
class AdminNav:
    entries: tuple[Entry, ...]
    username: str
    totp_active: bool

    @property
    def sections(self):
        """Les entrades sense «Inici»: la llista de la pàgina d'inici de l'administració."""
        return self.entries[1:]


def route_needs(name):
    """Grups de permisos de la ruta `name`: n'hi ha prou amb un grup sencer."""
    return BASE_ROUTES[name] if name in BASE_ROUTES else (ROUTES[name]["GET"],)


def _allowed(account, name, permissions) -> bool:
    return any(
        all(has_perm(account, code, write=write, permissions=permissions) for code, write in group)
        for group in route_needs(name)
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
