# T-M02-30 (nucli) · Permís de VC-46 i instructor de prova amb requisits

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 21/11/2026 11:01 | (vegeu la PR) | 8 noves (7 casos + 1) | [A comprovar] |

**En tres línies:** el responsable de cursos i sortides ja pot canviar des dels ajustos si els requisits per fer classe bloquegen o només avisen. Les dades inventades fan que l'instructor de prova sigui soci actiu amb una llicència tècnica vigent, perquè les sessions de prova tinguin instructor també amb el mode «bloqueig». I el `seed_demo_data` carrega les dades del 02.

## Què s'ha fet
- `apps/core/permission_catalog.py` i `core/0069_instructor_requirements_permission`: `settings.edit.activities.instructor_requirements_mode` (AJ02-10) per al responsable de cursos, amb una versió nova de la matriu.
- `apps/members/demo_data.py`: `instructor_member`, un soci de ple dret amb la quota pagada.
- `seed_demo_data`: el compte `instructor-demo` es crea sobre aquest soci, amb una llicència tècnica declarada (`licences.declare_existing`, 365 dies) i, amb la branca d'abans, el compte `cursos-demo` i les dades del 02.

## Decisions i perquè
- El permís és el que diu el pla (VC-46: el responsable, per decisió de la junta).
- La llicència tècnica és de 365 dies perquè cobreixi les sessions de prova dels dos mesos següents.
- La part de P-459 (AC27) no s'hi fa: és un dubte de permisos sense resposta.

## Problemes trobats
La prova de l'ordre del 02 suposava que `seed_demo_data` no en carregava les dades; ara la base ja en té i l'ordre es nega, com ha de fer.

## Com se sap que funciona
`test_t_m02_30_only_the_courses_manager_edits_vc_46` (per rol) i `test_t_m02_30_the_demo_instructor_is_a_member_with_a_technical_licence`; les proves de permisos, del seed i del 02 (2387) en verd.

## Termes nous
Cap.
