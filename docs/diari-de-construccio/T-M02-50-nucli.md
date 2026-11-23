# T-M02-50 (nucli) · Permisos de «Inclou la primera llicència» (AC27 i AC28) i ajustos VC-60 i VC-61

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 23/11/2026 16:40 | ff3c2273 | proves del catàleg del 02 i de la matriu | [A comprovar] |

**En tres línies:** el catàleg de permisos té AC27 (veure si el preu d'un curs inclou la primera llicència de l'alumne) i AC28 (veure-ho i canviar-ho, que demana AC27), i el tresorer edita els dos ajustos nous de la decisió 104: la categoria de despesa i el departament del cost de la llicència inclosa (VC-60 i VC-61). És la resposta provisional del propietari a P-426 (#403).

## Què s'ha fet
- `apps/core/permission_catalog.py`: AC27, AC28 i els permisos d'edició de VC-60 i VC-61 (AJ02-11 i AJ02-12), marcats com a diners.
- `core/0073_activities_first_licence_permissions`: les cel·les inicials amb una versió nova de la matriu (060), reversible.

## Decisions i perquè
- Feina del carril B4; la migració era la 0072 i passa a la 0073 perquè la 0072 la va fer servir la T-M09-26 (#488).

## Problemes trobats
- Cap.

## Com se sap que funciona
`apps/core/tests/test_activities_core.py` i `test_permissions_02.py` (2.520 proves del nucli en verd al carril); `makemigrations --check` net.
