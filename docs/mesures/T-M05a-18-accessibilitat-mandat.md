# T-M05a-18: accessibilitat i dispositius del flux de mandat (B5 i B8, «N1»)

Revisió del flux de mandat per al nivell 1 ([checklist](../checklist-produccio.md), B5 i B8; [P-M05a-F](../planning.md#M05a-5-processos), pas 2). Data: 17/11/2026. Prova automàtica: `apps/core/tests/e2e/test_accessibilitat_mandat.py`. Informes JSON a `.e2e-captures/accessibilitat/mandat-soci.json` i `mandat-administracio.json` (fora de Git). Només dades inventades.

## Resultat per a la checklist

| ID | Abast N1 | Resultat | Pendent |
|---|---|---|---|
| B5 | Flux de mandat en mòbil (Android, iOS) i navegadors habituals | **En part.** Totes les pantalles del flux funcionen a 1280, 390 i 320 px en Chromium, en clar i en fosc, i cap no es desplaça de costat a 320 px. | Provar-ho en un iPhone (Safari) i en un Android (Chrome) reals, i en Firefox i Safari d'escriptori [A comprovar: dispositiu real]. Qui i quan: [P-284](../decisions/pendents.md). |
| B8 | Accessibilitat bàsica del flux de mandat: contrast, teclat, etiquetes, errors clars | **Superada, amb una incidència de disseny.** axe (WCAG 2.0 a 2.2, A i AA): cap violació greu a les pantalles del flux. Teclat: amb el tabulador s'arriba a tots els elements, en ordre i amb el focus visible, sense trampes. Etiquetes: tots els camps en tenen. Errors: cada camp amb error porta `aria-invalid` i `aria-describedby` cap al missatge; els errors generals van amb `role="alert"`. | Contrast de la barra inferior del mòbil en fosc (4,18:1; cal 4,5:1), component de disseny: [P-283](../decisions/pendents.md). Lector de pantalla real [A comprovar: VoiceOver i TalkBack]. |

## Pantalles revisades
Cadascuna a 1280, 390 i 320 px i, per a axe, en clar i en fosc:
- **Soci:** «Com pago la quota» (sense preferència, amb error per no triar cap opció i amb el mandat signat); «Mandat de domiciliació» (formulari per signar, enviat buit amb errors, i el mandat actiu amb «Canvia l'IBAN»); «Revoques el mandat?» (i enviat sense la contrasenya); una pantalla del flux sense sessió, que porta a l'entrada i hi torna després d'entrar.
- **Tresorer:** «Mètodes i mandats», «Revoca el mandat» (i sense el motiu) i «Campanya de mandats».

La sessió caducada (no només absent) és la mateixa per a totes les pantalles i ja la prova `test_sessio_caducada_081.py`.

## Dispositius i navegadors

| Què | Com | Resultat |
|---|---|---|
| Ordinador, 1280 px | Chromium headless (Playwright 1.64.1, chromium-headless-shell 1248), Windows | Correcte |
| Mòbil, 390 px (amplada d'un iPhone 12 a 15) | Mateix Chromium, només l'amplada: sense agent d'usuari ni tacte de mòbil | Correcte, amb la incidència de contrast de P-283 en fosc |
| Mòbil petit o zoom del 400 %, 320 px | Mateix Chromium | Correcte, sense desplaçament lateral |
| Tema clar i fosc | Atribut `data-theme` a cada pantalla | Correcte, amb la incidència de P-283 en fosc |
| iPhone amb Safari (WebKit) | — | [A comprovar: dispositiu real] |
| Android amb Chrome, teclat del mòbil per a l'IBAN | — | [A comprovar: dispositiu real] |
| Firefox i Safari d'escriptori | — | [A comprovar: dispositiu real] |
| VoiceOver (iOS) i TalkBack (Android) | — | [A comprovar: dispositiu real] |
| Text ampliat al 200 % (només la lletra) | — | [A comprovar: dispositiu real] |

## Què s'ha corregit
- «Com pago la quota»: el formulari porta `novalidate`. Abans, si no es triava cap opció, sortia l'avís del navegador, en la llengua del navegador i sense passar pel servidor. Ara surt el missatge del servidor, «Tria una de les opcions.», en català i com a alerta. Les altres pantalles del flux ja ho feien així.

## Per a la sessió de disseny (no s'ha tocat)
- **Contrast de `.ramillete-pestanya` en fosc** (P-283): text #9ba8ab sobre #314351, 4,18:1, a les cinc pestanyes de la barra inferior del mòbil i a totes les pantalles del soci (no és només del flux de mandat). Prova `xfail` estricta a `test_accessibilitat_mandat.py`: quan es corregeixi, passarà a fallar i caldrà treure-la.
- **Resum d'errors en tornar el formulari** (recomanació, no és cap error d'N1): després d'enviar un formulari amb errors, la pàgina es torna a carregar i el focus queda a dalt. Els errors es poden trobar perquè cada camp hi apunta, però un lector de pantalla no els anuncia sols. Un component «resum d'errors» amb enllaços als camps i el focus a sobre, o «Error:» al títol de la pàgina, ho resoldria per a tota la plataforma.

## Revisió manual d'axe
axe deixa per revisar a mà el contrast dels símbols ✓ i ◷ de les etiquetes d'estat. Són `aria-hidden` i decoratius: el text del costat diu l'estat. No cal fer-hi res.
