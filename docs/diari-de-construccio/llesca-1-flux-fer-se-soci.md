# Llesca 1 · Prova del flux sencer «fer-se soci»

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 13/11/2026 10:18 | PR #20 | 2 noves (e2e) | [A comprovar] |

**En tres línies:** fins ara cada pas de fer-se soci tenia la seva prova, però cap comprovava que tots lliguessin. Ara un navegador fa el camí sencer tot sol, de la sol·licitud a la web fins al carnet verificat, entrant com cada persona que hi intervé. No canvia res de l'aplicació: és una prova.

No és una tasca del pla: és la prova amb què acaba la llesca 1 del [pla d'acceleració](../plans/pla-acceleracio.md) (§3; [089](../decisions/089-prova-d-acceleracio-interruptors-d1-a-d6.md), D3).

## Què s'ha fet
- Una prova al navegador que encadena set trams de [P-M01-A i P-M01-E](../planning.md#M01-5-processos): el visitant omple «Fer-se soci»; la secretaria aprova l'alta; la persona crea el compte amb la invitació i veu la quota pendent; la tresoreria veu la quota; es paga; el soci veu la quota pagada i el carnet; i la verificació pública diu «Vàlid».
- Cada tram es fa a la pantalla real i amb el rol que toca: la secretaria i la tresoreria entren amb contrasenya i doble factor; la verificació es fa sense sessió.
- Entre tram i tram es comprova el que no ha de passar: abans de pagar no hi ha carnet ni es pot demanar, i la verificació no mostra ni els cognoms ni el correu.
- Desa una captura de cada tram a 1280 i 390 px (fora de Git), numerades de l'1 al 7.

## Decisions i perquè
- **El registre manual del pagament no s'ha construït.** És l'únic tram sense pantalla, bloquejat per [P-12](../decisions/pendents.md). Hi ha dues proves: la que passa salta aquest tram amb els serveis que confirmen un pagament, sense SQL; la del flux encadenat sencer busca l'acció a la fitxa del soci, no la troba i queda marcada com a «fallada esperada», amb la referència.
- **La fallada esperada només val per a aquest tram.** Si es trenca qualsevol altre pas, la prova falla de debò: així no amaga cap error.
- **Les dates surten del pagament desat**, no del rellotge de la prova: tant és a quina hora s'executi.
- **Cap espera fixa.** Quan la data de naixement torna a dibuixar una part del formulari, la prova espera el canvi que es veu a la pantalla.

## Problemes trobats
- El dia de l'aprovació, l'«estat de la quota» general d'un soci nou surt buit («—»), tot i que la fila de la quota diu «Pendent». És el que diu la regla vigent ([079](../decisions/079-respostes-del-responsable-al-grup-a-de-t-m00-i-t-m01.md), RN-M01-86): una quota pendent que encara no ha vençut no dona cap estat. La prova mira la fila de la quota i no fixa aquest buit; queda apuntat per si es vol revisar.
- El soci amb la quota pendent no té encara cap botó per pagar: és del 05b (pas 6 de P-M01-A).

## Com se sap que funciona
- CA-M01-01, CA-M01-03, CA-M01-06, CA-M01-12 i CA-M01-13, encadenats en una sola prova.
- Cinc execucions seguides en verd.
- Sortida de proves · PR #20 · executada el 13/11/2026 en local (PostgreSQL 16):
  ```
  $ pytest -m e2e apps/core/tests/e2e/test_flux_fer_se_soci.py --reuse-db
  1 passed, 1 xfailed
  $ pytest -m e2e apps/core/tests/e2e --reuse-db
  43 passed, 1 xfailed
  ```

## Termes nous
- **Prova de flux sencer** (`end-to-end`): una prova que fa un procés de punta a punta com el faria una persona, en lloc de comprovar una peça sola.
- **Fallada esperada** (`xfail`): una prova que se sap que falla per un motiu anotat. Si un dia passa, avisa, perquè es tregui la marca.
