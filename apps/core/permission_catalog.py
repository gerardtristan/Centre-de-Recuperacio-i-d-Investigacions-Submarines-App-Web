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
# 059, addenda del M02: el tresorer i el President gestionen activitats completes, com el
# responsable de cursos i sortides i l'administrador.
_ACTIVITY_MANAGERS = (R.COURSES_MANAGER, R.TREASURER, R.ADMINISTRATOR, R.PRESIDENT)

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
    # (activar l'opció de no socis) és l'ajust `licences.non_members_enabled`: el seu permís
    # arriba amb la pantalla d'ajustos del mòdul (T-M06-20).
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
