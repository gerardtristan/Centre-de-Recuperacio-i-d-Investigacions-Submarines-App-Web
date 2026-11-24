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
SCOPE_OWN_APPLICATIONS = "own_applications"  # sol·licituds d'ajut de què és responsable (09)

READ_ONLY_SCOPES = frozenset({SCOPE_READ, SCOPE_READ_MINIMAL})
KNOWN_SCOPES = frozenset(
    {
        SCOPE_ALL,
        SCOPE_READ,
        SCOPE_READ_MINIMAL,
        SCOPE_OWN_ACTIVITIES,
        SCOPE_OWN_SESSIONS,
        SCOPE_OWN_APPLICATIONS,
    }
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
# 059, addenda del M02: el tresorer i el President gestionen activitats completes, com el
# responsable de cursos i sortides i l'administrador.
_ACTIVITY_MANAGERS = (R.COURSES_MANAGER, R.TREASURER, R.ADMINISTRATOR, R.PRESIDENT)
_WP1 = (R.ADMINISTRATOR, R.PRESIDENT)  # M07-4: qui té WP1 d'inici
# La fila «Gestionar inventari i assignar material» de la matriu del 03 (059).
_EQUIPMENT_STAFF = (
    R.COURSES_MANAGER,
    R.EQUIPMENT_MANAGER,
    R.TREASURER,
    R.ADMINISTRATOR,
    R.PRESIDENT,
)

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
    # 085, A-2 (T-M01-22c): els drets d'un menor de 14 anys es demanen en persona i la
    # secretaria ho registra. Només registrar-la: atendre-la continua sent M11 (P-417).
    _perm(
        "core.gdpr.register_in_person",
        "M11b",
        _("Registrar la sol·licitud d'esborrat feta en persona per un menor de 14 anys"),
        initial={R.SECRETARY: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "core.legal_texts.publish",
        "M12",
        _("Publicar versions noves dels textos legals"),
        # «Cons.» veu i revisa els textos; publicar demana «Sí» (T-M00-08b).
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
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
    _perm(
        "core.charges.record_manual",
        "M14",
        _("Registrar un cobrament manual (efectiu o presencial), amb motiu"),
        # P-12 (072, Q-037): qui pot veure i editar la tresoreria. Comença només amb el Tresorer,
        # com la conciliació (T4), que també dona càrrecs per pagats (P-331).
        requires=("treasury.view",),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
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
    # T-M01-49c (072, tercera instrucció, punt 2): «la secretaria, amb permís propi». Matriu
    # inicial: només la Secretaria (P-413).
    _perm(
        "members.fees.edit_instalments",
        "P23",
        _("Editar l'import i el venciment dels terminis d'una quota, amb motiu"),
        requires=("members.fees.view",),
        initial={R.SECRETARY: _ALL},
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
        "treasury.accounts.manage",
        "T2",
        _("Crear i desactivar comptes"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "treasury.cost_centres.manage",
        "T3",
        _("Mantenir departaments i centres de cost"),
        # El Tresorer, [A validar] al M04-4, comença sense (S-M04-09).
        initial={R.ADMINISTRATOR: _ALL},
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
    # P-190 (095): T8 i T10 tenen cadascun el seu codi. Les cel·les, a `payments/0023`.
    _perm(
        "treasury.exclude",
        "T8",
        _("Excloure una línia de l'extracte, amb motiu"),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    _perm(
        "treasury.export",
        "T9",
        _("Exportar moviments en CSV"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "treasury.review",
        "T10",
        _("Llista «a revisar»: veure-la i tancar-hi liquidacions amb nota"),
        # «Cons.» la veu; tancar una liquidació «a revisar» demana «Sí» (T-M04-14c, P-390).
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    # T11 fa servir P10 (P-243).
    # --- 05a Alta del mètode de pagament i mandats -------------------------------------------
    _perm(
        "payments.mandates.view",
        "A4",
        _("Veure mètodes i mandats de tots els socis (IBAN emmascarat)"),
        # «Cons.» només ensenya «té mètode: sí/no»: la Secretaria (P-193, 095).
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL, R.SECRETARY: SCOPE_READ},
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
    # A7, A8 i B8 són configuració de l'entorn (variables i claus), no accions de l'app; A9 no
    # el té ningú i cap pantalla no ensenya l'IBAN (044).
    # --- 05b Cobraments ------------------------------------------------------------------------
    _perm(
        "payments.remittances",
        "B3",
        _("Generar remeses, descarregar el fitxer i marcar-lo enviat"),
        protected=True,
        protected_by="044",  # el fitxer porta els IBAN
        initial={R.TREASURER: _ALL},
        touches_money=True,
        touches_personal_data=True,
    ),
    _perm(
        "payments.returns",
        "B4",
        _("Registrar retornats i decidir el reintent"),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    _perm(
        "payments.refund",
        "B5",
        _("Fer devolucions"),
        # L'Administrador, [A validar] al M05b-4, comença sense (D-10).
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    _perm(
        "payments.view",
        "B6",
        _("Veure tots els pagaments, en curs, fallits i «a revisar»"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
        touches_personal_data=True,
    ),
    _perm(
        "payments.resend",
        "B7",
        _("Reenviar l'alternativa de pagament o l'enllaç de convidat"),
        # La Secretaria, «Sí (quotes)» a la matriu, comença sense: cap abast no limita a les
        # quotes (P-244).
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    # --- 06 Llicències (M06-4 i la matriu inicial de la 059; T-M06-16, T-M06-25) ----------------
    # LC1, LC2 i el «Propi» de LC3 són accions pròpies o públiques, fora de la matriu. LC9
    # (activar l'opció de no socis) és l'ajust `licences.non_members_enabled`: és a «Ajustos».
    _perm(
        "licences.declare_existing",
        "LC3",
        _("«Ja en tinc una»: registrar la llicència d'una altra persona"),
        initial={
            R.SECRETARY: _ALL,
            R.COURSES_MANAGER: _ALL,
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
        },
        touches_personal_data=True,
    ),
    _perm(
        "licences.list",
        "LC4",
        _("Llistat de llicències, filtres i venciments"),
        initial={
            R.SECRETARY: _ALL,
            R.COURSES_MANAGER: _ALL,
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
        },
        touches_personal_data=True,
    ),
    _perm(
        "licences.file",
        "LC5",
        _("Exportar per a la federació; marcar tramitada i vigent"),
        requires=("licences.list",),
        initial={R.SECRETARY: _ALL, R.ADMINISTRATOR: _ALL, R.PRESIDENT: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "licences.cancel",
        "LC6",
        _("Cancel·lar una llicència"),
        requires=("licences.list",),
        initial={R.SECRETARY: _ALL, R.ADMINISTRATOR: _ALL, R.PRESIDENT: _ALL},
        touches_money=True,
    ),
    _perm(
        "licences.refund",
        "LC7",
        _("Fer la devolució d'una llicència cancel·lada"),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    _perm(
        "licences.prices",
        "LC8",
        _("Tipus, preus i recàrrec de les llicències"),
        # «Cons.» els veu; canviar-los demana «Sí» (la Junta, Cons.).
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
            R.BOARD: SCOPE_READ,
        },
        touches_money=True,
    ),
    _perm(
        "licences.participant_status",
        "LC10",
        _("Veure si la llicència d'un participant és vigent"),
        # L'instructor només en veu «vigent sí o no» per a la data de la sessió (RN-M06-22).
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_ACTIVITIES, SCOPE_OWN_SESSIONS),
        initial={
            R.INSTRUCTOR: SCOPE_OWN_SESSIONS,
            R.SECRETARY: _ALL,
            R.COURSES_MANAGER: SCOPE_OWN_ACTIVITIES,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
        },
    ),
    _perm(
        "licences.import_m01",
        "LC11",
        _("Passar els registres de llicència del 01 al 06"),
        initial={R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "licences.field.details",
        "C6",
        _("Camps: número federatiu, categoria i venciment"),
        kind="field",
        requires=("licences.list",),
        initial={
            R.SECRETARY: _ALL,
            R.COURSES_MANAGER: _ALL,
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
        },
        touches_personal_data=True,
    ),
    # --- 09 Marge, despeses i facturació (M09-4 i la matriu inicial de la 059; T-M09-30) -------
    # MG10 (les seves factures) és una acció pròpia, fora de la matriu.
    _perm(
        "expenses.record",
        "MG1",
        _("Registrar una despesa amb factura"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_ACTIVITIES),
        initial={
            R.COURSES_MANAGER: SCOPE_OWN_ACTIVITIES,
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
        },
        touches_money=True,
    ),
    _perm(
        "expenses.pay",
        "MG2",
        _("Pagar una despesa, adjuntar-ne el comprovant i anul·lar-la"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "expenses.allocate",
        "MG3",
        _("Repartir una despesa entre activitats"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "expenses.other_income",
        "MG4",
        _("Registrar ajuts, patrocinis i donatius"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "expenses.planned_costs",
        "MG5",
        _("Costos previstos d'una activitat"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_ACTIVITIES),
        initial={
            R.COURSES_MANAGER: SCOPE_OWN_ACTIVITIES,
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
        },
        touches_money=True,
    ),
    _perm(
        "expenses.margin.view",
        "MG6",
        _("Veure el marge d'una activitat"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_ACTIVITIES, SCOPE_READ),
        initial={
            R.COURSES_MANAGER: SCOPE_OWN_ACTIVITIES,
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
            R.BOARD: SCOPE_READ,
        },
        touches_money=True,
    ),
    _perm(
        "expenses.margin.close_activity",
        "MG7",
        _("Tancar econòmicament una activitat"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "expenses.reports",
        "MG8",
        _("Informes per departament, subtipus i projecte"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL, R.BOARD: SCOPE_READ},
        touches_money=True,
    ),
    _perm(
        "expenses.invoices.issue",
        "MG9",
        _("Emetre factures i rectificatives"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
        touches_personal_data=True,
    ),
    _perm(
        "expenses.periods.close",
        "MG11",
        _("Tancar un període"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "expenses.periods.reopen",
        "MG12",
        _("Reobrir un període"),
        protected=True,
        protected_by="059 (matriu del 09); RN-M09-16",
        initial={R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "expenses.volunteering",
        "MG13",
        _("Hores de voluntariat"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "expenses.catalogues",
        "MG14",
        _("Categories, proveïdors i llindar de marge baix"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    # Documents de justificació (factures de despesa i comprovants): només el tresorer i la
    # junta, mai l'administrador (051, RN-M09-23).
    _perm(
        "expenses.documents.open",
        "C5",
        _("Obrir els documents de justificació (factures de despesa i comprovants)"),
        protected=True,
        protected_by="051",
        initial={R.TREASURER: _ALL, R.BOARD: _ALL},
        touches_money=True,
        touches_personal_data=True,
    ),
    # --- 09 Ajuts (M09-ajuts-4 i la matriu inicial de la 059; T-M09-30) ------------------------
    # Només el tresorer, la junta i l'administrador. La junta, «les que en sigui responsable» a
    # AJ4, AJ5 i AJ13 (S-M09A-01): la comprovació per objecte la registra l'apartat d'ajuts.
    _perm(
        "grants.view",
        "AJ3",
        _("Veure el calendari, les convocatòries i les sol·licituds d'ajut"),
        initial={R.TREASURER: _ALL, R.BOARD: _ALL, R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "grants.calls.manage",
        "AJ1",
        _("Crear, editar i copiar convocatòries d'ajut"),
        requires=("grants.view",),
        initial={R.TREASURER: _ALL, R.BOARD: _ALL, R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "grants.eligibility",
        "AJ2",
        _("Revisar l'elegibilitat d'una convocatòria"),
        requires=("grants.view",),
        initial={R.TREASURER: _ALL, R.BOARD: _ALL, R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "grants.applications.prepare",
        "AJ4",
        _("Crear una sol·licitud d'ajut i moure-la fins a «presentada»"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_APPLICATIONS),
        requires=("grants.view",),
        initial={R.TREASURER: _ALL, R.BOARD: SCOPE_OWN_APPLICATIONS, R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "grants.applications.resolve",
        "AJ5",
        _("Marcar una sol·licitud concedida o denegada i escriure les observacions"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_APPLICATIONS),
        requires=("grants.view",),
        initial={R.TREASURER: _ALL, R.BOARD: SCOPE_OWN_APPLICATIONS, R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "grants.applications.amendments",
        "AJ13",
        _("Requeriments d'esmena i pròrroga de la justificació"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_APPLICATIONS),
        requires=("grants.view",),
        initial={R.TREASURER: _ALL, R.BOARD: SCOPE_OWN_APPLICATIONS, R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "grants.income",
        "AJ6",
        _("Registrar l'ingrés d'un ajut"),
        requires=("grants.view", "expenses.other_income"),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "grants.justification",
        "AJ7",
        _("Lligar despeses a un ajut i generar el paquet de justificació"),
        # L'administrador lliga despeses però no obre els documents (AJ12, 051).
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        requires=("grants.view",),
        initial={R.TREASURER: _ALL, R.BOARD: SCOPE_READ, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "grants.applications.close",
        "AJ8",
        _("Marcar una sol·licitud justificada o tancada"),
        requires=("grants.view",),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "grants.applications.undo",
        "AJ9",
        _("Desfer l'últim canvi d'estat d'una sol·licitud, amb motiu"),
        requires=("grants.view",),
        initial={R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "grants.alert_days",
        "AJ10",
        _("Configurar els dies dels avisos dels ajuts"),
        requires=("grants.view",),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "grants.audit.view",
        "AJ11",
        _("Consultar el registre d'activitat dels ajuts"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        requires=("grants.view",),
        initial={R.TREASURER: SCOPE_READ, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "grants.documents.open",
        "AJ12",
        _("Obrir i descarregar els documents de justificació i el paquet d'un ajut"),
        protected=True,
        protected_by="051",
        initial={R.TREASURER: _ALL, R.BOARD: _ALL},
        touches_money=True,
        touches_personal_data=True,
    ),
    # --- Ajustos (055; RN-RP-17, 19 i 22) -----------------------------------------------------
    # Cada apartat té `settings.section.<apartat>`: «Cons.» veu i «Sí» veu i edita tots els
    # valors. `settings.edit.<clau>` dona l'edició d'un sol valor i demana l'apartat (RN-RP-03).
    # Socis (01; T-M01-32): «Cons.» per als rols que hi poden editar algun valor. Qui edita
    # cada valor és la columna «Qui el canvia» de l'addenda de la 055 i de l'ampliació de la 091.
    _perm(
        "settings.section.members",
        "AJ01",
        _("Ajustos de socis"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.TREASURER: SCOPE_READ, R.ADMINISTRATOR: SCOPE_READ, R.SECRETARY: SCOPE_READ},
    ),
    # VC-01: un sol permís per al preu de tots els tipus, també els creats des de l'app
    # (T-M01-52; `members.annual_fee_cents.<codi>`, família registrada pel 01).
    _perm(
        "settings.edit.members.annual_fee_cents",
        "AJ01-1",
        _("Quota anual de cada tipus de soci"),
        requires=("settings.section.members",),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    # T-M01-52 (091, RN-M01-107): crear, editar i desactivar tipus [A validar: P-376].
    _perm(
        "settings.edit.members.membership_types",
        "AJ01-2",
        _("Tipus de soci: crear-los, editar-los i desactivar-los"),
        requires=("settings.section.members",),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "settings.edit.members.fee_reminder_offsets",
        "AJ01-3",
        _("Dies dels recordatoris de quota respecte del venciment"),
        requires=("settings.section.members",),
        initial={R.TREASURER: _ALL},
    ),
    _perm(
        "settings.edit.members.type_change_supplement_due_days",
        "AJ01-4",
        _("Dies per pagar el suplement del canvi a ple dret"),
        requires=("settings.section.members",),
        initial={R.TREASURER: _ALL},
    ),
    _perm(
        "settings.edit.members.card_back_text",
        "AJ01-5",
        _("Text del darrere del carnet"),
        requires=("settings.section.members",),
        initial={R.SECRETARY: _ALL, R.ADMINISTRATOR: _ALL},
    ),
    # VC-04: «per decisió de la junta», l'edita l'administrador.
    _perm(
        "settings.edit.members.classic_member_years",
        "AJ01-6",
        _("Anys d'antiguitat per a la insígnia de soci clàssic (0, sense insígnia)"),
        requires=("settings.section.members",),
        initial={R.ADMINISTRATOR: _ALL},
    ),
    # T-M01-43e (P-399): mesos de l'avís de renovació, com els dies dels recordatoris amb què
    # es comprova (P-360): el Tresorer.
    _perm(
        "settings.edit.members.renewal_notice_months",
        "AJ01-8",
        _("Mesos d'antelació de l'avís de renovació"),
        requires=("settings.section.members",),
        initial={R.TREASURER: _ALL},
    ),
    # T-M01-49 (097, P-61): els quatre ajustos del pagament a terminis (`members.instalments.*`,
    # família registrada pel 01). Matriu inicial com el preu de la quota (P-396).
    _perm(
        "settings.edit.members.instalments",
        "AJ01-7",
        _("Pagament a terminis de la quota de ple dret"),
        requires=("settings.section.members",),
        initial={R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    # Textos dels correus i de l'ajuda de les pantalles (T-M00-08 i 08e; 097,
    # planning.md#M00-textos-editables): una àrea per apartat, cadascuna amb «Cons.» (veure) i
    # «Sí» (veure i editar). Matriu inicial: l'administrador edita totes les àrees i la
    # Secretaria, la de socis (P-380). Una àrea nova és un permís més.
    _perm(
        "settings.section.texts-members",
        "AJ00-T1",
        _("Textos dels correus i de l'ajuda: socis"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.SECRETARY: _ALL, R.ADMINISTRATOR: _ALL},
    ),
    # Pagaments (05b): «Cons.» per als rols que hi poden editar algun valor. VC-17, només
    # l'administrador; VC-11 i VC-16, només el tresorer.
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
    # VC-16 (T-M05b-09 i 12): l'edita el Tresorer (apèndix de valors configurables).
    _perm(
        "settings.edit.payments.prenotification_days",
        "AJ5b-4",
        _("Dies de l'avís previ d'una remesa"),
        requires=("settings.section.payments",),
        initial={R.TREASURER: _ALL},
    ),
    # VC-16 (T-M05b-22c; RN-M05b-09): dies del recordatori d'una transferència que no arriba.
    _perm(
        "settings.edit.payments.transfer_reminder_days",
        "AJ5b-12",
        _("Dies que s'espera una transferència abans del recordatori"),
        requires=("settings.section.payments",),
        initial={R.TREASURER: _ALL},
    ),
    _perm(
        "settings.edit.payments.max_direct_debit_attempts",
        "AJ5b-5",
        _("Màxim d'intents de domiciliació per càrrec"),
        requires=("settings.section.payments",),
        initial={R.TREASURER: _ALL},
    ),
    # VC-11 (T-M05a-22): l'edita el Tresorer (apèndix de valors configurables).
    _perm(
        "settings.edit.payments.mandate_campaign_reminder_days",
        "AJ5b-6",
        _("Dies dels recordatoris de la campanya de mandats"),
        requires=("settings.section.payments",),
        initial={R.TREASURER: _ALL},
    ),
    # T-M05b-15a: quants dies després del venciment es cobra una quota amb la targeta guardada.
    _perm(
        "settings.edit.payments.saved_card_charge_window_days",
        "AJ5b-7",
        _("Dies després del venciment en què es cobra una quota amb la targeta guardada"),
        requires=("settings.section.payments",),
        initial={R.TREASURER: _ALL},
    ),
    # P-291 (095): codis de retorn del banc i l'acció de cada un. Les cel·les, a `payments/0021`.
    _perm(
        "settings.edit.payments.return_codes_retry",
        "AJ5b-8",
        _("Codis de retorn que proposen un reintent"),
        requires=("settings.section.payments",),
        initial={R.TREASURER: _ALL},
    ),
    _perm(
        "settings.edit.payments.return_codes_block_mandate",
        "AJ5b-9",
        _("Codis de retorn que bloquegen el mandat"),
        requires=("settings.section.payments",),
        initial={R.TREASURER: _ALL},
    ),
    # P-123 (095): qui l'edita no és al pla; el Tresorer, com els codis del banc [P-386].
    _perm(
        "settings.edit.payments.mandate_countries",
        "AJ5b-10",
        _("Països de l'IBAN admesos al mandat"),
        requires=("settings.section.payments",),
        initial={R.TREASURER: _ALL},
    ),
    # P-131 (095; VC-14, A7): els mètodes actius del proveïdor. Només l'Administrador, amb un
    # codi TOTP nou i nota; avisa el tresorer. Les claus i els secrets, a les variables d'entorn.
    _perm(
        "settings.edit.payments.provider",
        "AJ5b-11",
        _("Mètodes actius del proveïdor"),
        requires=("settings.section.payments",),
        initial={R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    # Llicències (06; M06-6, «Valors configurables»; T-M06-20). «Cons.» per als rols que hi editen
    # algun valor. LC9 és activar l'opció de no socis: només l'Administrador, per decisió de la
    # junta (RN-M06-03).
    _perm(
        "settings.section.licences",
        "AJ06",
        _("Ajustos de llicències"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.SECRETARY: SCOPE_READ, R.TREASURER: SCOPE_READ, R.ADMINISTRATOR: SCOPE_READ},
    ),
    _perm(
        "settings.edit.licences.non_members_enabled",
        "LC9",
        _("Llicència per a persones que no són sòcies (opció de la junta)"),
        requires=("settings.section.licences",),
        initial={R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "settings.edit.licences.day_enabled",
        "AJ06-1",
        _("Llicència d'un dia"),
        requires=("settings.section.licences",),
        initial={R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "settings.edit.licences.reminder_days",
        "AJ06-2",
        _("Dies dels avisos de venciment de la llicència"),
        requires=("settings.section.licences",),
        initial={R.SECRETARY: _ALL},
    ),
    _perm(
        "settings.edit.licences.to_renew_days",
        "AJ06-3",
        _("Dies abans del venciment en què una llicència surt «per renovar»"),
        requires=("settings.section.licences",),
        initial={R.SECRETARY: _ALL},
    ),
    _perm(
        "settings.edit.licences.next_year_opens_on",
        "AJ06-4",
        _("Dia en què s'obre la llicència de l'any vinent"),
        requires=("settings.section.licences",),
        initial={R.SECRETARY: _ALL},
    ),
    # P-530 (T-M02-51a): el tipus de la primera llicència d'un alumne nou. Buit per defecte; el
    # trien la secretaria i el tresorer (és diners: el cost de la federació va al previst).
    _perm(
        "settings.edit.licences.first_licence_type",
        "AJ06-5",
        _("Tipus de la primera llicència d'un alumne nou (P-530)"),
        requires=("settings.section.licences",),
        initial={R.SECRETARY: _ALL, R.TREASURER: _ALL},
        touches_money=True,
    ),
    # --- 02 Activitats (cursos i sortides) --------------------------------------------------
    # T-M02-33 i T-M02-38: la matriu inicial de la 059 («02 Activitats»), cel·la per cel·la.
    # AC1 a AC4 són accions públiques o pròpies i no tenen permís de rol. CF1 i CF2
    # (conferències) són del mòdul 11 i es declararan amb ell. «Cons.» és l'abast de només consulta.
    _perm(
        "activities.enrol_in_person",
        "AC5",
        _("Inscriure presencialment una altra persona"),
        initial=dict.fromkeys(_ACTIVITY_MANAGERS, _ALL),
        touches_personal_data=True,
        touches_money=True,
    ),
    _perm(
        "activities.catalogue.manage",
        "AC6",
        _("Mantenir el catàleg de cursos i especialitats, tipus, subtipus, projectes i preus"),
        initial=dict.fromkeys(_ACTIVITY_MANAGERS, _ALL),
        touches_money=True,
    ),
    _perm(
        "activities.manage",
        "AC7",
        _("Crear, editar, publicar, cancel·lar i duplicar activitats"),
        initial=dict.fromkeys(_ACTIVITY_MANAGERS, _ALL),
        touches_money=True,
    ),
    _perm(
        "activities.participants.view",
        "AC8",
        _("Llista de participants amb requisits"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ, SCOPE_OWN_SESSIONS),
        initial={
            R.INSTRUCTOR: SCOPE_OWN_SESSIONS,
            R.EQUIPMENT_MANAGER: SCOPE_READ,  # la conserva per assignar material (D-06)
            **dict.fromkeys(_ACTIVITY_MANAGERS, _ALL),
        },
        touches_personal_data=True,
    ),
    _perm(
        "activities.attendance.record",
        "AC9",
        _("Passar llista i registrar incidències"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_SESSIONS),
        initial={
            R.INSTRUCTOR: SCOPE_OWN_SESSIONS,
            R.COURSES_MANAGER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
        },
        touches_personal_data=True,
    ),
    # AC10a, AC10b i AC12 només admeten «les seves sessions» (RN-RP-04): ho fa qui fa classe a la
    # sessió, tingui el rol que tingui.
    _perm(
        "activities.assessment.record",
        "AC10a",
        _("Avaluar pràctiques"),
        allowed_scopes=(SCOPE_OWN_SESSIONS,),
        initial={R.INSTRUCTOR: SCOPE_OWN_SESSIONS},
        touches_personal_data=True,
    ),
    _perm(
        "activities.reinforcement.propose",
        "AC10b",
        _("Proposar classes de reforç"),
        allowed_scopes=(SCOPE_OWN_SESSIONS,),
        initial={R.INSTRUCTOR: SCOPE_OWN_SESSIONS},
        touches_personal_data=True,
    ),
    _perm(
        "activities.reinforcement.decide",
        "AC11",
        _("Confirmar o rebutjar (programar) classes de reforç"),
        initial={R.COURSES_MANAGER: _ALL, R.ADMINISTRATOR: _ALL, R.PRESIDENT: _ALL},
        touches_money=True,
    ),
    _perm(
        "activities.outcome.record",
        "AC12",
        _("Registrar apte o no apte"),
        allowed_scopes=(SCOPE_OWN_SESSIONS,),
        initial={R.INSTRUCTOR: SCOPE_OWN_SESSIONS},
        touches_personal_data=True,
    ),
    _perm(
        "activities.certificate.issue",
        "AC13",
        _("Emetre el certificat"),
        initial={R.COURSES_MANAGER: _ALL, R.ADMINISTRATOR: _ALL, R.PRESIDENT: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "activities.environment.manage",
        "AC14",
        _("Resultats ambientals i fitxa de projecte"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={
            R.COURSES_MANAGER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
            R.BOARD: SCOPE_READ,
        },
    ),
    _perm(
        "activities.message.send",
        "AC15",
        _("Enviar un missatge als inscrits"),
        initial=dict.fromkeys(_ACTIVITY_MANAGERS, _ALL),
        touches_personal_data=True,
    ),
    _perm(
        "activities.waitlist.manage",
        "AC16",
        _("Gestionar la llista d'espera a mà"),
        initial=dict.fromkeys(_ACTIVITY_MANAGERS, _ALL),
        touches_personal_data=True,
    ),
    _perm(
        "activities.refund.propose",
        "AC17",
        _("Proposar una devolució per cancel·lació"),
        initial=dict.fromkeys(_ACTIVITY_MANAGERS, _ALL),
        touches_money=True,
    ),
    _perm(
        "activities.refund.execute",
        "AC18",
        # És la part del 02 de B5 (05b): fer o rebutjar una proposta de devolució. La devolució
        # mateixa la fa el 05b, que hi demanarà B5 quan existeixi (T-M05b-25).
        _("Fer la devolució d'una proposta, o rebutjar-la"),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    _perm(
        "activities.income.view",
        "AC19",
        _("Veure els imports cobrats d'una activitat"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        # S-M02-18: el responsable els consulta de totes les activitats.
        initial={R.COURSES_MANAGER: SCOPE_READ, R.TREASURER: _ALL, R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    _perm(
        "activities.reports.view",
        "AC20",
        _("Informes operatius"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ, SCOPE_OWN_SESSIONS),
        initial={
            R.INSTRUCTOR: SCOPE_OWN_SESSIONS,
            R.EQUIPMENT_MANAGER: SCOPE_READ,
            R.BOARD: SCOPE_READ,
            **dict.fromkeys(_ACTIVITY_MANAGERS, _ALL),
        },
        touches_personal_data=True,
    ),
    _perm(
        "activities.field.student_for_instructor",
        "C3",
        _(
            "Camps de l'alumne per a l'instructor: nom, titulació, llicència sí o no, "
            "assistència i avaluacions"
        ),
        kind="field",
        allowed_scopes=(SCOPE_OWN_SESSIONS,),
        protected=True,
        protected_by="059; S-M02-17",
        initial={R.INSTRUCTOR: SCOPE_OWN_SESSIONS},
        touches_personal_data=True,
    ),
    # T-M02-38 (addenda de llocs del 02): AC21 i AC22 són els dos nivells de RN-RP-22 per a
    # l'apartat «Llocs» dels ajustos del 02 (P-75); AC23 i C7, el cost de material previst.
    _perm(
        "activities.places.view",
        "AC21",
        _("Llocs: veure la llista, els preus estàndard i l'historial, el centre i les notes"),
        initial=dict.fromkeys(
            (R.COURSES_MANAGER, R.EQUIPMENT_MANAGER, R.TREASURER, R.ADMINISTRATOR, R.PRESIDENT),
            _ALL,
        ),
    ),
    _perm(
        "activities.places.manage",
        "AC22",
        _("Llocs i preus estàndard: veure i editar"),
        requires=("activities.places.view",),
        initial=dict.fromkeys(_ACTIVITY_MANAGERS, _ALL),
        touches_money=True,
    ),
    _perm(
        "activities.material_cost.edit",
        "AC23",
        _("Canviar el cost de material previst d'una activitat, amb nota"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_ACTIVITIES),
        initial={
            R.COURSES_MANAGER: SCOPE_OWN_ACTIVITIES,
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
        },
        touches_money=True,
    ),
    # Addenda de la 104 (T-M02-48): fotos de titulacions i tramitacions a la federació.
    # L'instructor no en té cap. AC26 com LC5.
    _perm(
        "activities.card_photos.view",
        "AC24",
        _("Fotos de titulacions: veure"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.SECRETARY: _ALL, R.BOARD: SCOPE_READ},
        touches_personal_data=True,
    ),
    _perm(
        "activities.card_photos.manage",
        "AC25",
        _("Fotos de titulacions i homologacions: veure i editar"),
        requires=("activities.card_photos.view",),  # RN-RP-03
        initial={R.SECRETARY: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "activities.filings.manage",
        "AC26",
        _("Tramitacions a la federació: llistes, exportar, marcar tramitada, feta o rebutjada"),
        initial={R.SECRETARY: _ALL, R.ADMINISTRATOR: _ALL, R.PRESIDENT: _ALL},
        touches_personal_data=True,
    ),
    # Addenda de la 104 (T-M02-50; RN-M02-57): «Inclou la primera llicència» a les versions de
    # preu del catàleg. Resposta provisional del propietari a P-426; falta el tresorer.
    _perm(
        "activities.first_licence.view",
        "AC27",
        _("Inclou la primera llicència: veure"),
        initial=dict.fromkeys(
            (R.SECRETARY, R.COURSES_MANAGER, R.TREASURER, R.ADMINISTRATOR, R.PRESIDENT), _ALL
        ),
        touches_money=True,
    ),
    _perm(
        "activities.first_licence.manage",
        "AC28",
        _("Inclou la primera llicència: veure i editar"),
        requires=("activities.first_licence.view",),  # RN-RP-03
        initial=dict.fromkeys(_ACTIVITY_MANAGERS, _ALL),
        touches_money=True,
    ),
    _perm(
        "activities.field.material_cost",
        "C7",
        _("Camp: cost de material previst d'una activitat"),
        kind="field",
        allowed_scopes=(SCOPE_ALL, SCOPE_READ, SCOPE_OWN_ACTIVITIES),
        initial={
            R.COURSES_MANAGER: SCOPE_OWN_ACTIVITIES,
            R.EQUIPMENT_MANAGER: _ALL,
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
            R.BOARD: SCOPE_READ,
        },
        touches_money=True,
    ),
    # --- 03 Material (M03-4 i la matriu inicial de la 059; T-M03-18) ---------------------------
    # MT1 i MT2 (el material propi del soci) són accions pròpies, fora de la matriu. «Les seves»
    # de l'instructor són les sessions on fa classe; les del responsable de cursos i sortides,
    # les activitats de què és responsable.
    _perm(
        "equipment.inventory.manage",
        "MT3",
        _("Mantenir tipus i inventari de material; donar de baixa una peça"),
        initial=dict.fromkeys(_EQUIPMENT_STAFF, _ALL),
    ),
    _perm(
        "equipment.stock.view",
        "MT4",
        _("Veure l'stock de material"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={
            R.INSTRUCTOR: SCOPE_READ,
            **dict.fromkeys(_EQUIPMENT_STAFF, _ALL),
            R.BOARD: SCOPE_READ,
        },
    ),
    _perm(
        "equipment.typical.manage",
        "MT5",
        _("Material típic dels cursos, les especialitats i els tipus de sortida"),
        initial=dict.fromkeys(_EQUIPMENT_STAFF, _ALL),
    ),
    _perm(
        "equipment.assignments.manage",
        "MT6",
        _("Assignar material, marcar-lo llogat, lliurar-lo i retornar-lo"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_SESSIONS),
        initial={R.INSTRUCTOR: SCOPE_OWN_SESSIONS, **dict.fromkeys(_EQUIPMENT_STAFF, _ALL)},
        touches_personal_data=True,
    ),
    _perm(
        "equipment.rentals.adhoc",
        "MT6b",
        _("Lloguer puntual a un centre: qui ha agafat què i cost del centre"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_SESSIONS),
        initial={R.INSTRUCTOR: SCOPE_OWN_SESSIONS, **dict.fromkeys(_EQUIPMENT_STAFF, _ALL)},
        touches_money=True,
        touches_personal_data=True,
    ),
    _perm(
        "equipment.participants.view",
        "MT7",
        _("Veure el material dels participants"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_SESSIONS),
        initial={R.INSTRUCTOR: SCOPE_OWN_SESSIONS, **dict.fromkeys(_EQUIPMENT_STAFF, _ALL)},
        touches_personal_data=True,
    ),
    _perm(
        "equipment.centres.manage",
        "MT8",
        _("Centres de busseig i tarifes (preu per a l'alumne)"),
        # «Cons.» els veu; canviar-los demana «Sí» (el responsable de cursos i sortides, Cons.).
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={
            R.COURSES_MANAGER: SCOPE_READ,
            R.EQUIPMENT_MANAGER: _ALL,
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
        },
        touches_money=True,
    ),
    _perm(
        "equipment.rental_lists.manage",
        "MT9",
        _("Llista de lloguer: generar-la, exportar-la i marcar-la enviada"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_SESSIONS),
        initial={R.INSTRUCTOR: SCOPE_OWN_SESSIONS, **dict.fromkeys(_EQUIPMENT_STAFF, _ALL)},
        touches_personal_data=True,
    ),
    _perm(
        "equipment.actual_quantities",
        "MT10",
        _("Quantitats reals de material després de l'activitat"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_SESSIONS),
        initial={R.INSTRUCTOR: SCOPE_OWN_SESSIONS, **dict.fromkeys(_EQUIPMENT_STAFF, _ALL)},
    ),
    _perm(
        "equipment.reviews.manage",
        "MT11",
        _("Revisions del material"),
        initial=dict.fromkeys(_EQUIPMENT_STAFF, _ALL),
    ),
    _perm(
        "equipment.costs.view",
        "MT12",
        _("Cost de material per participant i per activitat; marge dels lloguers"),
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_ACTIVITIES, SCOPE_READ),
        initial={
            R.COURSES_MANAGER: SCOPE_OWN_ACTIVITIES,
            R.EQUIPMENT_MANAGER: _ALL,
            R.TREASURER: _ALL,
            R.ADMINISTRATOR: _ALL,
            R.PRESIDENT: _ALL,
            R.BOARD: SCOPE_READ,
        },
        touches_money=True,
    ),
    _perm(
        "equipment.field.participant_price",
        "C4",
        _("Camp: preu per a l'alumne del material llogat"),
        kind="field",
        # L'instructor el veu a les seves sessions, però no el marge (MT12).
        allowed_scopes=(SCOPE_ALL, SCOPE_OWN_SESSIONS),
        initial={R.INSTRUCTOR: SCOPE_OWN_SESSIONS, **dict.fromkeys(_EQUIPMENT_STAFF, _ALL)},
        touches_money=True,
    ),
    _perm(
        "equipment.import.run",
        "MT13",
        _("Càrrega inicial de l'inventari"),
        initial={R.EQUIPMENT_MANAGER: _ALL, R.ADMINISTRATOR: _ALL},
    ),
    # Material (03; T-M03-22): «Cons.» per als rols que hi poden editar algun valor. VC-29, el
    # responsable de material; VC-28, el tresorer (apèndix de valors configurables).
    _perm(
        "settings.section.equipment",
        "AJ03",
        _("Ajustos de material"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={
            R.EQUIPMENT_MANAGER: SCOPE_READ,
            R.TREASURER: SCOPE_READ,
            R.ADMINISTRATOR: SCOPE_READ,
        },
    ),  # fmt: skip
    _perm(
        "settings.edit.equipment.review_notice_days",
        "AJ03-1",
        _("Dies d'antelació de l'avís de revisió del material"),
        requires=("settings.section.equipment",),
        initial={R.EQUIPMENT_MANAGER: _ALL},
    ),
    _perm(
        "settings.edit.equipment.unreturned_after_days",
        "AJ03-2",
        _("Dies després de l'activitat per a l'avís de material no retornat"),
        requires=("settings.section.equipment",),
        initial={R.EQUIPMENT_MANAGER: _ALL},
    ),
    # VC-28: el cost d'ús per tipus (`UsageRate`, amb `valid_from`). Diners: el canvi porta data
    # d'entrada en vigor i avisa el tresorer i la junta (RN-AJ-04).
    _perm(
        "settings.edit.equipment.usage_rates",
        "AJ03-3",
        _("Cost d'ús per tipus de material"),
        requires=("settings.section.equipment",),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    # Facturació (09; T-M09-26): VC-34 l'activa l'administrador per decisió de la junta, quan es
    # responguin la P-02 i la P-47 (RN-M09-19).
    _perm(
        "settings.section.billing",
        "AJ09",
        _("Ajustos de facturació"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.ADMINISTRATOR: SCOPE_READ},
    ),
    _perm(
        "settings.edit.billing.enabled_charge_kinds",
        "AJ09-1",
        _("Tipus de càrrec que es facturen (facturació activada)"),
        requires=("settings.section.billing",),
        initial={R.ADMINISTRATOR: _ALL},
        touches_money=True,
    ),
    # Marges i períodes (09; T-M09-26): VC-31 i VC-32, el tresorer («Qui el canvia» del bloc
    # «Valors configurables» de M09-6); l'administrador, «Cons.», com als altres apartats.
    _perm(
        "settings.section.margin",
        "AJ09-M",
        _("Ajustos de marges i períodes"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.TREASURER: SCOPE_READ, R.ADMINISTRATOR: SCOPE_READ},
    ),
    _perm(
        "settings.edit.margin.low_margin_threshold_cents",
        "AJ09-M1",
        _("Llindar de l'avís de marge baix"),
        requires=("settings.section.margin",),
        initial={R.TREASURER: _ALL},
    ),
    # RN-M09-28: el canvi només s'aplica als períodes que es creen després.
    _perm(
        "settings.edit.margin.period_length",
        "AJ09-M2",
        _("Durada dels períodes nous (mensual o trimestral)"),
        requires=("settings.section.margin",),
        initial={R.TREASURER: _ALL},
    ),
    # Ajuts (09; T-M09-26; RN-M09A-06 i 19): VC-36 i VC-37, el tresorer.
    _perm(
        "settings.section.grants",
        "AJ09-A",
        _("Ajustos dels ajuts"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.TREASURER: SCOPE_READ, R.ADMINISTRATOR: SCOPE_READ},
    ),
    _perm(
        "settings.edit.grants.deadline_reminder_days",
        "AJ09-A1",
        _("Dies dels avisos de tancament i de justificació dels ajuts"),
        requires=("settings.section.grants",),
        initial={R.TREASURER: _ALL},
    ),
    _perm(
        "settings.edit.grants.requirement_reminder_days",
        "AJ09-A2",
        _("Dies dels avisos dels requeriments d'esmena"),
        requires=("settings.section.grants",),
        initial={R.TREASURER: _ALL},
    ),
    # Activitats (02; M02-6, «Valors configurables»; T-M02-28): «Cons.» per als rols que hi editen
    # algun valor. VC-21 el tresorer; VC-22 i VC-24 el responsable de cursos i sortides (VC-24,
    # per decisió de la junta). VC-23 i VC-25 arriben amb els seus ajustos (T-M02-21 i T-M02-28).
    _perm(
        "settings.section.activities",
        "AJ02",
        _("Ajustos d'activitats"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={
            R.COURSES_MANAGER: SCOPE_READ,
            R.SECRETARY: SCOPE_READ,  # VC-57 (T-M02-48)
            R.TREASURER: SCOPE_READ,
            R.ADMINISTRATOR: SCOPE_READ,
            R.PRESIDENT: SCOPE_READ,  # VC-55, com AC6 (T-M02-48)
        },
    ),
    _perm(
        "settings.edit.activities.default_payment_window_hours",
        "AJ02-1",
        _("Hores per pagar una inscripció (per defecte)"),
        requires=("settings.section.activities",),
        initial={R.TREASURER: _ALL},
    ),
    _perm(
        "settings.edit.activities.offer_accept_hours",
        "AJ02-2",
        _("Hores per acceptar una plaça oferta de la llista d'espera"),
        requires=("settings.section.activities",),
        initial={R.COURSES_MANAGER: _ALL},
    ),
    _perm(
        "settings.edit.activities.default_requirements_mode",
        "AJ02-3",
        _("Mode dels requisits per defecte (avís o bloqueig)"),
        requires=("settings.section.activities",),
        initial={R.COURSES_MANAGER: _ALL},
    ),
    # VC-46 (RN-M02-26; T-M02-30): el responsable, per decisió de la junta.
    _perm(
        "settings.edit.activities.instructor_requirements_mode",
        "AJ02-10",
        _("Requisits per fer classe (avís o bloqueig)"),
        requires=("settings.section.activities",),
        initial={R.COURSES_MANAGER: _ALL},
    ),
    # Addenda de la 104 (VC-55 a VC-59): la destinació, qui té AC6; les fotos, l'administrador per
    # decisió de la junta; la conservació, la secretaria; els preus i cobrar-los, el tresorer.
    _perm(
        "settings.edit.activities.homologation_target_agency",
        "AJ02-4",
        _("Agència de destinació de les homologacions"),
        requires=("settings.section.activities",),
        initial=dict.fromkeys(_ACTIVITY_MANAGERS, _ALL),
    ),
    # VC-25 (RN-M02-24; T-M02-28b): l'enllaç per defecte a la previsió marítima, l'administrador.
    _perm(
        "settings.edit.activities.marine_forecast_url",
        "AJ02-25",
        _("Enllaç per defecte a la previsió marítima"),
        requires=("settings.section.activities",),
        initial={R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "settings.edit.activities.card_photos_enabled",
        "AJ02-5",
        _("Fotos de carnets de titulació (opció de la junta)"),
        requires=("settings.section.activities",),
        initial={R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "settings.edit.activities.card_photo_retention_months",
        "AJ02-6",
        _("Mesos que es conserva la foto d'una titulació"),
        requires=("settings.section.activities",),
        initial={R.SECRETARY: _ALL},
    ),
    _perm(
        "settings.edit.activities.homologation_fee_cents",
        "AJ02-7",
        _("Preu de l'homologació a la federació"),
        requires=("settings.section.activities",),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    _perm(
        "settings.edit.activities.course_filing_fee_cents",
        "AJ02-8",
        _("Preu de la tramitació de la titulació d'un curs"),
        requires=("settings.section.activities",),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    _perm(
        "settings.edit.activities.filing_fees_enabled",
        "AJ02-9",
        _("Cobrar les tramitacions a la federació"),
        requires=("settings.section.activities",),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    _perm(
        "settings.edit.activities.included_licence_expense_category",
        "AJ02-11",
        _("Categoria de despesa de la primera llicència inclosa al curs (VC-60)"),
        requires=("settings.section.activities",),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    _perm(
        "settings.edit.activities.homologation_department",
        "AJ02-12",
        _("Departament de l'ingrés d'una homologació (VC-61)"),
        requires=("settings.section.activities",),
        initial={R.TREASURER: _ALL},
        touches_money=True,
    ),
    # VC-23 (RN-M02-19; T-M02-21): la secretaria.
    _perm(
        "settings.edit.activities.reminder_days_before",
        "AJ02-23",
        _("Dies abans d'una sessió o sortida que surt el recordatori (VC-23)"),
        requires=("settings.section.activities",),
        initial={R.SECRETARY: _ALL},
    ),
    # --- 07 Web pública (M07-4; T-M07-02) -----------------------------------------------------
    # La matriu inicial de M07-4. El Responsable de comunicació comença sense res fins a la P-43.
    _perm(
        "website.pages",
        "WP1",
        _("Editar pàgines i blocs de la web, publicar-los i tornar a una versió anterior"),
        initial={R.ADMINISTRATOR: _ALL, R.PRESIDENT: _ALL},
    ),
    _perm(
        "website.news",
        "WP2",
        _("Crear, publicar i retirar notícies"),
        initial={R.ADMINISTRATOR: _ALL, R.PRESIDENT: _ALL},
    ),
    _perm(
        "website.media",
        "WP3",
        _("Pujar i retirar fotos i fitxers de la web, amb autor, permís i consentiment"),
        initial={R.ADMINISTRATOR: _ALL, R.PRESIDENT: _ALL},
        touches_personal_data=True,  # fotos on es veuen persones (P-41)
    ),
    _perm(
        "website.help",
        "WP4",
        _("Preguntes freqüents i tutorials"),
        initial={R.ADMINISTRATOR: _ALL, R.PRESIDENT: _ALL, R.BOARD: _ALL},
    ),
    # L'abast per motiu (RN-M07-07) arriba amb la safata (T-M07-11); d'inici, tots els motius.
    _perm(
        "website.contact",
        "WP5",
        _("Veure i respondre els missatges de contacte"),
        initial={R.SECRETARY: _ALL, R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "website.newsletter",
        "WP6",
        _("Redactar i enviar el butlletí (amb el recompte de subscriptors, mai el llistat)"),
        initial={R.ADMINISTRATOR: _ALL, R.PRESIDENT: _ALL},
    ),
    _perm(
        "website.subscribers",
        "WP7",
        _("Veure i exportar el llistat de subscriptors"),
        initial={R.ADMINISTRATOR: _ALL},
        touches_personal_data=True,
    ),
    _perm(
        "website.contact_reasons",
        "WP8",
        _("Motius de contacte i a qui arriba cada un"),
        initial={R.ADMINISTRATOR: _ALL},
    ),
    # Ajustos de la web (M07-6; T-M07-03): «Cons.» per a qui hi edita algun valor. WP1 (Admin. i
    # Pres.) edita la portada i les dades de contacte; els interruptors i els terminis, l'Admin.
    _perm(
        "settings.section.website",
        "AJ07",
        _("Ajustos de la web pública"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.ADMINISTRATOR: SCOPE_READ, R.PRESIDENT: SCOPE_READ},
    ),
    _perm(
        "settings.edit.website.home_activities_count",
        "AJ07-1",
        _("Activitats a la portada"),
        requires=("settings.section.website",),
        initial=dict.fromkeys(_WP1, _ALL),
    ),
    _perm(
        "settings.edit.website.news_on_home",
        "AJ07-2",
        _("Notícies a la portada"),
        requires=("settings.section.website",),
        initial=dict.fromkeys(_WP1, _ALL),
    ),
    _perm(
        "settings.edit.website.club_contact",
        "AJ07-3",
        _("Dades de contacte del club"),
        requires=("settings.section.website",),
        initial=dict.fromkeys(_WP1, _ALL),
    ),
    _perm(
        "settings.edit.website.newsletter_enabled",
        "AJ07-4",
        _("Butlletí actiu"),
        requires=("settings.section.website",),
        initial={R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "settings.edit.website.newsletter_confirm_hours",
        "AJ07-5",
        _("Hores per confirmar la subscripció al butlletí"),
        requires=("settings.section.website",),
        initial={R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "settings.edit.website.contact_enabled",
        "AJ07-6",
        _("Formulari de contacte actiu"),
        requires=("settings.section.website",),
        initial={R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "settings.edit.website.contact_retention_months",
        "AJ07-7",
        _("Mesos que es guarden els missatges de contacte tancats"),
        requires=("settings.section.website",),
        initial={R.ADMINISTRATOR: _ALL},
    ),
    # --- 08 Dashboard (M08-4; RN-RP-16) -------------------------------------------------------
    # DB1 dona només xifres agregades, mai cap dada personal ni cap pantalla de detall.
    _perm(
        "dashboard.view",
        "DB1",
        _("Veure el dashboard sencer, amb les xifres econòmiques"),
        initial=dict.fromkeys(
            (
                R.SECRETARY,
                R.COURSES_MANAGER,
                R.EQUIPMENT_MANAGER,
                R.TREASURER,
                R.HISTORY_DEPARTMENT,
                R.ADMINISTRATOR,
                R.PRESIDENT,
            ),
            _ALL,
        ),
        touches_money=True,
    ),
    # Sense cap acció a la primera versió (RN-M08-06): es declara per si se n'afegeix alguna.
    _perm(
        "dashboard.actions",
        "DB2",
        _("Fer accions des del dashboard (si n'hi ha)"),
        initial=dict.fromkeys((R.COURSES_MANAGER, R.TREASURER, R.ADMINISTRATOR, R.PRESIDENT), _ALL),
    ),
    # Ajustos del dashboard (M08-6; P-488 i P-487): «veure» i «veure i editar», l'Administrador.
    _perm(
        "settings.section.dashboard",
        "AJ08",
        _("Ajustos del dashboard"),
        allowed_scopes=(SCOPE_ALL, SCOPE_READ),
        initial={R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "settings.edit.dashboard.help_text",
        "AJ08-1",
        _("Text d'ajuda d'un indicador"),
        requires=("settings.section.dashboard",),
        initial={R.ADMINISTRATOR: _ALL},
    ),
    _perm(
        "settings.edit.dashboard.min_group_size",
        "AJ08-2",
        _("Mida mínima d'un grup al dashboard (P-487)"),
        requires=("settings.section.dashboard",),
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
