"""Catàleg de permisos (decisió 059; planning.md, apèndix «Rols i permisos editables»).

El catàleg és codi, no dades: cada permís hi declara l'abast que admet, si és protegit, què
demana i la configuració inicial de la matriu. Les cel·les editables de la configuració
inicial es carreguen a `RolePermission` amb una migració de dades; les protegides no tenen
mai fila i les aplica el motor directament des d'aquí.

Cada mòdul hi afegeix els seus permisos quan es construeix (060). La columna `ref` és
l'identificador de la fila a la matriu del pla, per poder-la seguir des de les proves.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from django.utils.translation import gettext_lazy as _

from .models import Role

R = Role.Code

# Abasts, de més ampli a més estret dins de cada permís (RN-RP-02: en una unió guanya el
# primer de la llista `allowed_scopes`).
SCOPE_ALL = "all"
SCOPE_READ = "read"  # «Cons.»: només consultar
SCOPE_READ_MINIMAL = "read_minimal"  # «Cons. (dades mínimes)»
SCOPE_OWN_ACTIVITIES = "own_activities"  # activitats de què és responsable (02)
SCOPE_OWN_SESSIONS = "own_sessions"  # sessions on fa classe (02)

READ_ONLY_SCOPES = frozenset({SCOPE_READ, SCOPE_READ_MINIMAL})
KNOWN_SCOPES = frozenset(
    {SCOPE_ALL, SCOPE_READ, SCOPE_READ_MINIMAL, SCOPE_OWN_ACTIVITIES, SCOPE_OWN_SESSIONS}
)


@dataclass(frozen=True)
class Permission:
    code: str
    ref: str
    description: str
    allowed_scopes: tuple[str, ...] = (SCOPE_ALL,)
    kind: str = "action"  # "action" o "field" (camp sensible)
    requires: tuple[str, ...] = ()
    # Protegit: no surt a l'editor com a editable i no té files a la base de dades.
    protected: bool = False
    protected_by: str = ""
    # Configuració inicial: rol → abast.
    initial: Mapping[str, str] = field(default_factory=dict)
    # Per a l'avís del resum i el tancament de sessions quan s'amplia l'accés (RN-RP-07, 11).
    touches_money: bool = False
    touches_personal_data: bool = False

    @property
    def module(self) -> str:
        return self.code.split(".", 1)[0]


def _perm(*args, initial=None, **kwargs) -> Permission:
    return Permission(*args, initial=MappingProxyType(dict(initial or {})), **kwargs)


_ALL = SCOPE_ALL

PERMISSIONS: tuple[Permission, ...] = (
    # --- 00 Base comuna ---------------------------------------------------------------------
    # P-90 (resposta C, 16/11/2026): a producció, les pantalles «En construcció» només les veu
    # qui té aquest permís, que l'administrador assigna per rol. Comença sense cap rol.
    _perm(
        "core.under_construction.view",
        "DX1",
        _("Veure les pantalles en construcció (disseny i contingut d'exemple, sense dades reals)"),
    ),
    _perm(
        "core.people.manage",
        "M2",
        _("Crear i editar perfils d'altres persones i els seus comptes personals"),
        initial={R.SECRETARY: _ALL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "core.accounts.manage",
        "M3",
        _("Crear comptes d'administrador, assignar i retirar rols, desactivar comptes"),
        protected=True,
        protected_by="059, punt 4.13",
        initial={R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "core.permissions.edit",
        "M3b",
        _("Modificar els permisos dels rols (editor)"),
        protected=True,
        protected_by="059, punt 4.13",
        initial={R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "core.accounts.reset_credentials",
        "M4",
        _("Restablir la contrasenya o el TOTP d'un altre compte d'administrador"),
        protected=True,
        protected_by="059, punt 4.13; 018",
        initial={R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "core.guest_links.manage",
        "M5",
        _("Generar, reenviar i revocar enllaços de convidat"),
        initial={R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "core.audit.view",
        "M6",
        _("Consultar el registre d'activitat"),
        initial={R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "core.departments.manage",
        "M7",
        _("Mantenir la llista de departaments"),
        initial={R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "core.cluber_import.run",
        "M8",
        _("Importar les dades de Cluber i desfer-ho"),
        initial={R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "core.bank_statement.import",
        "M9",
        _("Importar l'extracte bancari i desfer-ho"),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    _perm(
        "core.gdpr.handle",
        "M11",
        _("Atendre sol·licituds RGPD d'altres persones"),
        initial={R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "core.legal_texts.publish",
        "M12",
        _("Publicar versions noves dels textos legals"),
        initial={R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "core.locked_data.view",
        "M13",
        _("Consultar dades bloquejades"),
        protected=True,
        protected_by="028",
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
        touches_money=True,
    ),
    # M14 (registrar un cobrament manual) queda bloquejat fins a P-12 i no surt a l'editor.
    # --- 01 Socis i carnet ------------------------------------------------------------------
    _perm(
        "members.create_in_person",
        "P2",
        _("Crear una alta presencial"),
        initial={R.SECRETARY: _ALL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "members.requests.view",
        "P3a",
        _("Consultar sol·licituds d'alta, de canvi de tipus i de baixa"),
        initial={
            R.SECRETARY: _ALL,
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
        },
        touches_personal_data=True,
    ),
    _perm(
        "members.requests.approve_join",
        "P3",
        _("Aprovar o rebutjar altes"),
        requires=("members.requests.view",),
        initial={
            R.SECRETARY: _ALL,
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
        },
        touches_personal_data=True,
    ),
    _perm(
        "members.list",
        "P4",
        _("Llistat i fitxa de socis"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ_MINIMAL),
        initial={R.SECRETARY: _ALL, R.TREASURER: SCOPE_READ_MINIMAL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "members.edit",
        "P5",
        _("Editar dades d'un soci (inclòs document i número)"),
        requires=("members.list",),  # RN-RP-21
        initial={R.SECRETARY: _ALL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "members.edit_join_date",
        "P6",
        _("Corregir la data d'alta"),
        requires=("members.list",),  # RN-RP-21
        initial={R.SECRETARY: _ALL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "members.requests.resolve_change",
        "P7",
        _("Resoldre canvis de tipus i baixes"),
        requires=("members.requests.view",),
        initial={
            R.SECRETARY: _ALL,
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
        },
        touches_personal_data=True,
        touches_money=True,
    ),
    _perm(
        "members.requests.cancel_supplement",
        "P7a",
        _("Anul·lar el suplement vençut d'un canvi de tipus"),
        # 075 (RN-M01-82): només aquest suplement i només vençut; P8 amb edició també ho pot fer.
        requires=("members.requests.view",),
        initial={R.SECRETARY: _ALL},
        touches_money=True,
    ),
    _perm(
        "members.fees.generate",
        "P8",
        _("Generar quotes anuals"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "members.fees.exempt",
        "P22",
        _("Eximir o anul·lar una quota, amb motiu"),
        # RN-M01-72 i RN-M01-94; decisió 085 (J-2): el Tresorer. La pantalla d'anul·lar una quota
        # demana el mateix permís (072, quarta instrucció, punt 4).
        requires=("members.fees.view",),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    _perm(
        "members.unpaid.mark",
        "P9",
        _("Marcar i desmarcar impagat"),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    _perm(
        "members.fees.view",
        "P10",
        _("Veure l'estat de quotes de tots els socis"),
        # És un permís de consulta: el «Cons.» de la secretaria equival a «Sí».
        initial={R.SECRETARY: _ALL, R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
        touches_personal_data=True,
    ),
    _perm(
        "members.export",
        "P11",
        _("Exportar el llistat de socis"),
        initial={R.SECRETARY: _ALL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "members.gdpr.handle",
        "P17",
        _("Atendre sol·licituds RGPD d'altres"),
        initial={R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "members.cluber_import.run",
        "P18",
        _("Importació de Cluber i desfer"),
        initial={R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "members.licence_record.manage",
        "P19",
        _("Registre mínim de llicència (còpia de lectura, 052)"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={
            R.SECRETARY: _ALL,
            R.COURSES_MANAGER: SCOPE_READ,
            R.TREASURER: SCOPE_READ,
            R.ADMINISTRATOR: _ALL,
        },
        touches_personal_data=True,
    ),
    _perm(
        "members.audit.view",
        "P20",
        _("Consultar el registre d'activitat dels socis"),
        initial={R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "members.card.revoke",
        "P21",
        _("Revocar el carnet d'un soci, amb motiu"),
        # 079 (A-21, RN-M01-92): acció nova, inicialment només de la secretaria.
        requires=("members.list",),
        initial={R.SECRETARY: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "members.field.birth_date",
        "C1",
        _("Camp: data de naixement"),
        kind="field",
        protected=True,
        protected_by="058",
        initial={R.SECRETARY: _ALL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "members.field.identity",
        "C2",
        _("Camps: document d'identitat, adreça i consentiments d'altres"),
        kind="field",
        initial={R.SECRETARY: _ALL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    # --- 04 Tresoreria ----------------------------------------------------------------------
    _perm(
        "treasury.view",
        "T1",
        _("Veure comptes, saldos i moviments"),
        # Matriu inicial de la 059: la Junta, [A validar] al M04-4, comença sense.
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "treasury.reconcile",
        "T4",
        _("Conciliar i desfer una conciliació"),
        # L'Administrador, [A validar] al M04-4, comença sense (P-112).
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    _perm(
        "treasury.reverse",
        "T5",
        _("Anul·lar un moviment amb motiu"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "treasury.transfer",
        "T6",
        _("Registrar un traspàs"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "treasury.cash_count",
        "T7",
        _("Registrar un arqueig"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    # --- 05a Alta del mètode de pagament i mandats -------------------------------------------
    _perm(
        "payments.mandates.view",
        "A4",
        _("Veure mètodes i mandats de tots els socis (IBAN emmascarat)"),
        # «Cons.» només ensenya «té mètode: sí/no». La Secretaria, [A validar] al M05a-4,
        # comença sense (P-193).
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "payments.campaign.send",
        "A5",
        _("Enviar la campanya i els recordatoris"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "payments.mandates.revoke",
        "A6",
        _("Revocar un mandat a petició escrita del soci, amb motiu"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    # --- Ajustos (055; RN-RP-17, 19 i 22) -----------------------------------------------------
    # Cada apartat té `settings.section.<apartat>`: «Cons.» veu i «Sí» veu i edita tots els
    # valors. `settings.edit.<clau>` dona l'edició d'un sol valor i demana l'apartat (RN-RP-03).
    # Pagaments (05b, VC-17): «Cons.» per als rols que avui hi poden editar algun valor
    # (VC-16 és del tresorer; arriba amb les remeses); els tres valors, només l'administrador.
    _perm(
        "settings.section.payments",
        "AJ5b",
        _("Ajustos de pagaments"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.TREASURER: SCOPE_READ, R.ADMINISTRATOR: SCOPE_READ},
    ),
    _perm(
        "settings.edit.payments.bizum_ui_timeout_minutes",
        "AJ5b-1",
        _("Minuts que la pantalla espera la confirmació d'un Bizum"),
        requires=("settings.section.payments",),
        initial={R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "settings.edit.payments.safety_net_age_minutes",
        "AJ5b-2",
        _("Minuts sense notificació abans de preguntar l'estat d'un pagament al proveïdor"),
        requires=("settings.section.payments",),
        initial={R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "settings.edit.payments.safety_net_give_up_hours",
        "AJ5b-3",
        _("Hores que la xarxa de seguretat torna a provar una ordre abans de deixar-la a revisar"),
        requires=("settings.section.payments",),
        initial={R.ADMINISTRATOR: _ALL},
    ),
)

CATALOG: Mapping[str, Permission] = MappingProxyType({p.code: p for p in PERMISSIONS})

# Regla protegida 13 de la 059: gestionar usuaris, rols i permisos és exclusiu del rol
# administrador. Cap fila de la base de dades no ho pot donar a cap altre rol.
ADMINISTRATOR_ONLY = frozenset(
    {"core.accounts.manage", "core.permissions.edit", "core.accounts.reset_credentials"}
)


def editable_initial_cells() -> list[tuple[str, str, str]]:
    """Cel·les de la configuració inicial que van a `RolePermission` (rol, permís, abast)."""
    return sorted(
        (str(role), perm.code, scope)
        for perm in PERMISSIONS
        if not perm.protected
        for role, scope in perm.initial.items()
    )
