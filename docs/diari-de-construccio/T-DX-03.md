# T-DX-03 · Etiqueta «En construcció», l'ajust i el permís de la P-90

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 16/11/2026 17:40 | a0aabe3 | 13 noves | [A comprovar] (PR #66, `risc:alt`) |

**En tres línies:** la plataforma ja pot ensenyar pantalles de mòduls que encara no s'han fet, amb el seu disseny i un contingut inventat. Porten una etiqueta petita, «En construcció», i no poden desar ni enviar res. En local es veuen sempre; a producció només les veu qui tingui un permís que, d'entrada, no té ningú.

## Què s'ha fet
- `apps/core/under_construction.py`: el decorador de les vistes «En construcció». Només accepta GET (un POST, PUT, PATCH o DELETE torna 405) i dona «no trobat» (404) a qui no les pot veure.
- `SHOW_UNDER_CONSTRUCTION` (variable d'entorn): apagat per defecte, que és el valor de producció, i encès a `dev.py`.
- Permís nou `core.under_construction.view` (P-90, resposta C), sense cap rol al començament. Com que no hi ha cap cel·la inicial, no cal migració.
- L'etiqueta: `templates/_en_construccio.html` i `static/css/en-construccio.css`. Detall: [design-system §6.9](../design-system.md#69-etiqueta-en-construcció).
- Fila a [`estat/DX.md`](../estat/DX.md).

## Decisions i perquè
- **El control és al servidor, no a la plantilla:** amagar un botó no és cap control. Una pantalla «En construcció» no pot rebre cap petició que escrigui, i sense accés no existeix (404).
- **P-90, resposta C (propietari):** el permís l'assigna l'administrador per rol, des de l'editor. Els socis i la web pública no tenen permisos, així que a producció no hi arriben mai.
- **Alhora que la #65 del pilot (Norma 43), amb autorització del propietari del 16/11/2026,** perquè no comparteixen cap fitxer. Aquesta PR no toca l'extracte bancari, `files.py`, les migracions ni cap fitxer de documentació de la #65.

## Problemes trobats
- Cap. Avui cap vista no fa servir el decorador; les primeres seran la T-DX-09 i les de la 19 a la 42.

## Com se sap que funciona
- `apps/core/tests/test_under_construction.py`:
  - Cap mètode que escriu arriba a la vista (405).
  - Amb l'ajust encès, la veu tothom.
  - Amb l'ajust apagat: sense sessió, 404; un compte d'administrador sense el permís, 404; quan el seu rol el rep, 200.
  - El permís comença sense cap rol.
  - L'etiqueta és text traduïble amb `id` i sense `style=`.
  - **Prova comuna:** recorre totes les rutes de la plataforma amb el decorador i comprova que cap no accepta un mètode que escrigui.
- Proves del catàleg de permisos (matriu inicial cel·la per cel·la) i `makemigrations --check`, nets.
- Bateria sencera: 4.829 proves unitàries i 63 e2e (1 xfail que ja hi era).

## Evidències
- Sortida de proves · commit a0aabe3 · executada el 16/11/2026 en local (PostgreSQL 16):
  ```
  $ pytest apps/core/tests/test_under_construction.py apps/core/tests/test_permissions.py -q
  491 passed
  $ pytest -q
  4829 passed
  $ pytest -m e2e apps/core/tests/e2e -q
  63 passed, 1 xfailed
  ```
