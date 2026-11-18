# Proves en dispositius reals i amb lector de pantalla (P-284 i P-301)

Llista de comprovació per al propietari, que fa aquestes proves ([097](../decisions/097-respostes-del-propietari-a-les-preguntes-obertes-del-18-11-2026.md)). Cobreix B5 i B8 de la [checklist](../checklist-produccio.md): la **part 1** (flux de mandat, «N1») s'ha de fer **abans d'encendre el nivell 1**, i la **part 2** («N2»), **abans del nivell 2**. Tasca: T-F1-02 ([estat](../estat/F1.md)). El que ja s'ha provat a Chromium és a [`T-M05a-18-accessibilitat-mandat.md`](T-M05a-18-accessibilitat-mandat.md).

## Abans de començar

- [ ] **Entorn de proves temporal en marxa.** Encara no existeix: espera el teu sí al cost ([089](../decisions/089-prova-d-acceleracio-interruptors-d1-a-d6.md), D5). Mai a producció.
- [ ] **Només dades inventades.** L'entorn es carrega amb `seed_demo_data`. No hi escriguis mai el teu IBAN, el teu DNI ni dades d'un soci real. Per al mandat, fes servir un IBAN inventat de l'entorn de proves.
- [ ] Comptes de prova: un soci (àrea personal), un tresorer i un administrador (entrada de l'administració, amb el doble factor en una app del mòbil de proves).
- [ ] Dispositius:
  - el teu mòbil;
  - un altre del sistema contrari (si el teu és Android, un iPhone, i al revés);
  - una tauleta (només a la part 2);
  - un ordinador amb Firefox i, si n'hi ha, Safari.
- [ ] Lectors de pantalla: **TalkBack** (Android: Ajustos → Accessibilitat) i **VoiceOver** (iPhone: Ajustos → Accessibilitat). Practica abans els gestos bàsics: lliscar per avançar, tocar dues vegades per activar.
- [ ] Apunta, per a cada dispositiu, el model, el sistema i la versió del navegador.

## Com apuntar el resultat

Per a cada pas: **OK**, o bé **KO** amb una frase que digui què passa, on i amb quin dispositiu. Si pots, fes-ne una captura (sense dades personals). Els KO van a la taula del final i, d'allà, a una tasca del pilot o del carril de disseny.

## Part 1 — Flux de mandat (B5 i B8 «N1»)

Fes-la sencera amb tots dos mòbils, primer sense lector de pantalla i després amb TalkBack (Android) o VoiceOver (iPhone).

| # | Pas | Què has de comprovar |
|---|---|---|
| 1.1 | Entra com a soci a l'àrea personal | La pàgina cap a l'amplada del mòbil, sense desplaçament lateral. Les lletres es llegeixen sense ampliar |
| 1.2 | Ves a «Com pago la quota» i envia el formulari sense triar res | Surt «Tria una de les opcions.», en català. El lector de pantalla l'anuncia |
| 1.3 | Tria la domiciliació i ves a «Mandat de domiciliació» | Es veuen el creditor, l'identificador, el tipus (recurrent) i la referència |
| 1.4 | Envia el formulari buit | Cada camp amb error diu què falta. El lector llegeix l'error quan arribes al camp |
| 1.5 | Escriu l'IBAN inventat | El teclat del mòbil és còmode per a l'IBAN. Els espais s'accepten |
| 1.6 | Signa el mandat | Surt el mandat actiu amb l'IBAN emmascarat (mai sencer) i «Canvia l'IBAN» |
| 1.7 | Revoca el mandat, primer sense la contrasenya i després amb ella | Sense contrasenya, l'error és clar. Amb contrasenya, el mandat queda revocat i la preferència torna a «pagar cada vegada» |
| 1.8 | Surt i obre una pantalla del flux sense sessió | Et porta a l'entrada i, després d'entrar, et torna a la pantalla on eres |
| 1.9 | Tema clar i fosc (selector de tema) | Tot es llegeix en tots dos. Fixa't en la barra inferior en fosc ([P-283](../decisions/pendents.md)) |
| 1.10 | Text ampliat al 200 % (ajust de mida de lletra del mòbil) | No es tallen textos ni botons, i no apareix desplaçament lateral |
| 1.11 | Tresorer, des del mòbil: «Mètodes i mandats», «Revoca el mandat» (també sense motiu) i «Campanya de mandats» | Les taules es poden llegir o desplaçar dins del seu requadre, i els botons es poden tocar amb el dit |
| 1.12 | Firefox i Safari d'escriptori: passos 1.2 a 1.7 | Fan el mateix que a Chromium |

Amb el lector de pantalla, comprova també:
- [ ] Cada camp anuncia la seva etiqueta.
- [ ] Els botons diuen què fan, no només «botó».
- [ ] L'ordre de lectura segueix l'ordre de la pantalla.
- [ ] En enviar amb errors, saps que n'hi ha sense haver de mirar la pantalla. Avui el focus queda a dalt de la pàgina (recomanació de la T-M05a-18): apunta si et costa trobar els errors.

**Part 1 superada quan:** cap pas no és KO a cap dels dos mòbils, o els KO que queden tenen una tasca i el propietari accepta encendre el nivell 1 amb ells.

## Part 2 — Resta de pantalles (B5 i B8 «N2»)

Abans de fer-la, el pilot ha d'haver afegit l'auditoria axe a les pantalles de la 04 i del 05b, perquè els errors automàtics ja estiguin corregits. Fes-la amb un mòbil, la tauleta i un lector de pantalla com a mínim. Per a cada pantalla, mira els mateixos punts de la part 1: amplada, errors, tema clar i fosc, text al 200 % i lector de pantalla.

**Soci i convidat:**
- [ ] Fer-se soci (formulari públic), amb errors i sense.
- [ ] Perfil: dades, correu, data de naixement, consentiments, esborrar el compte (amb contrasenya).
- [ ] Quotes i detall d'una quota; pagar amb targeta i amb Bizum (proveïdor de proves): esperant confirmació, pagat, fallit i «no s'ha confirmat a temps».
- [ ] Rebut d'un pagament.
- [ ] Carnet: amb connexió i sense, i la verificació pública del carnet.
- [ ] Canvi de tipus i baixa.
- [ ] Pàgina del convidat i pagament com a convidat.
- [ ] Instal·lar la web al mòbil (ajuda per a l'iPhone).

**Administració (tresorer i administrador):**
- [ ] Entrada amb el doble factor des del mòbil.
- [ ] Socis: altes pendents (aprovar i rebutjar), llista, fitxa, edició, tipus de soci i sol·licituds.
- [ ] Quotes i impagats: marcar i desmarcar l'impagat amb motiu.
- [ ] Tresoreria: inici, moviments, conciliació, «a revisar», traspàs, arqueig i liquidacions.
- [ ] Pagaments: llista, mandats, campanya, remeses i retornats.
- [ ] Ajustos i registre d'activitat.

**Tauleta, en horitzontal i en vertical:**
- [ ] Les pantalles de l'administració que més es faran servir (conciliació, «a revisar» i altes pendents) es poden fer servir sense ampliar.

**WCAG 2.2 AA a mà** (el que l'axe no pot comprovar):
- [ ] Amb un teclat connectat a la tauleta o a l'ordinador, sense ratolí, s'arriba a tot, el focus es veu sempre i no queda atrapat enlloc.
- [ ] Res no depèn només del color: els estats porten text.
- [ ] Els missatges de confirmació i d'error s'anuncien.
- [ ] Els objectius tàctils són prou grans (uns 24 px com a mínim).
- [ ] La vora dels camps es veu bé ([097](../decisions/097-respostes-del-propietari-a-les-preguntes-obertes-del-18-11-2026.md): si costa de veure, el carril de disseny la torna a mirar).

**Part 2 superada quan:** cap pas no és KO, o els que queden tenen una tasca i el propietari accepta el nivell 2 amb ells.

## Resultats

| Data | Part i pas | Dispositiu, sistema i navegador | Lector | OK o KO | Què passa | Tasca |
|---|---|---|---|---|---|---|
| | | | | | | |
