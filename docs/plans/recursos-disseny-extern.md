# Recursos de disseny externs: inventari, encaix, mapa i ordre

- **Versió:** 2 (16/11/2026). **Estat:** mapa aprovat pel propietari el 16/11/2026 (PR #45). La 2 hi afegeix els quatre recursos que faltaven (Convite, Teletipo, Solape i Baliza), les respostes a les P-90 a P-96 i les preguntes noves P-97 a P-99. Les tasques T-DX són a la cua de [`docs/estat/DX.md`](../estat/DX.md).
- **Font:** els 34 fitxers `design/extern/moxen-*.zip`, copiats sense cap canvi des de la carpeta local `design/Extern` (mateix nom i mateix contingut, comprovat amb SHA-256). Són la font original i no s'esborren.
- **Regles de disseny:** les taules B, C i D són a [`design-system.md` §15](../design-system.md#15-regles-b-c-i-d-dels-recursos-externs), amb els noms originals.
- **Què no fa aquest document:** no canvia cap regla congelada del pla (D1 de la [089](../decisions/089-prova-d-acceleracio-interruptors-d1-a-d6.md)). Quan un recurs demana una funció que el pla no té, aquí es diu «proposta» i la pantalla va «En construcció» fins que una decisió l'afegeixi.

## 1. Abast

**Una sola interfície.** No és un wireframe: és la plataforma sencera, amb totes les pantalles de totes les tasques, la navegació comuna (Solapas a l'administració, Ramillete a l'àrea del soci) i les interaccions.

- **Pantalla funcional:** la que ja té codi. Té les seves dades i els seus permisos, com ara.
- **Pantalla «En construcció»:** disseny i interaccions visuals (obrir, navegar, pestanyes), però no desa, no envia i no modifica res. Al servidor només respon a `GET` (cap ruta que escrigui), els formularis van dins d'un `fieldset disabled` i el contingut és d'exemple, inventat i fix, sense llegir ni escriure cap model. A dalt a la dreta porta l'etiqueta «En construcció» ([`design-system.md` §6.9](../design-system.md#69-etiqueta-en-construcció)). Si només un bloc no és funcional, l'etiqueta va només en aquell bloc.
- **Interruptor:** en local i a l'entorn de proves, l'ajust `SHOW_UNDER_CONSTRUCTION` (variable d'entorn) les mostra a tothom. **A producció està apagat** i només les veuen els comptes d'administrador amb el permís «Veure pantalles en construcció», que l'administrador assigna per rol i mai als socis ni a la web pública ([P-90](../decisions/pendents.md), resposta C). Mentre ningú no tingui el permís, a producció no les veu ningú. Sense accés, la ruta respon 404 i el menú no les mostra.
- **Quan una tasca s'acaba,** l'etiqueta se'n va, la prova «només lectura» es substitueix per les proves de la tasca i la pantalla passa a ser funcional.

**Res no es perd.** Cada recurs conserva el seu nom original (Solapas, Vigencia, Tramite…) com a nom del component: classe `.vigencia`, fitxers `static/css/vigencia.css` i `static/js/vigencia.js`. Els noms són noms propis i no es tradueixen, tot i que la resta del codi segueixi la convenció de §11 del sistema de disseny.

**Les quatre fonts que faltaven** (Convite, Teletipo, Solape i Baliza) es van afegir el 16/11/2026. Ara hi ha els 38 zip a `design/extern/`, idèntics als de la carpeta local (SHA-256 a §2.1). **Tres no són el que diu el nom:** Teletipo és un lector de canals RSS, no un xat ([P-97](../decisions/pendents.md)); Baliza són marques de novetats, no notificacions ([P-98](../decisions/pendents.md)); Convite és la targeta d'un esdeveniment, sense fotos ni mapa ([P-99](../decisions/pendents.md)). Cap dels quatre no envia dades fora de la UE, tret de la tipografia, que se substitueix per la local com a tots els altres.

## 2. Inventari: què és cada recurs de debò

**Comú a tots:** són demostracions de Moxen (`index.html` amb un `.css` i un `.js` propis i un `README.md` en castellà i en anglès). JavaScript sense biblioteques ni passos de compilació («Dependencias: Ninguna»), variables CSS al principi del full d'estil i `prefers-reduced-motion` a tots. **Tots carreguen una tipografia de fora (Google Fonts o Fontshare)**, que no es pot fer servir (decisions 035 i 046). Sis porten fotos d'arxiu amb `CREDITOS.md` (Convite, Desfile, Expositor, Fototeca, Seguir i Vistazo; arquitectura, ceràmica, quadres i paisatge): són de la demostració i no surten mai a la plataforma (regla D11). Mides en línies de JS / CSS.

| Recurs | Què és de debò | Mida | Com s'adapta a la pila (es conserva el disseny; canvia el que diu la columna) |
|---|---|---|---|
| Solapas | Pestanyes d'una app de gestió: una per fitxa oberta; arrossegar per ordenar, × per tancar (passa a la de la dreta), menú de desbordament amb comptador, punt de canvis sense desar | 524 / 291 | La barra es pinta al servidor. Cada pestanya carrega la fitxa amb HTMX dins d'un panell que es queda al DOM, així es conserva el que s'ha escrit. Esborranys: [P-96](../decisions/pendents.md) |
| Reasigna | Repartiment de cites quan algú falta: vol de les cites cap a qui fa el mateix servei, «sin lugar», marge d'hora, confirmar tot alhora | 409 / 268 | La proposta la calcula el servidor; el vol és presentació. Res es desa fins a «Confirmar» |
| Autentico | Comprovant amb codi HMAC-SHA-256 calculat al navegador (SubtleCrypto) i segell «VÁLIDO» / «ALTERADO» | 481 / 304 | **La clau mai va al navegador:** el codi es calcula i es comprova al servidor. Del recurs es queden el segell i els grups del codi. No aprova res: verifica |
| Cartola | Antiguitat de documents pendents per client en trams 0–30, 31–60 i més de 60 dies; filtres per estat, disputa, exportar CSV | 340 / 246 | Trams i xifres calculats al servidor; filtres amb HTMX. Els trams són configurables. L'exportació passa pel permís d'exportar i pel registre d'activitat |
| Averia | Formulari d'avaria: preguntes segons l'equip, fotos reduïdes amb un llenç i sense la ubicació EXIF, rebuig pel contingut, franja amb folio | 492 / 315 | Preguntes per tipus com a dades. La validació del fitxer (`core.validate_upload`) i l'eliminació de l'EXIF es fan **també al servidor**; la reducció al navegador és una ajuda |
| Antefirma | Generador de signatures de correu: plantilles i colors, «copiar amb format» (HTML amb estils en línia), text pla i codi, validació del correu i el telèfon | 388 / 237 | La vista prèvia fa servir els tokens. Només el text copiat porta estils en línia, perquè és per als clients de correu i no es pinta en cap pantalla nostra |
| Vigencia | Dies que queden de llicències i certificats sobre una regla de 60 dies amb alertes a 30, 15 i 7; ordre per urgència; «Renovar» +6/12/24 mesos; `.ics` amb `VALARM` | 356 / 276 | Dies, estat i data els dona el servidor (070, P-71). Fora el lliscador de temps i el «Renovar» del navegador: renovar és pagar. Barra amb `<meter>` (sense `style=`). `.ics` generat al servidor |
| Horario | Horari setmanal: triar el grup de cada assignatura, encavalcaments ratllats en taronja, avís abans de triar, cerca de combinacions | 344 / 282 | Les franges i els encavalcaments venen del servidor; el navegador només marca l'avís previ |
| Ramillete | Barra inferior amb un botó central que s'obre en ventall (accions ràpides), focus atrapat i Esc; en pantalla ampla passa a lateral | 342 / 312 | No són pestanyes petites: és una barra de navegació amb l'acció principal. Menú construït al servidor per permisos, com ara (T-M01-46) |
| Emisor | Emetre butlleta o factura: el formulari de factura es desplega i la fulla es va omplint; RUT xilè amb mòdul 11; empreses desades al navegador | 382 / 291 | RUT → NIF, NIE o CIF amb la lletra de control (`core.normalize_document`). Les empreses es desen al servidor, mai al `localStorage`. Lloc: [P-93](../decisions/pendents.md) |
| Deposito | Pagar per transferència: copiar les dades del compte (un camp o tots), pujar el comprovant (imatge o PDF ≤ 3 MB, pel contingut) i seguir-ne l'estat; panell del negoci per confirmar o rebutjar amb motiu | 363 / 300 | Dades del compte del club i referència (T-M04-10) des del servidor. Comprovant amb `core.validate_upload`. Confirmar o rebutjar és una acció amb permís, motiu i registre |
| Tramite | Seguiment d'un pagament (processant, autoritzat, abonat), «Reintentar» i «Cancel·lar» si es rebutja, rebut que surt d'una ranura, imprimir en blanc i negre | 338 / 251 | Les etapes són els estats de l'intent de pagament (05b), consultats amb HTMX. Fora el temps simulat. El rebut només surt quan el servidor l'ha confirmat (regla B10) |
| Marcador | Cinta de punt de llibre amb física de cadena: cau, rebota, s'amara de tinta; en treure-la s'enrotlla | 210 / 111 | Desat al servidor per als socis; per als no socis, només els identificadors de les activitats al `localStorage` (cap dada personal) |
| Oleaje | Transició de seccions en desplaçar: la següent puja amb la vora en ona i escuma; l'ona s'agita segons la velocitat; paral·laxi | 135 / 97 | Lent, desactivable, s'atura amb la pestanya amagada i amb `prefers-reduced-motion` (§5) |
| Eclipse | Interruptor de tema: el sol creua el carril, la lluna el tapa, estrelles; onada de canvi de tema que surt de l'astre | 143 / 171 | Control visual damunt del motor de Duermevela. Discret: mida del selector actual (§7 del sistema de disseny) |
| Duermevela | Motor de tema clar, fosc o «Sistema»: script al `<head>` abans de pintar, sincronització entre pestanyes, `theme-color`, `color-scheme`, `<picture>`; cortina que surt del control | 277 / 238 | Substitueix `static/js/tema.js` i manté la clau `cris-tema`. Les il·lustracions de l'habitació no s'hi fan servir |
| Vistazo | Llista amb una finestra de foto que segueix el cursor, s'inclina i entra amb una cortina; al mòbil, primer toc mostra i segon obre | 154 / 72 | Fotos del club amb consentiment. Gradients en OKLCH (C7) |
| Recoveco | Preguntes freqüents plegades per tema; la cerca del navegador obre la resposta; enllaç a la frase exacta; cercador propi si cal | 424 / 220 | Les preguntes són textos d'ajuda: dades editables (regla «Valors i llistes»). `⌘F` → `Ctrl+F`; `Ctrl+K` per a la cerca general (B19) |
| Apoderado | App d'un tutor dins d'un telèfon: avisos que es confirmen, calendari de proves, assistència amb percentatge, autoritzacions signades amb el dit una sola vegada | 611 / 433 | És una app sencera de quatre pestanyes. Lloc: [P-91](../decisions/pendents.md) |
| Gastos | Anell de segments amb la despesa del mes, total que roda, filtre per categoria amb FLIP, canviar de mes, «Afegir despesa» | 593 / 274 | Imports en cèntims, xifres del servidor; anell en SVG amb atributs (sense `style=`). Categories = centres de cost |
| Comanda | App de cambrers: estat de les taules, plats amb regles («tria'n 2», incompatibilitats), botó que no s'encén fins que tot val, cuina simulada | 782 / 391 | Del recurs es queden les regles de les opcions i el botó que espera; validació també al servidor. Fora la cuina simulada. Lloc: [P-94](../decisions/pendents.md) |
| Avisador | Matriu de quins avisos reps i per quin canal, amb vista prèvia, resum en paraules, canal apagat que bloqueja la columna, «Solo lo importante», «Restaurar» | 485 / 256 | Per als permisos, la matriu és rol × apartat amb «veure» i «veure i editar»; desar demana TOTP, nota i resum dels afectats (059). Per als avisos, és la mateixa peça |
| Asueto | Dia concret: nanses d'obertura i tancament, dia tancat, cites que ja no hi caben ratllades amb la primera hora lliure, «Mover», «Aplicar» l'excepció | 657 / 333 | Les excepcions s'apliquen al servidor; res es mou fins a «Aplicar» |
| Camilla | App de reserva de cita dins d'un telèfon: especialitat, professional, dia, franges ocupades apagades, dades validades en viu, ✓, `.ics`, «Les meves cites» | 614 / 350 | **És una clínica:** fora tot el que és salut (especialitats, dades del pacient). Del recurs es queden el flux per passos, les franges i el `.ics`. Lloc: [P-94](../decisions/pendents.md) |
| Errata | Errors en sortir de cada camp, resum «Hi ha 3 errors» amb enllaços, índex de seccions, error del servidor al mateix resum, «Tot correcte» | 542 / 389 | El servidor és qui valida; el navegador avança el mateix missatge. Missatges que no revelen si un compte existeix |
| Pregon | Vista prèvia de compartir: tres targetes (xat, xarxa social, correu) que es reescriuen alhora, comptador de caràcters, punt focal de la imatge, «Copiar etiquetes» | 366 / 243 | Les etiquetes `meta` es generen al servidor |
| Parrilla | Tauler de ginys: arrossegar, encaix, redimensionar per passos de reixa, paleta, «Guardar disposició» com a dades, «Restaurar» | 563 / 305 | La disposició es desa per compte al servidor. Cap giny no mostra dades personals |
| Probador | Galeria de plantilles com a miniatures vives, FLIP fins a un marc d'escriptori, botons de dispositiu, lliscador de color | 415 / 316 | El color només pot ser un dels tokens; plantilles i colors com a dades |
| Fototeca | Biblioteca de fotos: selecció amb un rectangle elàstic, carpetes, ventall, desfer, panell de detalls amb nom i etiquetes, pujada amb anell | 795 / 342 | Fotos a Scaleway (París), EXIF fora al servidor, persones identificables només amb consentiment |
| Expositor | Graella de pujada: anell de càrrega, foto massa petita ratllada amb el motiu, reordenar (també amb teclat), «Fer portada», «6 fotos llestes» | 545 / 236 | La mida mínima com a dada. Mateixes regles de fotos que Fototeca |
| Monograma | Avatar generatiu a partir d'un nom (iniciales, bloques, ondas, mosaico), «Otra variante», paletes, copiar SVG i descarregar | 525 / 211 | **Mai a partir del nom:** a partir de `Member.avatar_seed` (RN-M01-30). Paletes amb tokens |
| Seguir | Botó «Seguir» → «Siguiendo» amb goma, comptador que roda, anell de l'avatar i partícules | 131 / 152 | Comptador del servidor; seguir és opcional i els perfils són privats per defecte |
| Desfile | Carrusel amb el desplaçament i l'imant del navegador, «3 / 8», barra de progrés, avanç automàtic amb pausa i el motiu de la pausa | 262 / 148 | Sense avanç automàtic per defecte (D20). Targetes fora de vista inertes, com al recurs |
| Amanuense | **No és un xat:** dictat per veu en un camp de text, amb text provisional i definitiu, puntuació dictada, paraules dubtoses i «Desfer dictat» | 924 / 273 | **Es fa servir sense veu** ([P-95](../decisions/pendents.md), resposta del propietari): el seu disseny és el caixó d'escriure dels xats. El reconeixement de veu del navegador no es fa servir mai (a Chrome, l'àudio surt cap a Google, fora de la UE). El dictat arribarà amb els xats, amb un reconeixement instal·lat al servidor de la UE (dependència nova, `risc:alt`, amb el sí del propietari) |
| Convite | **Targeta d'un esdeveniment, sense fotos ni mapa:** la data és un full de calendari; «Assistiré» encén la plaça següent de la barra i «Queden 12» roda fins a 11; «Afegir al calendari» dona un `.ics` real, l'enllaç o el text, i el full vola en arc fins a la icona; «La meva hora» converteix l'hora del lloc a la teva; campana de recordatori | 616 (JS + CSS) | Places i inscripció del servidor; «Assistiré» obre el flux d'inscripció (Camilla, P-94) i no apunta ningú pel navegador. `.ics` al servidor. Fora «La meva hora» (totes les activitats són en hora local). L'enllaç copiat és el de la plataforma. Una foto d'arxiu (`CREDITOS.md`), que no es fa servir. Lloc: [P-99](../decisions/pendents.md) |
| Teletipo | **Lector de canals RSS/Atom i OPML, no un xat:** en deixar-hi un fitxer, cada font entra al lateral amb el seu comptador i els articles s'imprimeixen al rotlle com tires de teletip; l'article s'obre net (sense guions ni rastrejadors, sense `utm_*` ni `fbclid`) i la tira passa a gris; J i K per recórrer, M marca, S desa, «Tot llegit». Llegeix fitxers locals amb `DOMParser`; no fa cap petició a la xarxa; desa llegits i desats al `localStorage` | 1388 (JS + CSS, 4 fitxers) | Per als xats (P-97, recomanació A) es conserva la carcassa: lateral de converses amb comptadors, rotlle de missatges, J/K i «Tot llegit». Els missatges els pinta el servidor amb l'escapat de Django; els llegits es desen al servidor. El lector de canals no es fa servir |
| Solape | **Encavalcaments entre calendaris** (és el que diu el nom): llegeix dos `.ics` de debò (línies plegades, zones horàries, repeticions amb excepcions) en una agenda per dies, un to per calendari; el que es trepitja es cus amb una ziga-zaga taronja i va a una llista de xocs; «Moure a les 10:30» o «Ometre aquesta vegada»; comptador amb segell ✓; «Exportar .ics unit» | 1287 (JS + CSS) | Els calendaris són del club (activitats, sessions d'instructors, embarcació i material) i els xocs els calcula el servidor. No s'importa cap calendari personal d'un soci. L'exportació `.ics` es genera al servidor amb el permís de qui la demana |
| Baliza | **Marques de novetats, no notificacions:** unes balizes bateguen al costat del que és nou i obren una nota ancorada amb fletxa; «Entès» les apaga; una píndola compta el que s'ha descobert i la seva llista porta a cada baliza; «Amagar consells» les envia a la píndola i queda recordat al `localStorage` | 783 (JS + CSS) | El batec continu xoca amb D20: es fa un sol batec en aparèixer. Al navegador només es recorda quines novetats s'han vist (identificadors, sense dades personals). Lloc: [P-98](../decisions/pendents.md) |

### 2.1 Còpia dels quatre últims
Copiats a `design/extern/` sense cap canvi, amb el nom original. SHA-256 (iguals als de `design/Extern` de la carpeta principal):

| Fitxer | SHA-256 |
|---|---|
| `moxen-convite.zip` | `3b0149b0a081b59de63cbc468c175fc8a2e09acfec4c987eba1de65b0097a779` |
| `moxen-teletipo.zip` | `db6d025fb677d1661d2385ae00312f29bb917a5110b463c907e12ccfd65433aa` |
| `moxen-solape.zip` | `632fba2e666328caa53a3ead315c6d4f8d8db3115754b6abe5d7e391a230ad01` |
| `moxen-baliza.zip` | `35d924537fc52ebee8e15467ab18a46f8a322586825d016d2a988539444124e7` |

## 3. Encaix tècnic (regles comunes)

1. **Sense dependències noves.** Tots els recursos són JavaScript sense biblioteques. Si una adaptació en demanés una, és `risc:alt` i passa pel propietari. L'única prevista és el reconeixement de veu per al dictat d'Amanuense, instal·lat al servidor de la UE (P-95), que espera els xats.
2. **Res de fora de la UE ni de cap CDN** (035, 046). Fora les fonts de Google i de Fontshare: es fa servir la tipografia de `static/css/fonts.css`. El canvi de tipus de lletra és l'única diferència visual buscada.
3. **CSS:** cada full del recurs passa a `static/css/<recurs>.css`. Les seves variables de color, mida, radi, ombra i durada se substitueixen per tokens de `tokens.css` (si en falta un, s'afegeix primer al sistema de disseny). Cap `style=` a les plantilles: els valors que calcula el servidor van amb `<meter>`, `<progress>`, atributs d'SVG o classes per tram; els que calcula el JavaScript (posicions d'arrossegament) van amb `element.style.setProperty` sobre una variable CSS.
4. **JavaScript:** `static/js/<recurs>.js`, carregat amb `defer` i sense guions en línia (excepte el del tema al `<head>`, que ja existeix). La pantalla funciona sense JavaScript; el JavaScript l'anima. Els estats animats es basen en classes amb nom (B4), també `htmx-added` i `htmx-settling`.
5. **Càlculs al servidor.** Dies que queden, estats de pagament, imports, trams, encavalcaments i validacions es calculen al servidor. Del JavaScript dels recursos es treu tot el que simula el temps o el negoci (lliscadors de temps, rellotges de cuina, veus d'exemple, «Renovar»).
6. **Emmagatzematge al navegador:** només preferències (tema) i referències sense dades personals (activitats guardades d'un no soci). Mai dades personals ni esborranys de formularis (P-96).
7. **Fitxers:** validació pel contingut amb `core.validate_upload` i eliminació de l'EXIF al servidor, encara que el navegador ja ho faci. Emmagatzematge a Scaleway (París).
8. **Textos:** tots traduïbles (061). Els textos d'ajuda i les preguntes freqüents són dades editables.
9. **Moviment:** els tokens de [§15.4](../design-system.md#154-tokens-que-concreten-les-regles) del sistema de disseny; res bloqueja més de 400 ms i tot es pot interrompre.

## 4. Mapa

**Llegenda.** Fase 1 = mòduls 00, 01, 04, 05a i 05b; fase 2 = la resta. «Secció aprovada»: sí per a 01, 02, 03, 04, 05a, 05b, 06 i 09; la 00 es regeix per `specs/00-base-comuna/spec.md` fins que tingui secció; no per a 07, 08, 10, 11 i 12. La 02 està aprovada però **aparcada** (D6). Tots els fluxos tenen els estats d'error, d'accés denegat (403) i de sessió caducada de §6.3 del sistema de disseny; la columna de seguretat només diu el que és propi del recurs.

| Recurs | On el vols | Altres llocs que proposo | Mòdul · fase | Secció aprovada | Seguretat i privacitat del flux | Configurable des de l'app |
|---|---|---|---|---|---|---|
| Solapas | Pestanyes de l'administració | — | 00 · 1 | spec 00 | Cada pestanya torna a demanar la fitxa al servidor amb el permís per rol i objecte; un permís retirat tanca la pestanya amb «accés denegat». Títols de pestanya amb el número de soci, no el nom | — |
| Reasigna | Calendari de l'administració | Sessions d'un instructor que falta (02) | 02 · 2 | sí (aparcada) | Només qui gestiona activitats; l'instructor només veu les seves sessions. Reassignar avisa els afectats i queda al registre | Marge d'hora (± 30 min, ± 1 h) |
| Autentico | Validar pagaments, socis, sol·licituds | **Verificació del carnet** (`card_verify`, ja funcional). Per *aprovar* (altes, sol·licituds, pagaments a revisar) proposo el panell de revisió de Deposito, perquè Autentico verifica i no aprova. Proposta: codi de verificació al rebut (cal regla nova, D1) | 01 · 1 | sí | Pàgina pública declarada, amb limitació de peticions (T-M01-20). Diu el mateix que ara (RN-M01-26): si és vàlid, el número de soci i el nom de pila; si no, cap dada. El segell no hi afegeix cap dada | — |
| Cartola | Dates dels pagaments | Tresoreria: càrrecs pendents i retornats per antiguitat (proposta, el pla no té aquesta pantalla) | 05b · 1 | sí (pantalla: proposta) | Només tresoreria (T1). Exportació amb permís i registre; sense IBAN | Trams de dies |
| Averia | Publicar sortides i activitats | **Comunicar una avaria del material** (03), que és el seu ús literal | 02, 03 · 2 | sí (02 aparcada) | Publicar demana permís d'activitats. Fotos sense EXIF i sense persones identificables sense consentiment | Preguntes per tipus d'activitat o d'equip |
| Antefirma | Signatures de la junta i del club | — | fora de mòdul · 2 | no | Només dades de càrrec i de contacte del club (cris@cris.es), mai el telèfon personal si la persona no ho vol | Plantilles i colors (tokens) |
| Vigencia | Temps per renovar llicències i quotes | Confirmació en bloc de caducitats (T-M01-36) | 01 · 1; 06 · 2 | sí | El soci només veu les seves; el compte enrere surt de l'estat del servidor (070, P-71), mai del rellotge del navegador | Dies d'avís (30, 15, 7) |
| Horario | Calendari general, també per als socis | Avís d'encavalcament en apuntar-se | 02 · 2 | sí (aparcada) | El soci veu les activitats publicades i les seves inscripcions; no veu qui més hi va si no ho permet la 02 | Vista per defecte (setmana o mes) |
| Ramillete | Qualsevol pestanya petita | **Barra de navegació de l'àrea del soci** (inferior al mòbil, lateral a l'escriptori), amb l'acció principal (pagar la quota pendent o el carnet) | 00, 01 · 1 | sí | Menú construït al servidor per permisos; amagar no és un control | Acció principal per defecte |
| Emisor | Semblant a factures aprovades | Estètica del rebut (segell) a la 05b ara; factures a la 09 | 05b · 1; 09 · 2 | sí | Factura amb NIF validat; sense IBAN; els registres econòmics no s'esborren (058) | Dades fiscals del club |
| Deposito | Transferències | Panell de revisió per aprovar altes i sol·licituds (vegeu Autentico) | 04, 05b · 1 | sí (comprovant: proposta) | Soci: només la seva referència. Tresorer: confirmar o rebutjar amb motiu, que el soci llegeix. El comprovant és privat (fitxers privats) i mai no mostra cap IBAN del soci | Dades del compte del club |
| Tramite | La part de pagament | Pagament de convidat (enllaç segur, 021) | 05b · 1 | sí | Estat del servidor; mai «pagat» pel navegador. Convidat: només el seu càrrec | — |
| Marcador | Guardar activitats (socis i no socis) | Butlletí: «avisa'm quan s'obri» | 02, 07 · 2 | 02 sí (aparcada); 07 no | No soci: sense compte i sense dades personals al navegador | — |
| Oleaje | Lloc destacat de l'àrea del soci i de la web pública | Substitueix l'ona de la portada del soci (032) | 01 · 1; 07 · 2 | 01 sí; 07 no | Cap dada a la capa animada | Activar o desactivar |
| Eclipse | Canvi clar/fosc discret | Web pública i àrea del soci | 00 · 1 | spec 00 | — | Tema per defecte del club |
| Duermevela | Canvi clar/fosc amb transició | Motor de tema de tota la plataforma | 00 · 1 | spec 00 | Al `localStorage` només la preferència | Tema per defecte del club |
| Vistazo | Galeria de projectes amb fotos | Departament d'Història (11) | 07 · 2 | no | Fotos amb consentiment | Projectes i fotos com a dades |
| Recoveco | Preguntes freqüents | Ajuda de l'àrea del soci i de l'administració | 07 · 2 | no | Cap resposta no revela dades d'un compte | Preguntes i respostes |
| Apoderado | Verificacions i firmes | Proposta: confirmar la lectura d'avisos de la junta i acceptar textos legals (01); autoritzacions d'activitat (02) | 01 · 1; 02 · 2 | sí | Cada confirmació guarda la versió del text, el canal i l'hora (T-M01-08); cap dada de salut | — |
| Gastos | Finances: ingressos, costos i benefici per àmbit | Moviments per centre de cost (04) | 09 · 2 | sí | Només tresoreria i junta; marge = ingressos − despeses − cost de material | Àmbits (centres de cost) |
| Comanda | Apuntar-se a sortides i cursos | Opcions d'una inscripció (lloguer de material, «tria'n una») | 02 · 2 | sí (aparcada) | Validació al servidor; cap dada de salut a les opcions | Opcions i regles per activitat |
| Avisador | Permisos «veure» i «veure i editar» | Preferències de notificacions (amb Baliza) | 00 · 1 | spec 00 | Només l'administrador, amb TOTP, nota, resum dels afectats i registre; mai sense cap administrador operatiu (059) | És l'editor mateix |
| Asueto | Calendari d'un dia | Dies de tancament del local | 02 · 2 | sí (aparcada) | Moure una activitat avisa els inscrits | Horari del local |
| Camilla | Pagaments o apuntar-se | Proposta: flux d'inscripció per passos (P-94) | 02 · 2 | sí (aparcada) | Fora qualsevol camp de salut; convidat amb enllaç segur | — |
| Errata | Camp que falta o amb error | Tots els formularis | 00 · 1 | spec 00 | Missatges que no revelen l'existència de comptes | Textos d'ajuda |
| Pregon | Editor de la web i publicar posts | Vista prèvia en compartir una activitat | 07 · 2 | no | Publicar demana permís; imatges amb consentiment | Textos i imatges |
| Convite | Entrar a una activitat amb les fotos del lloc; després, mapa 3D | Capçalera de la fitxa d'una activitat (data, places que queden, «M'hi apunto» que obre Camilla, afegir al calendari) i de les conferències de l'11; les fotos del lloc, amb Fototeca i Expositor; el mapa 3D, més endavant (12) | 02, 11 · 2; 12 · després | 02 sí (aparcada); 11 i 12 no | Places que queden sense dir qui hi va; l'`.ics` no porta dades de cap persona; fotos amb consentiment i ubicació del lloc, mai la de les persones | Recordatori per defecte |
| Teletipo | Xats | Carcassa dels xats: converses per activitat i generals, entre administradors i socis (P-97) | 10 · després | no | Una conversa d'activitat només la veuen els inscrits i qui la gestiona; un missatge no s'obre fora de la conversa; text escapat, sense HTML ni rastrejadors | — |
| Amanuense | Xats | Caixó d'escriure dels xats, sense veu (P-95); dictat a la bitàcola (12) quan hi hagi el reconeixement al servidor de la UE | 10, 12 · després | no | Mai cap reconeixement de veu de fora de la UE. Amb veu, l'àudio no es desa: només el text, i el soci el revisa abans d'enviar | — |
| Solape | Calendaris | Xocs del calendari de l'administració (sessions d'un instructor, embarcació, material); exportar el calendari del club en `.ics` | 02 · 2 | sí (aparcada) | Només qui gestiona activitats veu els xocs de tots; l'instructor, els seus. L'`.ics` exportat només porta activitats que el compte pot veure | Tons per calendari (tokens) |
| Baliza | Notificacions | Novetats: quan una pantalla deixa d'estar «En construcció», una baliza ho diu una sola vegada. La píndola amb comptador i la seva llista, com a centre de notificacions (P-98, recomanació C) | 00 · 1 (estructura) | spec 00 | Una notificació no mostra dades d'una altra persona; al navegador només els identificadors de les novetats vistes | Preferències (Avisador) |
| Parrilla | Dashboard configurable | — | 08 · 2 | no | Cap dada personal (regla del dashboard) | Ginys per compte |
| Probador | Configurar la web sense codi | — | 07 · 2 | no | Només qui edita la web | Plantilla i color |
| Fototeca | Pujar i compartir fotos (fauna) | — | 12 · després | no | EXIF fora; persones amb consentiment | Carpetes i etiquetes |
| Expositor | Pujar i compartir fotos | Fotos d'una activitat o d'un projecte | 12 · després; 07 · 2 | no | Com Fototeca | Mida mínima |
| Monograma | Ajuda dels avatars de fauna marina | Avatar per defecte del soci, a partir de la llavor | 01 · 1; 12 · després | 01 sí; 12 no | A partir de `avatar_seed`, mai del nom | Paleta (tokens) |
| Seguir | Part social | — | 12 · després | no | Opcional; perfils privats per defecte | — |
| Desfile | Web pública i socis: projectes i sortides | Properes sortides a l'àrea del soci | 07 · 2 | no | Fotos amb consentiment | Avanç automàtic (apagat) |

## 5. Conflictes i com es resolen

| Conflicte | Resolució |
|---|---|
| D6 Remove embellishments contra Oleaje i la cortina de Duermevela | Cada efecte ha de tenir una funció escrita: Oleaje marca el canvi de secció (jerarquia); la cortina diu d'on ve el canvi de tema (estat i tacte). Si no en té, no es fa. Tots dos respecten `prefers-reduced-motion` (canvi instantani) |
| Oleaje contra la bateria del mòbil | Animació lenta, només mentre la secció es veu (`IntersectionObserver`), aturada amb la pestanya amagada (`visibilitychange`), desactivable a Ajustos i aturada amb `prefers-reduced-motion` |
| Radis fixos contra radis concèntrics | `tokens.css` ja porta l'escala 6/10/16/22 px pensada per encaixar; s'hi afegeix la variable calculada `--r-interior` (§15.4). §4 del sistema de disseny deia 4/8/12 i ja no coincidia: es corregeix |
| Vigencia contra les regles de renovació | Renovació als 12 mesos del pagament confirmat (070) i tres respostes a «està al corrent?» (P-71). El compte enrere és un valor del servidor; el navegador només el pinta. Sense «Renovar» al navegador |
| Avatars de fauna contra D11 Show the actual product | Un avatar és un identificador, no una il·lustració del producte: es permet. Els estats buits i les portades continuen amb dades de la demostració o fotos del club |
| B10 Exaggerated feedback en pagar contra no donar per fet un pagament pel navegador | La celebració només surt quan el servidor respon «pagat» (notificació verificada); mai en tornar del proveïdor |
| Fotos (Convite, Fototeca, Expositor) contra el RGPD | Persones identificables només amb consentiment (T-M01-08), cap dada de salut, EXIF fora al servidor, emmagatzematge a París. Cal la resposta de P-41 (drets d'imatge) abans de fer-les funcionals |
| Fonts de Google i Fontshare contra 035 i 046 | Fora; tipografia local de `fonts.css` |
| D7 Mono only where needed contra els imports en JetBrains Mono (`.import`) | Els imports passen a la lletra de text amb `tabular-nums`; el monoespai queda per al número de soci, la referència de transferència i el número de rebut |
| D18 Add loading states contra D20 (només Oleaje és contínua) | Els esquelets són estàtics, sense brillantor que es mogui. El progrés continu (B6) sí que pot moure's |
| Moviment de la 032 (entrada de 700 ms, gir de 600 ms) contra B9 | No bloquegen cap acció, però B9 demana panells de 200–300 ms: l'entrada passa a 300 ms i el gir a 400 ms. L'ona de la 032 la substitueix Oleaje |
| Desfile (avanç automàtic) contra D20 | Avanç manual per defecte; l'automàtic és un ajust apagat i, si s'encén, té el botó Pausa del recurs |
| Autentico calcula l'HMAC amb la clau al navegador | La clau és un secret: es calcula al servidor |
| Emisor desa empreses al `localStorage` | Es desen al servidor, amb permís |
| Camilla és una clínica | Fora especialitats i dades de pacient; cap dada de salut |
| Monograma fa l'avatar a partir del nom | A partir de `avatar_seed` (RN-M01-30) |
| Amanuense envia la veu fora de la UE | Resolt (P-95): sense veu; el dictat, només amb un reconeixement al servidor de la UE |
| Baliza batega sense parar, contra D20 i D1 (Delete filler badges) | Un sol batec en aparèixer; la nota diu què ha canviat (informa, no decora) i desapareix en veure-la |
| Teletipo i Baliza desen estat al `localStorage` | Teletipo: els llegits, al servidor. Baliza: només identificadors de novetats |
| Convite «La meva hora» | Fora: totes les activitats són en hora local |
| Solape llegeix `.ics` de qualsevol origen | No s'importa cap calendari personal; només calendaris del club |
| Avisador «Solo lo importante» i «Restaurar» als permisos | Són canvis de permisos com qualsevol altre: passen pel resum dels afectats, la nota i el TOTP |
| Recoveco fa servir `⌘F` | `Ctrl+F` (i `⌘F` al Mac); la cerca general és `Ctrl+K` (B19) |

## 6. Pantalles de la interfície sencera

«Funcional» = té codi; «En construcció» = només visual (§1); «En part» = l'etiqueta només al bloc que no és funcional. Estat a 16/11/2026, segons `docs/estat/`.

### 6.1 Estructura comuna (00)
| Pantalla | Estat | Recursos |
|---|---|---|
| Navegació de l'administració (barra lateral i pestanyes) | En part: el menú és funcional; les pestanyes són de la fase 2 d'aquest pla | Solapas |
| Navegació de l'àrea del soci | Funcional | Ramillete |
| Selector de tema | Funcional | Duermevela, Eclipse |
| Errors de formulari | Funcional (tots els formularis) | Errata |
| Notificacions i novetats | En construcció | Baliza |
| 403, 404, 500 i sessió caducada | Funcional | — |
| Etiqueta «En construcció» | Peça nova | — |

### 6.2 Comptes i accés (funcionals)
Entrar, codi de doble factor, seguretat del compte, verificar el correu, canviar el correu, invitació, recuperar la contrasenya, codis de recuperació, canvi de contrasenya temporal: **Errata**.

### 6.3 Àrea del soci
| Pantalla | Estat | Recursos |
|---|---|---|
| Inici i perfil | Funcional | Oleaje, Vigencia, Monograma |
| Quotes i detall d'una quota | Funcional | Vigencia |
| Pagar un càrrec, targeta i Bizum | Funcional (Bizum: T-M05b-04, PR #38) | Tramite |
| Pagar per transferència | En part: referència (T-M04-10, PR #41) funcional quan es fusioni; comprovant en construcció (proposta) | Deposito |
| Rebut | Funcional | Tramite, Emisor (segell) |
| Carnet | Funcional | — |
| Fer-se soci, canvi de tipus, baixa, esborrar les dades, exportar, consentiments, textos legals | Funcional | Errata; Apoderado (P-91: avisos i textos legals) |
| Calendari | En construcció | Horario, Solape |
| Activitats, inscripció i les meves inscripcions | En construcció | Camilla, Comanda, Marcador, Desfile |
| Fotos | En construcció | Fototeca, Expositor, Convite |
| Xats | En construcció | Teletipo, Amanuense |
| Social i avatars de fauna | En construcció | Seguir, Monograma |
| Notificacions i preferències | En construcció | Baliza, Avisador |
| Ajuda | En construcció | Recoveco |

### 6.4 Administració
| Pantalla | Estat | Recursos |
|---|---|---|
| Inici de l'administració | Funcional | Solapas |
| Socis: llistat, fitxa, editar, data d'alta, restablir el doble factor | Funcional | Solapas, Errata |
| Altes pendents, alta presencial, sol·licituds | Funcional | Deposito (panell de revisió), Errata |
| Llicències: registre i confirmació en bloc | Funcional | Vigencia |
| Importació de Cluber | Funcional | Errata, esquelet (B17) |
| Comptes d'administrador i restabliment | Funcional | Solapas |
| Rols i permisos | En construcció (T-RP-02 en curs, T-RP-03 per fer) | Avisador |
| Ajustos | En construcció (T-AJ-02 per fer) | Avisador |
| Registre d'activitat, RGPD, dades bloquejades, enllaços de convidat | Funcional | Solapas |
| Extracte bancari | Funcional | esquelet i desfer (B17, B19) |
| Tresoreria: comptes, saldos i moviments | Funcional | vores emmascarades (C2) |
| Transferències per revisar | En construcció (T-M04-12) | Deposito |
| Pagaments a revisar | En construcció (T-M05b-16) | Deposito |
| Pendents per antiguitat | En construcció (proposta) | Cartola |
| Remeses, retornats i devolucions | En construcció (05b) | Tramite, Cartola |
| Calendari, dia concret i reassignar | En construcció | Horario, Asueto, Reasigna, Solape |
| Activitats: publicar | En construcció | Averia, Pregon |
| Material: avaries | En construcció | Averia |
| Finances per àmbit, despeses i factures | En construcció | Gastos, Emisor |
| Dashboard | En construcció | Parrilla |
| Web: editor i configuració | En construcció | Probador, Pregon |
| Xats i fotos | En construcció | Teletipo, Amanuense, Fototeca, Expositor |
| Signatures de correu | En construcció | Antefirma |

### 6.5 Web pública
| Pantalla | Estat | Recursos |
|---|---|---|
| Verificació del carnet | Funcional | Autentico |
| Pagament de convidat | Funcional | Tramite |
| Portada | En construcció | Oleaje, Desfile, Eclipse |
| Projectes | En construcció | Vistazo, Desfile |
| Sortides i cursos, una activitat | En construcció | Marcador, Camilla, Comanda, Convite |
| Preguntes freqüents | En construcció | Recoveco |
| Butlletí | En construcció | Marcador |

## 7. Ordre proposat per a la fase 2

Una tasca = un recurs en un lloc, menys de 400 línies de codi d'aplicació, peça primer al sistema de disseny (document i CSS) i després a la plantilla. Identificadors `T-DX-NN` (disseny extern). Quan s'aprovi, la llista va a `docs/estat/DX.md` perquè la faci el pilot.

**Bloc A: estructura comuna**
1. T-DX-01 Tokens de moviment i radis (§15.4: durades, corbes, escala de premut, `--r-interior`).
2. T-DX-02 Paleta OKLCH amb alternativa, vores amb transparència i profunditat del tema fosc; contrastos tornats a comprovar.
3. T-DX-03 Etiqueta «En construcció», l'ajust `SHOW_UNDER_CONSTRUCTION` i la prova comuna «només lectura».
4. T-DX-04 Duermevela: motor de tema (substitueix `tema.js`).
5. T-DX-05 Eclipse: control de tema a la web pública i a l'àrea del soci.
6. T-DX-06 Errata: resum d'errors, començant pel formulari «Fer-se soci».
7. T-DX-07 Solapas a l'administració.
8. T-DX-08 Ramillete: navegació de l'àrea del soci.
9. T-DX-09 Baliza: novetats i notificacions (segons P-98), en construcció.

**Bloc B: pantalles funcionals de la fase 1**
10. T-DX-10 Tramite: estat del pagament (càrrec, targeta, Bizum).
11. T-DX-11 Tramite i Emisor: el rebut.
12. T-DX-12 Deposito: pagar per transferència (després de la PR #41); el comprovant, en construcció.
13. T-DX-13 Vigencia: quota i llicència a l'àrea del soci.
14. T-DX-14 Vigencia: llicències a l'administració.
15. T-DX-15 Autentico: verificació del carnet.
16. T-DX-16 Deposito: panell de revisió a altes pendents i sol·licituds.
17. T-DX-17 Oleaje: portada de l'àrea del soci.
18. T-DX-18 Monograma: avatar per defecte a partir de la llavor.
19. T-DX-19 Avisador: rols i permisos, en construcció fins a la T-RP-03.
20. T-DX-20 Avisador: ajustos, en construcció fins a la T-AJ-02.
21. T-DX-21 Cartola: pendents per antiguitat, en construcció.
22. T-DX-22 Deposito: transferències i pagaments a revisar, en construcció fins a la T-M04-12 i la T-M05b-16.

**Bloc C: pantalles en construcció dels mòduls que falten** (una tasca per pantalla, en aquest ordre: primer el que veu el soci)
T-DX-23 Calendari general (Horario, després Solape). T-DX-24 Activitats i inscripció (Camilla i Comanda, P-94). T-DX-25 Marcador. T-DX-26 Desfile i Oleaje a la portada pública. T-DX-27 Vistazo: projectes. T-DX-28 Recoveco: ajuda i preguntes freqüents. T-DX-29 Calendari d'un dia (Asueto). T-DX-30 Reasigna. T-DX-31 Publicar activitats (Averia i Pregon). T-DX-32 Avaries del material (Averia). T-DX-33 Finances per àmbit (Gastos). T-DX-34 Factures (Emisor). T-DX-35 Dashboard (Parrilla). T-DX-36 Editor de la web (Probador i Pregon). T-DX-37 Fotos (Fototeca i Expositor). T-DX-38 Convite (segons P-99). T-DX-39 Xats (Teletipo segons P-97; Amanuense com a caixó d'escriure, sense veu). T-DX-40 Social (Seguir i Monograma de fauna). T-DX-41 Signatures (Antefirma). T-DX-42 Apoderado (P-91).

## 8. Dubtes

**Resolts pel propietari el 16/11/2026** (a [`pendents.md`](../decisions/pendents.md)):
- **P-90** Pantalles «En construcció» a producció: **C**, un permís propi que l'administrador assigna per rol, mai als socis ni a la web pública. Sense assignar, no les veu ningú.
- **P-91** Apoderado: **A**, avisos i textos legals a l'àrea del soci; autoritzacions d'activitat a la 02.
- **P-92** Antefirma: **A**, eina de signatures de correu de l'administració.
- **P-93** Emisor: **C**, el segell al rebut ara i les factures a la 09.
- **P-94** Camilla és el flux d'inscripció i Comanda les opcions (**A**).
- **P-95** Amanuense: sense veu, com a caixó d'escriure dels xats. El dictat, quan es facin els xats, amb un reconeixement de veu instal·lat al servidor de la UE (dependència nova, `risc:alt`, amb el sí del propietari). Mai el de Google ni cap altre de fora de la UE.
- **P-96** Solapas: **B**, la llista de pestanyes (identificador i número, sense noms) a `sessionStorage` i el contingut només a la pàgina.

**Oberts** (a [`pendents.md`](../decisions/pendents.md) i al [tauler](../decisions/tauler-preguntes.yml), amb opcions A a D i la recomanació):
- **P-97** Teletipo no és un xat. Per defecte, la seva carcassa per als xats.
- **P-98** Baliza no són notificacions. Per defecte, novetats i la píndola com a centre de notificacions.
- **P-99** Convite no té fotos ni mapa. Per defecte, la capçalera de la fitxa d'una activitat.
