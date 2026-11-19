# T-RP-03 · Editor de permisos dels rols

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 19/11/2026 15:52 | servei a la PR #268 (T-RP-03a); pantalla a la PR següent (T-RP-03b) | 27 al servei, 25 a la pantalla i 1 e2e | [A comprovar] |

**En tres línies:** fins ara, la matriu de permisos només canviava amb una migració. Ara l'administrador la canvia des de «Rols i permisos»: tria un mòdul (i, si vol, un rol), canvia les cel·les, en veu el resum amb els comptes afectats i ho desa amb una nota i el codi de la seva aplicació d'autenticació. Cada canvi deixa una versió nova de la matriu, una entrada per cel·la al registre i un correu als que ho han de saber.

## Què s'ha fet
Dues PR, per la mida (D4): la T-RP-03a (servei, #268) i la T-RP-03b (pantalla).
- Servei `apps/core/permission_matrix.py`: cel·les vigents i inicials, diferència, comptes afectats, què és sensible i què amplia l'accés, comprovació (`check`) i desament (`save`).
- Pantalla `permisos/` (`apps/core/views/permission_matrix.py`, `templates/core/permission_matrix.html`) amb el disseny de l'Avisador (T-DX-19) i `avisador.css` tal com és. Entrada «Rols i permisos» al grup «Seguretat i RGPD» del menú, amb M3b.
- Correu `avis-canvi-permisos` (RN-RP-09) i acció de registre `roles.permission_changed` (RN-RP-08).

## Decisions i perquè
- **Qui:** M3b (`core.permissions.edit`), protegit i exclusiu de l'administrador. La resta de rols, també el President, «no trobat», amb GET i amb POST (CA-RP-03).
- **El mateix patró que els rols (T-RP-02):** «Mostra el resum» i «Torna a la configuració inicial» no desen res; desar és un POST amb CSRF, nota, casella i codi TOTP nou. El codi només es comprova si el canvi es pot desar, perquè un intent impossible no compti per al bloqueig.
- **Filtres per mòdul i per rol:** la matriu sencera (73 permisos × 11 rols) feia una pàgina de 44.000 px al mòbil. Ara es veu un mòdul alhora, i al mòbil, un rol. Les cel·les que no surten no es toquen en desar, i «Torna a la configuració inicial» només afecta les que es veuen, les mateixes que s'enviaran.
- **Canvis alhora:** el formulari porta la versió de la matriu amb què s'ha obert. Desar bloqueja les versions i, si n'hi ha una de nova, no desa res i ho diu.
- **Petició directa:** una cel·la protegida, d'un rol que no és de gestió o que no existeix rebutja tot el canvi (CA-RP-09). Els `requires` i els abasts admesos els valida `roles.validate_role_permissions`, que ja hi era (CA-RP-07).
- **Sessions (RN-RP-11, CA-RP-10):** si una cel·la dona un permís nou o un abast més ampli en un permís de diners, de dades personals o d'un camp sensible, es tanquen les sessions dels comptes amb aquell rol. La de qui desa, no: acaba d'escriure el codi TOTP. Dubte nou: [P-401](../decisions/pendents.md), opció per defecte A.

## Com se sap que funciona
- `apps/core/tests/test_permission_matrix.py` (27, el servei): cada rol que no és administrador rep «no trobat»; un canvi vàlid deixa la versió, una entrada per cel·la i el correu als administradors, als afectats i al President (CA-RP-05); es rebutgen un `requires` que falta (CA-RP-07), una cel·la protegida (CA-RP-09), un rol que no és de gestió, un abast no admès, un canvi buit, una nota buida i una matriu canviada mentrestant; tancament de sessions en ampliar l'accés i no en reduir-lo (CA-RP-10).
- `apps/core/tests/test_permission_matrix_screen.py` (25, la pantalla): «no trobat» per GET i POST a la resta de rols; files protegides sense control; el resum i «Torna a la configuració inicial» no desen res; sense codi o sense nota no es desa res (CA-RP-04); una cel·la protegida per petició directa (CA-RP-09); filtres i cel·les que no surten.
- `apps/core/tests/e2e/test_permisos.py`: l'administrador obre la pantalla des del menú, filtra la Secretaria, dona M7, veu el resum i el desa. Captures a 1280, 390 i 320 px (clar i fosc), mirades: a 1280 px, amb tots els rols, la matriu es desplaça de costat; amb un rol, cap desplaçament.

## Què queda
- La pantalla en construcció `/en-construccio/rols-permisos/` es pot retirar: ho proposarà la sessió de disseny al propietari.
- Revisió visual de conjunt: [T-F1-01](../planning.md#F1-revisio-final).
