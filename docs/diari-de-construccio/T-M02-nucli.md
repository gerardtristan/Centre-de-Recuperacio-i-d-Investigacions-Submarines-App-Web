# T-M02 (nucli) · Peces del nucli per al 02

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 21/11/2026 05:23 | (vegeu la PR) | 11 noves; 2 de la 00 ajustades | [A comprovar] |

**En tres línies:** quatre peces petites del nucli que el mòdul d'activitats necessita. El text «Soc major d'edat» dels convidats passa a ser un text legal que es pot editar a la pantalla de textos legals, amb una proposta que a producció no es publica fins que la junta la validi. També s'aproven els avisos de cancel·lació, es deixa apuntat on el 02 allibera les sessions d'un instructor que perd el rol i es donen els permisos de l'apartat d'ajustos d'activitats.

## Què s'ha fet
- `consents.KINDS` + `adult_declaration`. La proposta és a `apps/activities/guests.py` (`ADULT_PROPOSAL`) i la publica `seed_demo_data` (local); les proves del 02 la creen a la fixture.
- `events.APPROVED` + `enrolment.cancelled` i `activity.cancelled` (RN-M02-36).
- `roles.py`: el comentari de RN-RP-12 apunta al 02 (decisió 101, T-M02-04b).
- `settings.section.activities` i tres `settings.edit.activities.*` amb les cel·les inicials (`core/0066`).

## Decisions i perquè
- Instrucció escrita del propietari (21/11/2026): text editable amb proposta, pendent de la junta (P-458). A producció no es publica: el formulari de convidats rebutja fins llavors (D2, irreversible).
- No hi ha cap interruptor nou: la diferència entre local i producció és qui publica el text (la càrrega de dades inventades o l'administrador).
- La prova del menú d'ajustos fa servir ara l'instructor com a rol sense cap apartat (el responsable de cursos té el del 02).

## Problemes trobats
Cap.

## Com se sap que funciona
`apps/core/tests/test_activities_core.py` (tipus a `KINDS`, cap versió publicada per les migracions, esdeveniments aprovats i cel·les per rol), `test_seed_demo_data.py` (la proposta publicada a local) i `apps/activities/tests/test_guests.py` (amb la proposta el convidat s'inscriu; sense text, es rebutja).

## Termes nous
Cap.
