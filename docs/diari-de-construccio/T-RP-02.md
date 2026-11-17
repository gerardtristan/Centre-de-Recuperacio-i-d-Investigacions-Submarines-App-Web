# T-RP-02 · Assignar i retirar rols des de la pantalla

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 17/11/2026 | 2cf591df, fa50b7e9 (revisió) | 40 noves i 1 e2e | [A comprovar] |

**En tres línies:** fins ara, els rols dels comptes d'administrador només es podien canviar des del servidor. Ara l'administrador ho fa des de la llista de comptes: tria el rol, veu què canviarà i a qui afecta, i ho desa amb una nota i el codi de la seva aplicació d'autenticació. Tothom qui ho ha de saber en rep un correu.

## Què s'ha fet
- Pantalla «Rols de …» (`apps/core/views/roles.py`, `templates/core/account_roles.html`), enllaçada des de «Comptes d'administrador», que ara també mostra els rols de cada compte.
- Resum abans de desar ([RN-RP-07](../planning.md#ajustos-060-rols)): el canvi, el compte afectat i els avisos d'un sol tresorer (RN-RP-14), del compte que es queda sense cap rol (RN-RP-11) i de l'últim administrador operatiu (CA-RP-06), que amaga el formulari.
- Serveis de `apps/core/roles.py`: la nota arriba al registre (RN-RP-08) i cada canvi avisa per correu els administradors, el President i el compte afectat (RN-RP-09, plantilla `avis-canvi-rol`).
- Tasques noves a [`estat/M00.md`](../estat/M00.md): responsables orfes (espera el 02), tancar sessions en assignar un rol (espera la [P-330](../decisions/pendents.md)) i la pantalla de desactivar un compte (RN-RP-20).

## Decisions i perquè
- **El mateix control que el restabliment d'un altre compte** (RN-M01-60): un codi TOTP nou de qui ho fa, a la mateixa petició. Un codi equivocat no canvia res i compta per al bloqueig.
- **El resum és un GET i desar és un POST:** mirar el resum no desa res; el servidor ho torna a comprovar tot en desar.
- **Sense entrada pròpia al menú:** la navegació és del carril de disseny; s'hi arriba des de la llista de comptes.

## Problemes trobats
- Si assignar un rol ha de tancar les sessions del compte, el pla no ho diu per a aquesta tasca (sí per a l'editor de permisos). No s'ha implementat: és la P-330.

## Revisió de la PR #202
Cada punt, primer amb una prova que fallava i després l'arreglo (fa50b7e9):
- Un canvi que ja estava fet (un altre administrador s'hi ha avançat) diu «No s'ha desat res: el canvi ja estava fet», sense registre ni correu. `assign_role` torna `None` i `remove_role` llança `AlreadyDone`.
- El codi TOTP només es gasta si el canvi es pot fer: les condicions (canvi vigent, últim administrador operatiu) es miren abans. Si el servei el rebutja igualment, el missatge diu que el codi ja s'ha fet servir.
- Un GET només pren l'acció i el rol de l'adreça, mai la nota ni el codi.
- La nota va al correu (el pla no diu què ha de portar, a part del canvi i de qui l'ha fet). El correu surt quan es confirma la transacció, fora dels bloquejos, i arriba al compte afectat encara que sigui pendent o desactivat.
- Una sola regla d'«administrador operatiu» (`leaves_no_operational_admin`, amb `lock`) per a rols, desactivació, TOTP i RGPD.

## Com se sap que funciona
- `apps/core/tests/test_roles_screen.py`: cada rol que no és administrador (també el President) rep «no trobat»; codi equivocat, nota o casella buides no canvien res; l'últim administrador operatiu no perd el rol; nota i valor anterior al registre; correus a qui toca; sessions tancades quan el compte perd l'únic rol (CA-RP-11, sense la part del 02).
- `apps/core/tests/e2e/test_rols.py`: de la llista al resum amb l'avís d'un sol tresorer i al desat, amb captures a 1280, 390 i 320 px (clar i fosc), mirades.

## Termes nous
- **CSRF** (falsificació de peticions entre llocs): el testimoni que porta cada formulari perquè una altra web no pugui enviar-lo en nom teu.
