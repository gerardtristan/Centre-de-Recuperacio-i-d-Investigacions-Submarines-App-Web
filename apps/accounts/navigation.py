"""Navegació comuna de l'administració (T-M01-46; sistema de disseny §6.1 i §6.2).

El menú es construeix al servidor amb els permisos del compte: una entrada només hi surt si el
compte té el permís que la ruta declara (`apps/members/permissions.py` per a les rutes del 01,
`apps/activities/permissions.py` per a les del 02 i `BASE_ROUTES` per a les de la 00). No és cap
control: cada vista torna a comprovar el permís. Només ajuda a no ensenyar enllaços que
respondrien «no trobat».

- Sense una sessió vàlida de l'administració no hi ha menú i no es fa cap consulta.
- Es calcula com a màxim una vegada per petició, i només si la plantilla el fa servir (un
  fragment d'HTMX no el demana). Els permisos són els de `request_permissions`, els mateixos
  que ja ha calculat la vista.
"""

from dataclasses import dataclass

from django.urls import reverse
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy as _

from apps.activities.permissions import ROUTES as ACTIVITY_ROUTES
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
    ("administration:cluber_preview", _("Importació de Cluber: prova"), ()),
    (
        "administration:activities",
        _("Activitats"),
        (
            "administration:activity_detail",
            "administration:activity_course_add",
            "administration:activity_outing_add",
            "administration:activity_edit",
            "administration:activity_reopen",
            "administration:activity_cancel",
            "administration:activity_duplicate",
            "administration:activity_programme",
            "administration:session_add",
            "administration:session_edit",
            "administration:session_cancel",
        ),
    ),
    (
        "administration:catalogue_courses",
        _("Catàleg de cursos"),
        ("administration:catalogue_course_add",),
    ),
    (
        "administration:catalogue_specialities",
        _("Catàleg d'especialitats"),
        ("administration:catalogue_speciality_add",),
    ),
    ("administration:certification_levels", _("Nivells de titulació"), ()),
    ("administration:outing_types", _("Tipus de sortida"), ()),
    ("administration:projects", _("Projectes de medi ambient"), ()),
    (
        "administration:environment",
        _("Resultats ambientals"),
        ("administration:project_detail", "administration:activity_results"),
    ),
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
    if name in BASE_ROUTES:
        return BASE_ROUTES[name]
    return ((ROUTES.get(name) or ACTIVITY_ROUTES[name])["GET"],)


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
