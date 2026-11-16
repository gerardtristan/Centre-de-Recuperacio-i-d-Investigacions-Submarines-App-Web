# Estat de les tasques — DX Recursos de disseny externs (carril de disseny)

Mapa, ordre i detall de cada tasca: [`plans/recursos-disseny-extern.md` §7](../plans/recursos-disseny-extern.md#7-ordre-proposat-per-a-la-fase-2), aprovat pel propietari el 16/11/2026. Regles de disseny: [`design-system.md` §15](../design-system.md#15-regles-b-c-i-d-dels-recursos-externs). Format: [README](README.md).

## Regles del carril (propietari, 16/11/2026)

- **Carril propi, D. Disseny** ([pla d'acceleració §4.1](../plans/pla-acceleracio.md#41-què-pot-avançar-alhora)). Compta dins el màxim de tres carrils oberts.
- **Una sola tasca alhora**, en l'ordre de la taula: `tokens.css` i les plantilles comunes ho toquen tot.
- **Si xoca amb el carril de tresoreria o de pagaments** (el mateix fitxer, la mateixa plantilla o una PR oberta que l'hagi de rebasar), **mana el de tresoreria i pagaments**: la tasca de disseny espera o es rebasa després.
- Una tasca que canvia codi d'`apps/core` o d'`apps/accounts` (la T-DX-03, pel permís i l'ajust) passa per la regla del nucli: un sol canvi obert alhora.
- Cada tasca: un recurs en un lloc, menys de 400 línies de codi d'aplicació; primer la peça al sistema de disseny (document i CSS amb tokens) i després a la plantilla. Una pantalla «En construcció» porta la prova de només lectura i l'etiqueta (§6.9); quan es torna funcional, la prova canvia i l'etiqueta se'n va. Proves, captures a 1280 i 390 px en clar i en fosc, mirades, comprovació de §15.5 i diari de construcció.

| Tasca | Estat | Data | PR | Bloqueig o nota |
|---|---|---|---|---|
| T-DX-01 Tokens de moviment i radis (§15.4: durades, corbes, escala de premut, `--r-interior`) | feta | 16/11/2026 | #47 | Tokens de moviment (§15.4) amb els noms que ja existien, `.radi-concentric` i els logotips més grans del propietari (només els logotips; el selector de tema no canvia). Els components fan servir els tokens nous a partir de les tasques següents |
| T-DX-02 Paleta OKLCH amb alternativa, vores amb transparència i profunditat del tema fosc; contrastos tornats a comprovar | en curs | 16/11/2026 | — | Després de la T-DX-01 |
| T-DX-03 Etiqueta «En construcció», l'ajust `SHOW_UNDER_CONSTRUCTION`, el permís «Veure pantalles en construcció» (P-90) i la prova comuna de només lectura | per fer | — | — | `risc:alt` (permís nou) i nucli: cap altre canvi obert a `apps/core` |
| T-DX-04 Duermevela: motor de tema (substitueix `tema.js`, manté la clau `cris-tema`) | per fer | — | — | — |
| T-DX-05 Eclipse: control de tema a la web pública i a l'àrea del soci | per fer | — | — | Després de la T-DX-04 |
| T-DX-06 Errata: resum d'errors, començant pel formulari «Fer-se soci» | per fer | — | — | — |
| T-DX-07 Solapas a l'administració | per fer | — | — | P-96: llista de pestanyes a `sessionStorage`, sense noms |
| T-DX-08 Ramillete: navegació de l'àrea del soci | per fer | — | — | — |
| T-DX-09 Baliza: novetats i notificacions, en construcció | per fer | — | — | P-98 (C) |
| T-DX-10 Tramite: estat del pagament (càrrec, targeta, Bizum) | per fer | — | — | Bizum quan la PR #38 sigui a `master`. Carril de pagaments primer |
| T-DX-11 Tramite i Emisor: el rebut | per fer | — | — | P-93: només el segell |
| T-DX-12 Deposito: pagar per transferència; el comprovant, en construcció | bloquejada | — | — | Fins que la PR #41 (T-M04-10) sigui a `master` |
| T-DX-13 Vigencia: quota i llicència a l'àrea del soci | per fer | — | — | El compte enrere surt del servidor (070, P-71) |
| T-DX-14 Vigencia: llicències a l'administració | per fer | — | — | — |
| T-DX-15 Autentico: verificació del carnet | per fer | — | — | Mateixes dades que ara (RN-M01-26) |
| T-DX-16 Deposito: panell de revisió a altes pendents i sol·licituds | per fer | — | — | — |
| T-DX-17 Oleaje: portada de l'àrea del soci | per fer | — | — | Substitueix l'ona de la 032 |
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
