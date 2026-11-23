# T-M02-51a (nucli) · Permís de l'ajust del tipus de la primera llicència (P-530)

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 23/11/2026 20:04 | b38c3b46 | proves de permisos del 06 | [A comprovar] |

**En tres línies:** la secretaria i el tresorer poden editar l'ajust que diu de quin tipus és la primera llicència d'un alumne quan el curs la inclou (P-530), i el tresorer pot consultar l'apartat de llicències dels ajustos. L'ajust comença buit i, mentre ho és, no es crea cap llicència inclosa.

## Què s'ha fet
- `apps/core/permission_catalog.py`: `settings.edit.licences.first_licence_type` (AJ06-5) per a la secretaria i el tresorer; el tresorer, «Cons.» a l'apartat de llicències.
- `core/0074_licences_first_licence_type_permission`: les cel·les amb una versió nova de la matriu (060), reversible.

## Decisions i perquè
- P-530 (irreversible: diners i el que veu l'alumne): ajust buit per defecte fins que la secretaria i el tresorer el triïn. Feina del carril B4.

## Problemes trobats
- Cap.

## Com se sap que funciona
`apps/core/tests/test_permissions_06.py`; 2.421 proves del nucli en verd al carril.
