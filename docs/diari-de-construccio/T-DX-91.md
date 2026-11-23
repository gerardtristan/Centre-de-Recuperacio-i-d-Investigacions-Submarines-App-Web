# T-DX-91 · Les proves no depenen del `SHOW_UNDER_CONSTRUCTION` del `.env` local

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 23/11/2026 13:10 | 02a9082f | 1 nova; navegació i «En construcció» | [A comprovar] |

**En tres línies:** en local, `test_navigation` i `test_ramillete` fallaven i al CI passaven. La configuració de proves heretava `SHOW_UNDER_CONSTRUCTION` de `base.py`, que el llegeix del `.env`, i el `.env` local l'encén. Ara les proves sempre comencen amb les pantalles «En construcció» apagades, com al CI.

## Què s'ha fet
- `config/settings/test.py`: `SHOW_UNDER_CONSTRUCTION = False`.
- `apps/previews/tests/test_settings_dx91.py`: carrega la configuració de proves en un procés a part amb `SHOW_UNDER_CONSTRUCTION=1` a l'entorn i comprova que val `False`.
- `docs/estat/DX.md`.

## Decisions i perquè
- **`False`, no el valor del `.env`:** les proves que volen veure les pantalles en construcció ja l'encenen elles mateixes (`settings.SHOW_UNDER_CONSTRUCTION = True` o `override_settings`). La resta s'ha de provar com a producció.
- **La prova va en un procés a part:** la configuració ja és carregada quan corren les proves. Només un procés nou demostra que la variable de l'entorn no hi entra.
- **Seguretat i privacitat:** no canvia res de l'aplicació; només la configuració de les proves.

## Problemes trobats
- A la verificació de la T-DX-90 sortien 13 unitàries i 2 e2e en vermell en local. Amb `SHOW_UNDER_CONSTRUCTION=0`, hi passen totes menys `test_accessibilitat_05b.py::test_member_payment_screens`. Aquesta es queda esperant `networkidle` quan la màquina va carregada, i al CI passa.

## Com se sap que funciona
- La prova nova falla sense el canvi (la variable de l'entorn encenia les pantalles) i passa amb el canvi.
- `test_navigation`, `test_navigation_previews` i `test_under_construction` passen en local amb el `.env` de sempre.

## Comprovació §15.5
- No toca cap pantalla: sense captures.
