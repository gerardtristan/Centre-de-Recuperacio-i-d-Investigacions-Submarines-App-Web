# T-DX-87 · P-283 tancada i fila B8 del tancament de la fase 1 al dia

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 20/11/2026 21:55 | bcd846b2 | Cap de nova (només documentació) | [A comprovar] |

**En tres línies:** el document de tancament de la fase 1 deia que el contrast de la barra inferior del mòbil en fosc (P-283) era una incidència oberta amb una prova `xfail`, i que bloquejava B8 «N1». La T-DX-48 (#154) ja ho havia corregit el 17/11 i la prova passa, però la fila de `pendents.md` no es va tancar. Ara la P-283 és a «Resolts» i B8 diu «fet».

## Què s'ha fet
- `docs/decisions/pendents.md`: la P-283 passa d'«Oberts» a «Resolts» (opció A, T-DX-48).
- `docs/estat/fase1-tancament.md`: B8 «fet»; només queda el lector de pantalla real (propietari).
- `docs/estat/DX.md`: fila de la T-DX-87.

## Decisions i perquè
- **El registre de mesura del 17/11 no es toca:** descriu el que es va mesurar aquell dia.
- **Seguretat i privacitat:** cap canvi de codi.

## Problemes trobats
- Cap.

## Com se sap que funciona
- `test_accessibilitat_mandat.py::test_mobile_tab_bar_contrast_in_dark` no té `xfail` i passa a la verificació completa del 20/11/2026.

## Comprovació §15.5
- No toca cap pantalla.

## Evidències
- No n'hi ha de visuals: és una correcció de documentació.
