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
    # --- 02 Activitats (cursos i sortides) --------------------------------------------------
    # T-M02-33: la matriu inicial de la 059 («02 Activitats»), cel·la per cel·la. AC1 a AC4 són
    # accions públiques o pròpies i no tenen permís de rol. CF1 i CF2 (conferències) són del
    # mòdul 11 i es declararan amb ell. «Cons.» és l'abast de només consulta.
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
