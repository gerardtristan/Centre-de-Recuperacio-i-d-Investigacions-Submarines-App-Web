# T-RP-02d · Desactivar un compte d'administrador des de la pantalla

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 18/11/2026 | ce9f0929 (PR #216) | 24 noves i 1 e2e | [A comprovar] |

**En tres línies:** el servei per desactivar un compte d'administrador ja hi era, però només es podia fer servir des del servidor. Ara l'administrador ho fa des de la pantalla de rols del compte, també amb el seu: veu què passarà, escriu una nota i el codi de la seva aplicació d'autenticació. Si és el seu compte, surt de l'administració en confirmar-ho, i els altres administradors en reben un correu.

## Què s'ha fet
- Pantalla «Desactivar el compte …» (`apps/core/views/roles.py`, `templates/core/account_deactivate.html`), enllaçada des de «Rols de …». Només amb M3 (exclusiu de l'administrador); la resta, «no trobat».
- Resum abans de desar: el compte afectat, les sessions que es tanquen, el compte personal que no canvia i, si és el propi, l'avís que en sortiràs. Amb l'últim administrador operatiu ([RN-RP-13](../planning.md#ajustos-060-rols)), l'avís i cap formulari.
- `roles.deactivate_admin_account` guarda la nota al registre, rebutja un compte que ja era desactivat i, en confirmar la transacció, avisa per correu (plantilla `avis-desactivacio-admin`).
- L'entrada d'administració mostra l'avís de qui s'acaba de desactivar.

## Decisions i perquè
- **El mateix patró que els rols** (T-RP-02): GET per al resum, POST amb CSRF, nota, casella i codi TOTP nou. El codi només es comprova si el canvi es pot fer, perquè un intent impossible no compti per al bloqueig.
- **Autodesactivació** ([RN-RP-20](../planning.md#ajustos-060-rols)): el servei tanca totes les sessions del compte i la vista tanca també la de la petició en curs i porta a l'entrada amb un avís, sense «La sessió ha caducat».
- **Qui rep el correu:** els comptes actius amb el rol administrador i, si el desactiva un altre, el compte afectat. El President, no: ho pregunta la [P-370](../decisions/pendents.md), amb aquesta opció per defecte.

## Com se sap que funciona
- `apps/core/tests/test_account_deactivate_screen.py`: cada rol que no és administrador rep «no trobat»; codi equivocat, nota o casella buides i compte ja desactivat no canvien res; l'últim administrador operatiu no es pot desactivar i el codi no es gasta; dues sessions del mateix compte queden tancades i la petició en curs va a l'entrada (CA-RP-16); registre amb la nota i correus a qui toca.
- `apps/core/tests/e2e/test_rols.py`: un administrador es desactiva a si mateix amb un altre d'operatiu, amb captures a 1280, 390 i 320 px (clar i fosc), mirades.
