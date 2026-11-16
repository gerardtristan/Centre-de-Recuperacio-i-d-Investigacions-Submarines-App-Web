# Estat de les tasques — DX Recursos de disseny externs (carril de disseny)

Mapa, ordre i detall de cada tasca: [`plans/recursos-disseny-extern.md` §7](../plans/recursos-disseny-extern.md#7-ordre-proposat-per-a-la-fase-2), aprovat pel propietari el 16/11/2026. Regles de disseny: [`design-system.md` §15](../design-system.md#15-regles-b-c-i-d-dels-recursos-externs). Format: [README](README.md).

## Regles del carril (propietari, 16/11/2026)

- **Carril propi, D. Disseny** ([pla d'acceleració §4.1](../plans/pla-acceleracio.md#41-què-pot-avançar-alhora)). Compta dins el màxim de tres carrils oberts.
- **Diverses tasques alhora, amb agents** (propietari, 16/11/2026, i [decisió 094](../decisions/094-fusio-de-les-risc-alt-i-tres-carrils.md) punt 3), si no comparteixen cap fitxer de codi. Les pantalles «En construcció» només afegeixen fitxers propis (§16 del sistema de disseny); `tokens.css`, la base i la navegació comuna, d'una en una i per la sessió de DISSENY. Les files d'aquesta taula, l'índex del diari i les seccions del sistema de disseny es resolen en fer el rebase.
- **Si xoca amb el carril de tresoreria o de pagaments** (el mateix fitxer, la mateixa plantilla o una PR oberta que l'hagi de rebasar), **mana el de tresoreria i pagaments**: la tasca de disseny espera o es rebasa després.
- Una tasca que canvia codi d'`apps/core` o d'`apps/accounts` (la T-DX-03, pel permís i l'ajust) passa per la regla del nucli: un sol canvi obert alhora.
- Cada tasca: un recurs en un lloc, menys de 400 línies de codi d'aplicació; primer la peça al sistema de disseny (document i CSS amb tokens) i després a la plantilla. Una pantalla «En construcció» porta la prova de només lectura i l'etiqueta (§6.9); quan es torna funcional, la prova canvia i l'etiqueta se'n va. Proves, captures a 1280 i 390 px en clar i en fosc, mirades, comprovació de §15.5 i diari de construcció.

| Tasca | Estat | Data | PR | Bloqueig o nota |
|---|---|---|---|---|
| T-DX-01 Tokens de moviment i radis (§15.4: durades, corbes, escala de premut, `--r-interior`) | feta | 16/11/2026 | #47 | Tokens de moviment (§15.4) amb els noms que ja existien, `.radi-concentric` i els logotips més grans del propietari (només els logotips; el selector de tema no canvia). Els components fan servir els tokens nous a partir de les tasques següents |
| T-DX-02 Paleta OKLCH amb alternativa, vores amb transparència i profunditat del tema fosc; contrastos tornats a comprovar | feta | 16/11/2026 | #50 | Estats en OKLCH amb la mateixa L per rol i hexadecimal de reserva; vores amb `color-mix()`; `--c-superficie-flotant`. Els primitius de marca queden en hexadecimal |
| T-DX-03 Etiqueta «En construcció», l'ajust `SHOW_UNDER_CONSTRUCTION`, el permís «Veure pantalles en construcció» (P-90) i la prova comuna de només lectura | feta | 16/11/2026 | #66 | `risc:alt` (permís nou al catàleg; nucli). Alhora que la #65 del pilot, sense cap fitxer en comú (autorització del propietari, 16/11/2026) |
| T-DX-04 Duermevela: motor de tema (substitueix `tema.js`, manté la clau `cris-tema`) | feta | 16/11/2026 | #51 | Motor a `static/js/tema.js` (es manté el nom): pestanyes sincronitzades, `theme-color` i cortina de `--m-panell`; directe amb moviment reduït |
| T-DX-05 Eclipse: interruptor de dia i nit a la part pública (sense sessió); en obrir, el tema del sistema; «Com el sistema» quan s'ha fixat | feta | 16/11/2026 | #54 | Decisió del propietari del 16/11/2026: a la pública, l'interruptor visible i per defecte el tema del sistema |
| T-DX-05b Tema a la configuració del compte (socis i administració), per defecte «Sistema»; el selector surt de la capçalera | feta | 16/11/2026 | #55 | Decisió del propietari del 16/11/2026. Socis: «Aparença» a «Seguretat del compte»; administració: a l'inici. Substitueix la T-M01-45 (selector a la capçalera) |
| T-DX-06 Errata: resum d'errors, començant pel formulari «Fer-se soci» | feta | 16/11/2026 | #52 | Resum «Hi ha N errors» amb un enllaç per camp, al formulari d'alta (web i presencial). La validació en sortir de cada camp queda per a més endavant |
| T-DX-07 Solapas a l'administració | feta | 16/11/2026 | #57 | P-96 (B): adreça i etiqueta sense noms a `sessionStorage`. Fitxa del soci i de les sol·licituds; les altres fitxes s'hi afegeixen amb el bloc `solapa` |
| T-DX-08 Ramillete: navegació de l'àrea del soci | feta | 16/11/2026 | #58 | Per sota de 600 px i amb JavaScript. «Surt» es queda a la capçalera (un sol «Surt» per pantalla, T-M01-46) |
| T-DX-09 Baliza: novetats i notificacions, en construcció | feta | 16/11/2026 | #77 | Primera pantalla «En construcció» i el patró de totes (§16): un fitxer a `apps/previews/screens`, sense tocar codi comú. Novetats i avisos a `/en-construccio/novetats/`. P-98 (C) |
| T-DX-10 Tramite: estat del pagament (càrrec, targeta, Bizum) | feta | 16/11/2026 | #60 | Passos de l'estat del servidor dins de `_status.html`; Bizum inclòs. El rebut amb la ranura és la T-DX-11 |
| T-DX-11 Tramite i Emisor: el rebut | feta | 16/11/2026 | #62 | P-93 (C): només el segell. La ranura i la impressió en blanc i negre, de Tramite |
| T-DX-12 Deposito: pagar per transferència; el comprovant, en construcció | bloquejada | — | — | La pantalla de transferència és la T-M05b-06 (pilot), encara per fer; la T-M04-10 només ha deixat el servei `transfer_reference` |
| T-DX-13 Vigencia: quota i llicència a l'àrea del soci | feta | 16/11/2026 | #63 | Compte enrere al servidor; dies d'avís = recordatoris de VC-02 (cap valor nou). A «Les meves quotes» i a la llicència del perfil |
| T-DX-14 Vigencia: llicències a l'administració | feta | 16/11/2026 | #64 | Llicència de la fitxa de l'administració. La confirmació en bloc no en porta (sense data). Arreglat el desbordament a 320 px d'una llicència declarada |
| T-DX-15 Autentico: verificació del carnet | feta | 16/11/2026 | #67 | Segell «Vàlid» o «No vàlid» a la verificació pública; cap dada nova (RN-M01-26); sense codi HMAC al navegador |
| T-DX-16 Deposito: panell de revisió a altes pendents i sol·licituds | feta | 16/11/2026 | #69 | Comptadors «per revisar» i accions en una fila a Altes pendents i Sol·licituds. Sense motius predefinits (cap llista al pla) |
| T-DX-17 Oleaje: portada de l'àrea del soci | feta | 16/11/2026 | #71 | Capçalera amb ona i bloc «La teva quota» (estat, Vigencia, carnet) que puja en desplaçar, només amb CSS. Substitueix l'ona de la 032 |
| T-DX-18 Monograma: avatar per defecte a partir de `avatar_seed` | per fer | — | — | Mai a partir del nom (RN-M01-30) |
| T-DX-19 Avisador: rols i permisos, en construcció | per fer | — | — | Funcional quan es faci la T-RP-03 |
| T-DX-20 Avisador: ajustos, en construcció | per fer | — | — | Funcional quan es faci la T-AJ-02 |
| T-DX-21 Cartola: pendents per antiguitat, en construcció | per fer | — | — | Pantalla proposada; el pla no la té (D1) |
| T-DX-22 Deposito: transferències i pagaments a revisar, en construcció | per fer | — | — | Funcional amb la T-M04-12 i la T-M05b-16 |
| T-DX-23 Calendari general (Horario, després Solape), en construcció | per fer | — | — | — |
| T-DX-24 Activitats i inscripció (Camilla i Comanda), en construcció | per fer | — | — | P-94 |
| T-DX-25 Marcador, en construcció | per fer | — | — | — |
| T-DX-26 Desfile i Oleaje a la portada pública, en construcció | per fer | — | — | Desfile sense avanç automàtic |
| T-DX-27 Vistazo: projectes, en construcció | per fer | — | — | — |
| T-DX-28 Recoveco: ajuda i preguntes freqüents, en construcció | per fer | — | — | — |
| T-DX-29 Calendari d'un dia (Asueto), en construcció | per fer | — | — | — |
| T-DX-30 Reasigna, en construcció | per fer | — | — | — |
| T-DX-31 Publicar activitats (Averia i Pregon), en construcció | per fer | — | — | — |
| T-DX-32 Avaries del material (Averia), en construcció | per fer | — | — | — |
| T-DX-33 Finances per àmbit (Gastos), en construcció | per fer | — | — | — |
| T-DX-34 Factures (Emisor), en construcció | per fer | — | — | — |
| T-DX-35 Dashboard (Parrilla), en construcció | per fer | — | — | — |
| T-DX-36 Editor de la web (Probador i Pregon), en construcció | per fer | — | — | — |
| T-DX-37 Fotos (Fototeca i Expositor), en construcció | per fer | — | — | — |
| T-DX-38 Convite, en construcció | per fer | — | — | P-99 (A) |
| T-DX-39 Xats (Teletipo; Amanuense com a caixó d'escriure, sense veu), en construcció | per fer | — | — | P-97 (A); P-95: sense veu |
| T-DX-40 Social (Seguir i Monograma de fauna), en construcció | per fer | — | — | — |
| T-DX-41 Signatures de correu (Antefirma), en construcció | per fer | — | — | P-92 |
| T-DX-42 Apoderado: avisos i textos legals, en construcció | per fer | — | — | P-91 |
