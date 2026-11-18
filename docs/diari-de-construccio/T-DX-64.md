# T-DX-64 · Proves e2e amb esperes amb condició

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 18/11/2026 16:35 | c21cde67 | 2 proves canviades | [A comprovar] (PR #242) |

**En tres línies:** algunes proves e2e fallaven de tant en tant per temps quan la màquina anava carregada. Per indicació del propietari, les esperes fixes passen a esperes amb condició (auto-espera de Playwright), sense afegir reintents ni pujar els temps globals. La que continua fallant de tant en tant queda apuntada com a P-313.

## Què s'ha fet
- `apps/core/tests/e2e/conftest.py`: `review()` espera que acabin les transicions (`SETTLED_JS`), en lloc de 500 ms fixos.
- `apps/core/tests/e2e/test_logotip.py`: espera que la xarxa quedi en repòs, en lloc de 300 ms.
- `docs/decisions/pendents.md`: P-313 (la primera prova d'una tanda, en obrir `/entrar/`).

## Decisions i perquè
- **Dos bucles es queden:** el de `test_flux_primer_euro` espera el codi TOTP següent (cada 30 s) i el de `test_pwa_079` comprova l'estat del service worker amb un termini. Tots dos esperen una condició, no un temps a cegues.

## Problemes trobats
- Cap.

## Com se sap que funciona
- e2e de logotip, fumada, navegació i rebut: 11 passen i 4 se salten (Firefox i WebKit no són a la màquina local, com preveu la T-DX-54).
