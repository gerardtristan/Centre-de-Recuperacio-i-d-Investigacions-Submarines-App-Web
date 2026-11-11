# Sistema de disseny — Plataforma C.R.I.S.

- **Versió:** 1.6 (11/11/2026). La 1.6 descriu la navegació comuna tal com és a la plataforma (T-M01-46): la barra lateral de l'administració, el botó «Menú» i «Surt» (§6 i §6.1). No canvia cap token.
- La 1.5 (03/11/2026) afegeix els wireframes del mòdul 01 (T-M01-02): les pantalles de §5.2, els components del prototip interactiu que ja existien i ara es documenten (§6), la navegació de Socis amb la configuració inicial de la [059](decisions/059-rols-i-permisos-editables.md) (§6.2) i els patrons d'interacció i de seguretat de §6.7. No canvia cap token ni cap regla.
- La 1.4 (27/10/2026) incorpora patrons de Magic Portfolio com a referència visual (decisió 034): una sortida destacada a la portada, projectes, notícies i conferències, una galeria, el butlletí i l'afinament de les targetes i els xips dels socis (§5.1, §6.6 i §10).
- La 1.3 fixa el nom del club, fa més petit el selector de tema i compacta el compte personal (§4).
- **Versió anterior:** 1.2, etapa 3: sistema de disseny i wireframes de baixa fidelitat.
  - La 1.1 afegeix l'estil neumòrfic limitat (§6.4) i el selector de tema segmentat (§7).
  - La 1.2 afegeix l'estructura d'immersió del compte personal (§6.5), els tokens de profunditat, carnet i moviment (§2.6 i §4.1), el logotip més gran a la pública i la secció `centre-recuperacio-investigacio`.
- **Decisions:** [030](decisions/030-sistema-de-disseny.md) (substitueix la 009), ampliada per la [031](decisions/031-estil-neumorfic-limitat.md), per la [032](decisions/032-immersio-socis-i-centre.md) i per la [034](decisions/034-patrons-magic-portfolio.md).
- **Fitxers:** `static/css/tokens.css` (font de veritat dels valors, una sola còpia que fan servir la plataforma i els prototips des de la T-M01-38), `static/css/fonts.css` (fonts allotjades al servidor; llicència a `static/fonts/README.md`) i els prototips `design/wireframes/publica.html`, `socis.html`, `admin.html` i `comptes.html`.
- **Abast:** estructura i regles. **No és el disseny final.** No hi ha l'editor (etapa 4). L'únic moviment és el del compte personal (§4.1).

## 1. Principis
1. Tres zones amb la mateixa identitat i estructura diferent: **pública** (escriptori primer), **compte personal** (mòbil primer) i **administració** (escriptori primer, densa).
2. Es veu de seguida en quina zona ets: el color de la zona marca la capçalera, l'etiqueta de secció i els detalls.
3. Cap valor de disseny directe als components: tot surt de variables CSS (tokens) i té valor als dos temes.
4. Els estats es llegeixen sense color: sempre hi ha **símbol + text + color**.
5. Mòbil, tauleta i escriptori són tres disposicions pensades per separat, no una sola que s'estira.

## 2. Tokens de color
> **Atenció (detectat a la T-M01-02):** `tokens.css` porta la paleta revisada el 31/10/2026 (primitius `--abisme`, `--boira`, `--pissarra`, `--posidonia`, `--llauto`…), que el mateix fitxer diu que està «pendent de registrar com a decisió». Els valors d'aquesta secció són els de la 1.4 i ja no coincideixen amb els del fitxer. Mentre no hi hagi decisió, la font de veritat és `tokens.css`, i les comprovacions de contrast de la 1.5 (§6.7) s'han fet amb els seus valors [A validar: decisió de la paleta].

Els noms són en català, sense accents (vegeu §11). Cada color de zona i d'estat té tres tokens: el **decoratiu** (vores, punts, barres), el de **text** (text, etiquetes, enllaços) i el **fons tenyit**.

### 2.1 Superfícies, text i accions
| Token | Rol | Clar | Fosc |
|---|---|---|---|
| `--c-fons` | Fons de pàgina | `#f2f5f8` | `#08131e` |
| `--c-superficie` / `--c-superficie-2` | Targetes / zones secundàries | `#ffffff` / `#f7f9fb` | `#0f1f2f` / `#132638` |
| `--c-text` / `--c-text-2` | Text principal / secundari | `#0f1c2a` / `#566676` | `#e4edf5` / `#93a7b9` |
| `--c-linia` | Línies separadores | `#dbe3ea` | `#22384d` |
| `--c-linia-forta` | Vores de camps i botons (3:1) | `#7a8b9b` | `#5a7590` |
| `--c-enllac`, `--c-focus` | Enllaços, informació i focus | `#0b5f8f` | `#74c4ea` |
| `--c-accent` (`--c-accent-text`) | Acció principal i element actiu | `#f5c43a` (`#3d2e00`) | `#f5c43a` (`#2b2000`) |
| `--c-caixa` / `--c-caixa-text` | Caixes grises dels wireframes | `#e3e8ed` / `#566676` | `#1b3044` / `#93a7b9` |

### 2.2 Barra lateral (fosca als dos temes)
| Token | Clar | Fosc |
|---|---|---|
| `--c-lateral-fons` / `--c-lateral-fons-2` | `#062a47` / `#0b3a5e` | `#04101b` / `#0b2236` |
| `--c-lateral-text` / `--c-lateral-text-2` | `#cfe0ee` / `#8fb0c9` | `#cfe0ee` / `#7f9db5` |
| `--c-lateral-zona` (segons la zona) | admin `#8fb2ec`, soci `#e2b04f`, pública `#4cc3d3` | igual |
| `--c-lateral-focus` | `#f5c43a` | `#f5c43a` |

Com que la barra és fosca als dos temes, el color de zona i el focus que hi van a sobre fan servir **sempre els valors del tema fosc**.

### 2.3 Zones i estats
| Rol | Clar: decoratiu → text · fons | Fosc: decoratiu = text · fons |
|---|---|---|
| Zona pública (`--c-publica`) | `#0f8496` → `#0b6f7e` · `#e2f4f6` | `#4cc3d3` · `#0f3139` |
| Zona soci (`--c-soci`) | `#9a6b12` → `#85590a` · `#fbf1da` | `#e2b04f` · `#33270e` |
| Zona admin (`--c-admin`) | `#2a4f86` → `#2a4f86` · `#e5ecf7` | `#8fb2ec` · `#18294a` |
| Correcte (`--c-ok`) | `#1b8a5e` → `#157049` · `#e1f3ea` | `#55c995` · `#0f3123` |
| Avís (`--c-avis`) | `#a8650d` → `#8f5409` · `#fcefd9` | `#f0b056` · `#36260b` |
| Error (`--c-error`) | `#c0392f` → `#a8322a` · `#fbe5e2` | `#f2857b` · `#3a1714` |
| Informació (`--c-info`) | `#0b5f8f` · `#e3eff7` | `#74c4ea` · `#0f2c40` |
| Sistema (`--c-sistema`) | `#6b5aa8` · `#ece9f7` | `#b3a6ef` · `#231e3d` |

**Ajustos lleugers respecte a la paleta fixada:**
- `--c-error-text` clar `#a8322a`. Amb `#c0392f` sobre el fons tenyit d'error, el contrast queda just a 4,5:1 i qualsevol arrodoniment el fa baixar.
- `--c-linia-forta` és un token nou. Les vores dels camps i dels botons han de tenir un contrast de 3:1 (WCAG 1.4.11), i `--c-linia` no hi arriba.
- Els fons tenyits i les superfícies de la barra lateral (`-fons`, `--c-lateral-fons-2`) són els de `design/mapa-plataforma.html`.

### 2.4 Regla de les fletxes (comprovada)
Al tema clar, el primer valor serveix per a **fons, vores, punts i detalls decoratius** (3:1, n'hi ha prou) i el segon, més fosc, per a **text i enllaços** (4,5:1). Contrast calculat sobre `#ffffff` i sobre `#f2f5f8`:

| Primer valor | Sobre blanc | Sobre `#f2f5f8` | Segon valor | Sobre `#f2f5f8` |
|---|---|---|---|---|
| `#0f8496` | 4,4:1 ✕ | 4,0:1 ✕ | `#0b6f7e` | 5,3:1 ✓ |
| `#9a6b12` | 4,7:1 | 4,3:1 ✕ | `#85590a` | ≥ 5:1 ✓ |
| `#1b8a5e` | 4,35:1 ✕ | 4,0:1 ✕ | `#157049` | ≥ 5:1 ✓ |
| `#a8650d` | 4,6:1 | 4,3:1 ✕ | `#8f5409` | ≥ 5:1 ✓ |

La interpretació és correcta i és la que apliquen els tokens. Falta que la validi el club [A validar] (decisió 030). Abans de fer el disseny final caldrà una revisió de contrast amb eina (checklist B8).

### 2.5 Ús dels colors
- **Zona:** color de la capçalera (vora inferior), de l'etiqueta de secció, de la vora de les targetes destacades i del fons de l'element actiu. Cada pàgina posa `zona-publica`, `zona-soci` o `zona-admin` al `<body>`, i això defineix `--c-zona`, `--c-zona-text`, `--c-zona-fons` i `--c-lateral-zona`.
- **Groc (accent):** només per a l'acció principal d'una vista (botó `boto-principal`) i per a la barra de l'element actiu. El text que hi va a sobre és `--c-accent-text`.
- **Element actiu:** **barra groga de 3 px + negreta + fons de zona**. Al tema clar, el groc com a vora dona uns 1,6:1, i per això mai indica l'element actiu tot sol.
- **Estats:** sempre amb símbol i text (§6.3). «Sistema» es fa servir per als missatges automàtics (notificacions verificades, recordatoris, avisos previs).

### 2.6 Profunditat i carnet (compte personal, decisió 032)
El compte personal fa servir la metàfora d'una immersió: la portada és la superfície i la pàgina es fa més fonda a mesura que es baixa.

| Token | Clar | Fosc | Ús |
|---|---|---|---|
| `--c-ocea-1` a `--c-ocea-4` | `#e2f4f6` → `#c4e6ee` → `#a6d6e3` → `#8cc7d8` | `#0f3a4a` → `#0c2c40` → `#0a1f33` → `#08131e` | Degradats per profunditat: portada (1→2), ona (3), resta de la pàgina (3→4) |
| `--c-ocea-text` / `--c-ocea-text-2` | `#0f1c2a` / `#2f4152` | `#e4edf5` / `#a9bccc` | Text sobre els degradats (≥9,2:1 i ≥5,6:1 en totes les parades) |
| `--c-carnet-1` / `--c-carnet-2` | `#0b4f74` / `#062a47` | igual | Carnet: sempre fosc, com una targeta física |
| `--c-carnet-text` / `--c-carnet-text-2` | `#f2f5f8` / `#b9cfe0` | igual | Text del carnet (≥8:1 i ≥5,5:1) |
| `--c-carnet-zona` | `#e2b04f` | igual | Franja superior del carnet i anell del dock. **Decoratiu**: 4,4:1, no es fa servir per a text |

Al tema clar, el color de text de la zona soci (`#85590a`) baixa a 3,3:1 a la part fonda del degradat. Per això, a la portada les etiquetes fan servir `--c-ocea-text-2`.

## 3. Tipografia
Igual als dos temes.

| Ús | Família | Pesos | Token |
|---|---|---|---|
| Títols | Barlow Condensed | 600, 700 | `--f-titol` |
| Text | Source Sans 3 | 400, 600, 700 | `--f-text` |
| Codis: número de soci, referències (per exemple, `SRT-2026-014`, el codi d'una sortida), identificadors de material (`MAT-0112`), noms d'usuari d'administració, imports de taula i hores | JetBrains Mono | 400, 500 | `--f-codi` |

Alternatives del sistema (si no hi ha connexió): Arial Narrow o Arial; Segoe UI o system-ui; ui-monospace, Menlo o Consolas.

**Escala** (base 16 px): `--t-xs` 12 (només etiquetes en majúscules), `--t-s` 14, `--t-m` 16, `--t-l` 20, `--t-xl` 24, `--t-2xl` 32, `--t-3xl` 44. Alçada de línia: 1,5 al text i 1,1 als títols.

**Allotjament:** als wireframes, les fonts es carreguen de Google Fonts. **En producció s'han d'allotjar a `assets/fonts/` amb la llicència documentada** [A validar]. Totes tres són, segons consta, de llicència SIL Open Font License 1.1; cal comprovar-ho i desar el fitxer `OFL.txt` de cada família al costat de les fonts. Allotjar-les nosaltres també evita enviar l'adreça IP dels visitants a Google (RGPD).

**Risc que continua obert (1.5):** els tres wireframes carreguen les fonts de Google Fonts. Les pantalles del mòdul 01 són dins d'aquests tres fitxers i comparteixen aquella càrrega: no se n'ha afegit cap de nova. Fins que les fonts s'allotgin a `assets/fonts/`, qui obre un wireframe connectat a internet envia la seva adreça IP a Google; sense connexió, es veuen les alternatives del sistema.

## 4. Espaiat, formes i mides
- **Espaiat:** `--e-1` a `--e-8` = 4, 8, 12, 16, 24, 32, 48 i 64 px. No se'n fan servir d'altres.
- **Radis:** `--r-s` 4, `--r-m` 8, `--r-l` 12 i `--r-pastilla` (forma de pastilla).
- **Vores:** `--v-fina` 1 px; `--v-activa` 3 px (element actiu i vora de zona); `--v-focus` 3 px; `--v-plena` 2 px (peces neumòrfiques amb més contrast).
- **Avatar:** `--avatar` 56 px.
- **Tàctil:** `--tactil` 44 px. És l'alçada i l'amplada mínimes de tot element que es pot prémer, a totes les mides.
- **Estructura:** `--amplada-max` 1200 px, `--lateral-ample` 240 px (administració), `--lateral-carril` 72 px (tauleta, administració), `--capcalera-alcada` 64 px. `--lateral-soci`, `--columna-dreta` i `--barra-inferior-alcada` són de l'estructura anterior dels socis; ara no es fan servir, però es conserven fins que es validi la nova.
- **Logotip:** `--logo-capcalera` 40 px (socis i administració), `--logo-publica-mobil` 52 px i `--logo-publica` 72 px (capçalera pública), `--logo-peu` 120 px (peu de la pública).
- **Selector de tema:** `--selector-alcada` 32 px (alçada visible de cada opció), `--selector-opcio` 40 px (amplada mínima visible), `--selector-icona` 12 px (icones i ✓), text de 14 px a partir de tauleta i farciment del contenidor de 2 px. L'àrea tàctil continua sent de **44 × 44 px**: un pseudoelement invisible de l'etiqueta l'amplia 6 px amunt i avall i 2 px a cada costat, sense que es vegi més gran. La vora (`--c-linia-forta` o `--neu-vora`, ≥3:1), el focus i la llegenda «Tema» no canvien.
- **Compte personal:** `--portada-alcada` 64svh (alçada mínima de la portada **a partir de tauleta**; al mòbil, la portada fa l'alçada del contingut), `--carnet-amplada` 22rem (×1,25 a l'escriptori), `--carnet-proporcio` 1,586 (la d'una targeta física), `--dock-alcada` 64 px, `--dock-carnet` 60 px, `--tactil-gran` 56 px (accions crítiques: pagar), `--carril-targeta` 85 % (targetes del carril al mòbil) i `--ona-alcada` 32 px.
- **Espai vertical del compte personal (1.3):**

  | Lloc | Abans | Ara |
  |---|---|---|
  | Farciment superior de la portada | 32 px | 16 px al mòbil; 24 px a partir de tauleta |
  | Farciment inferior de la portada | ona + 32 px | ona + 12 px |
  | Ona | 48 px | 32 px |
  | Alçada mínima de la portada | 90svh | la del contingut al mòbil; 64svh a partir de tauleta |
  | Marge entre l'ona i la franja de pagaments | 24 px | 12 px |
  | Espai entre els blocs de la portada | 24 px | 16 px |
  | Espai entre els blocs de sota i marge superior de la graella | 24 px | 16 px |
  | Farciment inferior de la pàgina | 48 px | 32 px |
  | Salutació | avatar a sobre del nom; títol de 44 px | avatar al costat del nom; títol de 32 px al mòbil i de 44 px a partir de tauleta |

  El carnet manté la mida i la proporció. Al mòbil de 390 × 844 px, la franja de pagaments ja es veu sense desplaçar la pàgina, fins i tot amb les barres de demostració del wireframe.

### 4.1 Moviment (decisió 032)
Només a tres llocs del compte personal i mai en accions crítiques:

| Token | Valor | On |
|---|---|---|
| `--m-entrada` | 700 ms | Entrada de la portada (apareix i puja 24 px), una sola vegada |
| `--m-gir` | 600 ms | Gir del carnet |
| `--m-ona` × `--m-ona-repeticions` | 2,4 s × 2 | Ona de la portada. S'atura sola abans de 5 s, així que no cal cap botó de pausa (WCAG 2.2.2) |
| `--m-rapid` | 150 ms | Reserva per a transicions petites; encara no es fa servir |
| `--m-corba` | `cubic-bezier(.2, .7, .2, 1)` | Corba comuna |

Amb `prefers-reduced-motion: reduce` (l'usuari demana menys moviment al sistema), els tokens passen a 0 i `tokens.css` atura qualsevol animació i transició. La portada apareix directament, l'ona queda quieta i el carnet es gira a l'instant.

## 5. Punts de canvi
| Nom | Amplada | Consulta CSS |
|---|---|---|
| Mòbil | fins a 599 px | base, sense consulta |
| Tauleta | 600 a 1023 px | `@media (min-width: 600px)` |
| Escriptori | 1024 px o més | `@media (min-width: 1024px)` |

El CSS s'escriu de mòbil a escriptori a les tres zones, encara que la pública i l'administració estiguin **pensades** primer per a escriptori. Les variables CSS no es poden fer servir dins de `@media`, i per això aquests dos valors són els únics números directes que es permeten.

### 5.1 Com canvia cada bloc
**Pública (`publica.html`)**
| Bloc | Mòbil | Tauleta | Escriptori |
|---|---|---|---|
| `capcalera` (sobre el fons de pàgina; amb el nom sencer al costat del logotip, mai l'abreviatura) | Logotip de 52 px i el nom en 3 línies de 12 px, selector de tema només amb icones i botó ☰ de menú (hamburguesa, s'obre amb un clic) | Dues files: logotip de 72 px i el nom en 2 línies de 14 px, selector amb text i «Fes-te soci»; a sota, la pastilla de navegació centrada, amb 3 enllaços i «Més» (El Centre, Projectes, Notícies i conferències, Medi ambient, Galeria, Fer-se soci, Contacte, Àrea de socis) | Dues files: logotip de 72 px i el nom en 2 línies de 14 px, selector, «Àrea de socis» i «Fes-te soci»; a sota, la pastilla amb 6 enllaços (Inici, Activitats, Qui som, El Centre, Projectes, Notícies) i «Més» (Medi ambient, Galeria, Fer-se soci, Contacte) |
| `portada` | Text i, a sota, la **sortida destacada** (targeta amb imatge, data, lloc, estat i enllaç); una sola acció principal | Igual | 2 columnes (7/5), amb el titular ×1,3 |
| `properes-activitats` | 1 columna de targetes | 2 columnes | 3 columnes |
| `qui-som`, `medi-ambient` | Text i, a sota, la imatge | Igual, xifres en 3 columnes | 2 columnes; la imatge canvia de costat |
| `centre-recuperacio-investigacio` (entre `qui-som` i `medi-ambient`) | Introducció, 3 àmbits un a sota de l'altre (Recuperació, Investigació, Divulgació) i una crida a col·laborar | Àmbits en 3 columnes; crida amb el botó a la dreta | Igual que la tauleta. Tot el text és d'exemple i va marcat [A validar] |
| `projectes` (després del Centre) | Targetes tipus memòria una a sota de l'altra: xips, títol, **Objectiu / Dades / Resultats** i enllaç | 2 columnes | 2 columnes |
| `noticies` (després de `medi-ambient`) | Llista d'entrades: la data a l'esquerra (dia gran i mes), un xip de tipus, el títol enllaçat i un resum | Igual, amb una columna de data més ampla | Igual |
| `galeria` | Columnes tipus maçoneria: 2, amb peu de foto (lloc i any); espais reservats | 3 columnes | 4 columnes |
| `fer-se-soci` | Text, avís de pagament i botó, sense preus (els preus són al formulari `#alta`, des del 03/11/2026) | Igual | Igual |
| `contacte` | Dades i, a sota, el formulari | 2 columnes | 2 columnes |
| `peu` (amb `butlleti` a dalt) | Butlletí (correu, consentiment, botó «Subscriu-me») i, a sota, 1 columna; logotip de 120 px | Butlletí en 2 columnes; peu en 2 columnes | Igual; peu en 4 columnes |

Les seccions alternen el fons en aquest ordre: portada, properes activitats (alternat), qui som, el Centre (alternat), projectes, medi ambient (alternat), notícies, galeria (alternat), fer-se soci i contacte (alternat).

**Compte personal (`socis.html`, estructura d'immersió, §6.5)**
| Bloc | Mòbil | Tauleta | Escriptori |
|---|---|---|---|
| `capcalera-soci` + `navegacio-soci` | Logotip i selector de tema a dalt; navegació en un **dock flotant** a baix (Inici, Sortides, **Carnet** al centre i més gran, Pagaments, Perfil) | Sense barra lateral: logotip i selector a la primera fila, i a sota la navegació en text | Una sola fila: logotip, navegació i selector |
| `portada` (amb `salutacio` i `carnet`) | Gairebé tota la pantalla: avatar, salutació i carnet gran, un a sota de l'altre; ona a baix | Igual, centrat | 2 columnes: salutació a l'esquerra, carnet a la dreta (×1,25) |
| `franja-estat` | Franja plana a tota l'amplada, amb el botó a sota | Botó a la dreta | Igual que la tauleta |
| `avisos`, `proximes-activitats`, `bitacola`, `llicencia` | Una columna, en aquest ordre (els avisos primer, perquè són crítics) | Bento de 2 columnes: avisos i llicència; carril a tota l'amplada; bitàcola a tota l'amplada | **Bento asimètrica** de 12 columnes: carril (8) i avisos (4); bitàcola (7) i llicència (5) |
| Carril de `proximes-activitats` | Una targeta del 85 % i un tros de la següent; scroll-snap horitzontal | 2 targetes visibles | 2 targetes visibles dins de les 8 columnes |

Canvis d'id respecte a la 1.1: `pagaments-pendents` passa a `franja-estat` (el detall de cada pagament anirà a la pantalla de Pagaments). Es mantenen `salutacio`, `carnet`, `proximes-activitats`, `llicencia` i `avisos`, i són nous `portada` i `bitacola`.

**Administració (`admin.html`, fitxa d'una sortida)**
| Bloc | Mòbil (llegible) | Tauleta (utilitzable) | Escriptori |
|---|---|---|---|
| `barra-lateral` | Amagada; «Menú» l'obre com a panell sencer | Carril fosc de 72 px | Barra fosca de 240 px |
| `capcalera-fitxa` | Dades en 2 columnes; accions dins de «Accions» | Accions visibles a la dreta | Dades en una fila |
| `resum-economic` | 2×2 | 2×2 | 4 xifres en una fila |
| `participants` | Cada fila és un bloc apilat amb etiquetes | Taula sense Mètode ni Llicència | Taula sencera (8 de 12 columnes) |
| `material-assignat`, `activitat-recent` | A sota | A sota | Columna dreta (4 de 12 columnes) |
| `programa-i-notes` | 1 columna | 2 columnes | 2 columnes, amplada sencera |

### 5.2 Pantalles del mòdul 01 (T-M01-02)
S'obren amb l'adreça. A la pública i al compte personal, amaguen la portada; a l'administració, són vistes de Socis i accepten el rol a l'adreça (`#vista&rol=…`). La correspondència amb els processos és a `docs/planning.md`, M01-5.

| Pantalla | Fitxer i adreça | Mòbil | Escriptori |
|---|---|---|---|
| Sol·licitud d'alta | `publica.html#alta` | Formulari en una columna i «Què passa després» a sota | Formulari (7) i columna lateral fixa (5) |
| Verificació del carnet | `publica.html#verificar` | Una targeta amb el resultat | Igual, amb l'amplada d'un text |
| Llistat de socis | `admin.html#vista-socis-llistat` | Cada fila és un bloc amb etiquetes | Taula sencera |
| Fitxa del soci | `admin.html#vista-socis-fitxa` | Capçalera i pestanyes (Dades, Historial, Quotes, Llicència) | Igual, dades en dues columnes |
| Sol·licituds | `admin.html#vista-socis-sollicituds` | Pestanyes (Altes, Canvis de tipus, Baixes) i una targeta per sol·licitud | Targetes en dues columnes |
| Alta presencial | `admin.html#vista-socis-alta` | Formulari en una columna | Formulari (7) i notes (5) |
| Quotes i impagats | `admin.html#vista-socis-quotes` | Generació a dalt; taula en blocs | Xifres en una fila i taula sencera |
| Importació de Cluber | `admin.html#vista-socis-cluber` | Fitxer, importació final i resultat, un a sota de l'altre | Fitxer (7) i importació final (5); resultat a tota l'amplada |
| El meu perfil | `socis.html#perfil` | Una columna | Dades (7) i, al costat, consentiments, llicència, sol·licituds i dades (5) |
| Canvi a ple dret, baixa, esborrar el compte | `socis.html#canvi-tipus`, `#baixa`, `#esborrar` | Una columna | Columna estreta centrada |
| No trobat | `socis.html#no-trobat` | Una targeta | Igual |

Les pantalles del compte personal són planes, com pagar i els avisos (§6.5): sense degradat, ona ni moviment.

## 6. Components
Tots són a `tokens.css` (components compartits) o a l'estil de cada pàgina (estructura). Classes en català.

| Component | Classe | Regles |
|---|---|---|
| Botó | `boto`, `boto-principal`, `boto-text`, `boto-petit` | Mínim 44 × 44 px. Un sol `boto-principal` per vista o bloc. Els desactivats porten `aria-disabled` i vora discontínua |
| Selector de tema | `selector-tema` (+ `neu-selector` a la pública i als socis; + `selector-lateral` a la barra fosca de l'administració) | Control segmentat amb botons de ràdio; vegeu §7 |
| Avatar | `avatar` (+ `neu-anell` només sobre `--c-fons`; + `avatar-portada` sobre el degradat) | Inicials en Barlow Condensed 700 i `--c-text`; és decoratiu (`aria-hidden`), perquè el nom ja hi és en text |
| Carnet giratori | `carnet-giratori`, `cara-davant`, `cara-darrere` | Vegeu §6.5 |
| Dock | `navegacio-soci`, `dock-carnet` | Només al mòbil; vegeu §6.5 |
| Franja d'estat | `franja-estat` (+ `franja-ok`) | Plana, sense efectes; vegeu §6.5 |
| Carril | `carril` | Scroll-snap horitzontal, es pot enfocar amb el teclat (`tabindex="0"`) |
| Insígnia | `insignia` (+ `insignia-pendent`) | Sempre amb text d'estat («✓ Aconseguida» o «◌ Falten N») |
| Peces neumòrfiques | `neu-relleu`, `neu-selector`, `neu-pastilla`, `neu-anell` | Només als llocs de §6.4 |
| Targeta | `targeta` | Superfície, vora i radi gran |
| Etiqueta de secció | `etiqueta-seccio` | Majúscules de 12 px en el color de text de la zona |
| Estat | `estat` + `estat-ok`, `estat-avis`, `estat-error`, `estat-info`, `estat-sistema`, `estat-neutre` | Símbol (`aria-hidden`) + text + color + vora |
| Avís | `avis` + `avis-ok`, `avis-avis`, `avis-error`, `avis-sistema` | Barra a l'esquerra i títol en negreta |
| Xip | `xip` | Tipus d'element (Sortida, Curs) |
| Caixa d'imatge | `caixa-imatge` | Substitueix qualsevol imatge als wireframes |
| Camp | `camp`, `casella` | Etiqueta sempre visible; mínim 44 px |
| Codi i import | `codi`, `import` | JetBrains Mono; xifres tabulars als imports |
| Marca pendent | `a-validar` | Senyala les dades o decisions [A validar] dins de les pantalles |
| Demostració | `demo` | Només als wireframes: simula una persona o un rol |
| Nota de servidor (1.5) | `demo nota-servidor` | Només als wireframes. Diu quins controls s'apliquen al servidor; no forma part de la pantalla i separa la simulació (amagar per rol) del control real |
| Barra lateral de l'administració (1.6) | `barra-lateral`, `lateral-nav`, `lateral-compte`, `lateral-estat`; el `<body>` porta `amb-barra-lateral` | A `comptes.css`. Fosca als dos temes (`--c-lateral-*`). Les entrades les posa el servidor segons els permisos; vegeu §6.1 |
| Botó «Menú» (1.6) | `boto boto-petit boto-menu` | Només per sota de 1024 px i amb JavaScript. `aria-expanded` i `aria-controls="barra-lateral"`; vegeu §6.1 |
| «Surt» (1.6) | `boto boto-petit` dins d'un formulari | Sempre un POST amb CSRF, mai un enllaç. Un sol text a tot arreu: «Surt» |

**Components del prototip interactiu (ja existien des del 31/10/2026; es documenten a la 1.5 perquè les pantalles del mòdul 01 els reutilitzen).** Són a `tokens.css` i `interaccions.js` (JavaScript propi, sense dependències ni CDN, decisió 046).

| Component | Classe i funció | Regles |
|---|---|---|
| Diàleg | `dialeg` (`dialeg-cap`, `dialeg-cos`, `dialeg-peu`), `<dialog>` natiu amb `showModal()` | Reté el focus i es tanca amb Esc o amb el botó «Tanca» (`aria-label`). En obrir-lo, el focus va al primer camp; en tancar-lo, torna al botó que l'ha obert. Accions a baix: «Torna» o «Cancel·la» i l'acció principal |
| Botó dinàmic | `boto-dinamic`, `CRIS.botoDinamic(boto)` | Canvia de text i d'icona («Desant…», «Desat») sense salts d'amplada; mentre treballa porta `aria-busy` i `aria-disabled`. El resultat també s'anuncia en text |
| Interruptor | `interruptor` amb `role="switch"` i `aria-checked` | Estat amb posició, icona i text «Sí» o «No», mai només color. Nom amb `aria-labelledby` |
| Pestanyes | `pestanyes`, `pestanya`, `panells`; `CRIS.pestanyes(llista)` | Patró ARIA de pestanyes: fletxes, Inici i Fi; subratllat elàstic daurat. Una pestanya que el rol no pot veure no surt |
| Control segmentat | `segmentat` | Botons de ràdio dins d'un `fieldset` amb llegenda; l'opció triada porta ✓, negreta i relleu |
| Zona per pujar fitxers | `zona-magnetica`, `CRIS.zonaMagnetica(zona)` | També amb clic o Intro. Comprova el tipus i la mida i mostra l'error en text. Amb `data-csv`, resumeix el fitxer com un extracte bancari (per això la importació de Cluber no el fa servir) |
| Regió viva | `anunci`, `CRIS.anuncia(text)` | Anuncia els canvis d'estat al lector de pantalla |

`boto-tactil`, `impressora` i el subratllat de la navegació encara no tenen fila: no els fa servir cap pantalla nova [A completar].

### 6.1 Navegació
- Pública: barra superior en forma de pastilla. Al mòbil, una hamburguesa que s'obre i es tanca amb un clic o amb Esc. **Regla (034):** la pastilla no s'allarga. A l'escriptori mostra 6 enllaços i «Més», i les seccions noves van dins de «Més». Els enllaços que surten de «Més» només a l'escriptori porten la classe `nav-escriptori`, i les seves còpies dins de «Més», `nav-no-escriptori`. Així cada enllaç només es veu i es llegeix una vegada a cada mida.
- Compte personal: dock flotant al mòbil (Inici, Sortides, Carnet, Pagaments, Perfil, amb el carnet al centre) i navegació a la capçalera a partir de la tauleta. No té barra lateral, i així es distingeix de l'administració.
- Administració: barra lateral fosca amb els mòduls Socis, Activitats, Material, Tresoreria, Pagaments, Llicències, Web i Dashboard, **filtrada per rol** (§6.2).
- Element actiu: `aria-current="page"`, barra groga, negreta i fons (§2.5).

**Navegació a la plataforma (1.6, T-M01-46).** És la del wireframe `admin.html`, amb aquestes precisions:
- **Entrades.** Una per pantalla que existeix, no per mòdul: Inici, Llistat de socis, Altes pendents, Alta presencial, Sol·licituds de socis, Llicències pendents de confirmar, Quotes i impagats, Importació de Cluber, Comptes d'administrador i Registre d'activitat. Quan hi hagi més mòduls, s'agruparan com al wireframe.
- **Filtrada al servidor.** Una entrada només arriba a l'HTML si el compte té el permís que la ruta declara (`apps/members/permissions.py` i `apps/accounts/navigation.py`); no s'amaga amb CSS. No és cap control: cada vista torna a comprovar el permís.
- **Compte.** Sota les entrades: el nom d'usuari del compte actiu (`codi`), «Compte d'administrador · TOTP actiu» i «Surt» (formulari POST amb CSRF). Cap altra dada.
- **Escriptori (1024 px o més).** Columna fixa de `--lateral-ample`, sota la capçalera. El botó «Menú» no hi és.
- **Mòbil i tauleta (fins a 1023 px).** La barra va sota la capçalera, a tota l'amplada, plegada darrere del botó «☰ Menú». El botó l'obre i la tanca (Intro o Espai); Esc la tanca i torna el focus al botó. No tapa la pàgina ni reté el focus: l'ordre del tabulador és el de la pantalla (logotip, «Menú», tema, entrades, «Surt», contingut). Sense JavaScript, la barra es veu sempre oberta.
- **Diferències amb el wireframe, pendents:** el carril de 72 px amb icones de la tauleta (la plataforma encara no té el joc d'icones; de 600 a 1023 px es comporta com el mòbil) i el selector de tema dins del panell (a la plataforma n'hi ha un de sol, a la capçalera).
- **Entrada actual:** `aria-current="page"`, barra daurada (`--v-activa`, `--c-accent`), negreta i fons `--c-lateral-fons-2`; també quan s'és en una pantalla que en penja (la fitxa d'un soci marca «Llistat de socis»).
- **Contrast** (calculat amb els valors de `tokens.css`, clar i fosc): text de les entrades sobre la barra, 6,7:1 i 7,4:1; entrada actual sobre el seu fons, 7,9:1 i 9,2:1; focus daurat sobre la barra, 10:1 o més.
- **Compte personal.** Navegació en text a la capçalera (el dock és de la portada, pendent). «Surt» és l'última peça de la llista, com a botó petit, a totes les pantalles de l'àrea.

### 6.2 Menús i blocs per rol
**Socis (1.5):** segueix la configuració inicial de la [059](decisions/059-rols-i-permisos-editables.md) ([matriu](planning.md#rols-i-permisos-059-matriu)). El selector «Veure com» porta els onze rols de gestió de la 059.

| Pantalla de Socis | Rols que la veuen |
|---|---|
| Llistat i fitxa (P4) | Administrador i Secretaria, amb totes les dades; Tresorer en consulta, amb les dades mínimes per cobrar |
| Sol·licituds (P3a, P3, P7) | Administrador, Secretaria, Tresorer i President. El Tresorer i el President no veuen la data de naixement ni el document (C1, C2) |
| Alta presencial (P2) | Administrador i Secretaria |
| Quotes i impagats (P8, P9, P10) | Administrador i Tresorer generen; només el Tresorer marca impagats; la Secretaria consulta l'estat sense imports |
| Importació de Cluber (P18) | Administrador |

La barra lateral obre a cada rol la primera pantalla de Socis que pot veure (al President, Sol·licituds).

**Resta de mòduls (matriu provisional, P-04, pendent d'adaptar a la 059).** Surt de la spec 00, §2.4 i §2.5, i l'avís del selector ho diu. Amb els rols nous de la 059 (President, Junta, Resp. comunicació i Resp. botiga), aquestes pantalles mostren «Sense accés a aquesta pantalla» fins que s'adaptin. La vista «Permisos per rol» encara diu «059 no trobada» i té la matriu antiga: s'actualitzarà amb la T-RP-03.

| Mòdul del menú | Rols que el veuen |
|---|---|
| Socis | Administrador, Secretaria, Tresorer (consulta) |
| Activitats | Administrador, Resp. cursos i sortides, Resp. material (consulta), Tresorer (consulta), Instructor (les seves sessions), Dept. Història (conferències) |
| Material | Administrador, Resp. material, Resp. cursos (assignar), Instructor i Tresorer (consulta) |
| Tresoreria, Pagaments | Administrador, Tresorer. Pagaments: [A validar], perquè la matriu no té cap fila per a aquest mòdul |
| Llicències | Administrador, Secretaria, Resp. cursos i Tresorer (consulta) |
| Web | Administrador, Dept. Història [A validar] (contingut històric) |
| Dashboard | Tots excepte l'instructor (parcial o complet) |

A la fitxa d'una sortida:
- **Marge** (`resum-economic`): l'administrador, el responsable de cursos i el tresorer.
- **Participants:** els mateixos més l'instructor, però l'instructor no veu les columnes d'Import ni de Mètode.
- **Material:** tots els que tenen accés a la fitxa; l'instructor no en veu el cost.
- **Activitat recent:** l'administrador, el responsable de cursos i el tresorer [A validar] (M6).
- **Secretaria i Dept. Història:** veuen «Sense accés a aquesta fitxa».
- **Resp. material:** no veu ni els participants ni els diners [A validar].

### 6.3 Estats
| Estat | Símbol | Classe |
|---|---|---|
| Pagat, Vigent, Inscripció confirmada, Places lliures, Lliurat | ✓ | `estat-ok` |
| Pendent, Per recollir | ◷ | `estat-avis` |
| Estat del soci (M01): «Pendent de la primera quota» (`pending`), «Actiu», «Impagat», «Impagat · quota pagada, revisa-ho» (el tresorer encara no l'ha desmarcat; 040) i «Baixa» | ◷, ✓, ✕, ✕, ■ | `estat-avis`, `estat-ok`, `estat-error`, `estat-error`, `estat-neutre` |
| Caduca aviat, Últimes places | ! | `estat-avis` |
| Cancel·lat, Completa, Sense llicència | ✕ | `estat-error` |
| Sistema (missatge automàtic) | ⚙ | `estat-sistema` |

### 6.4 Estil neumòrfic limitat (decisió 031)
El relleu tou (dues ombres, una de fosca i una de clara, del mateix to que el fons) és un detall d'identitat en molt pocs llocs. **No** és l'estil general.

**Tokens** (un joc per tema: les ombres es recalculen per a cada fons, no s'inverteixen):

| Token | Clar | Fosc | Ús |
|---|---|---|---|
| `--neu-superficie` | `#f2f5f8` | `#08131e` | Igual que `--c-fons`, el fons on es posen les peces |
| `--neu-ombra-fosca` | `#c3ced9` | `#01060b` | El mateix to, més fosc (a baix i a la dreta) |
| `--neu-ombra-clara` | `#ffffff` | `#15293d` | El mateix to, més clar (a dalt i a l'esquerra) |
| `--neu-vora` | `#7a8b9b` (3,2:1) | `#5a7590` (3,9:1) | Vora de cada peça, ≥3:1 sobre la superfície |
| `--neu-relleu`, `--neu-relleu-petit`, `--neu-enfonsat` | compostos | compostos | Ombra en relleu (4 px / 10 px), relleu petit (2 px / 5 px) i ombra interior |

**On sí:**
| Peça | Pàgina | Com |
|---|---|---|
| Selector de tema | `publica.html`, `socis.html` | Contenidor en relleu petit; l'opció activa porta **ombra interior + negreta + ✓** |
| Avatar (component `neu-anell`) | Disponible per a qualsevol avatar sobre `--c-fons` | Anell tou (relleu petit i ombra interior); inicials amb `--c-text` (15,7:1 i 15,8:1) |
| Carnet (component `neu-relleu`) | Disponible sobre `--c-fons` | Relleu suau i vora |

**Ajust de la 032:** a la nova portada dels socis, l'avatar i el carnet van sobre un degradat oceànic. La superfície ja no és igual que el fons, i per tant **ja no són neumòrfics**. L'avatar porta un anell pla del color de zona i el carnet és una targeta fosca amb degradat (§6.5). Als socis, l'únic element neumòrfic és el selector de tema.
| Pastilla de navegació | `publica.html`, de la tauleta en amunt | Contenidor en relleu petit; l'enllaç actiu porta **ombra interior + negreta + barra groga** i `aria-current`. Al mòbil, el menú desplegat és pla |

**On no:** `admin.html` (tot, inclòs el selector de tema, que hi és pla), taules, formularis i camps, avisos, estats, targetes generals, botons principals («Fes-te soci», «Paga ara», «Inscriu-t'hi»), barra lateral i barra inferior.

**Regles:**
- Les peces neumòrfiques només es posen sobre `--c-fons`. Per això, la capçalera de la pública i la del compte personal, `salutacio` i `carnet` van sobre el fons de pàgina i no dins de targetes blanques. Al tema clar, damunt de `#ffffff` no pot haver-hi cap ombra més clara que el fons, i l'efecte no funcionaria.
- Cada peça té vora `--neu-vora` (≥3:1), focus visible (`--c-focus`: 6,3:1 i 9,65:1) i text ≥4,5:1 (`--c-text-2` sobre la superfície: 5,4:1 i 7,6:1).
- **Cap estat s'indica només amb l'ombra:** l'element actiu sempre porta també negreta i una marca (✓ o la barra) i el seu estat a l'HTML (`checked` o `aria-current`). Les ombres tenen un contrast baix a propòsit (1,5:1 i 1,3:1) i són decoratives.
- **`prefers-contrast: more`** (l'usuari demana més contrast al sistema): les ombres desapareixen i passen a vora plena de 2 px en `--c-text`. L'opció activa del selector es mostra invertida (`--c-fons` sobre `--c-text`, 15,7:1) i l'enllaç actiu de la pastilla porta una barra en `--c-text`.
- En mode de colors forçats (alt contrast de Windows), el navegador treu les ombres i l'estat continua indicat per la ✓, la negreta i la barra.

### 6.5 Compte personal: estructura d'immersió (decisió 032)
**Regla principal:** el «wow» (degradats, ona, gir del carnet, insígnies) només és a les peces no crítiques. **Pagar i els avisos són sempre plans, grans i amb contrast ≥4,5:1**, sense degradat, ombra ni moviment.

- **Portada:** compacta (al mòbil fa l'alçada del contingut, i a partir de tauleta com a mínim el 64 % de l'alçada visible) i té un degradat de superfície (`--c-ocea-1` → `--c-ocea-2`). Hi ha l'avatar, la salutació i el carnet gran. A baix, una ona (SVG decoratiu, `aria-hidden`) marca l'inici de la profunditat.
- **Carnet giratori:**
  - Mida de targeta física (proporció 1,586), sempre fosc i amb la versió del logotip per a fons fosc.
  - Davant: nom, número de soci en JetBrains Mono 500 de 32 px (`--c-carnet-text`, 8:1 o més), validesa i estat «✓ Vigent».
  - Darrere: QR [A validar], tipus, data d'alta, quota i llicència.
  - Es gira amb un botó visible, «Mostra el darrere» o «Mostra el davant», amb `aria-pressed`. La cara amagada porta `aria-hidden`.
  - Sense moviment, el gir és instantani.
- **No soci:** en lloc del carnet, una invitació a fer-se soci (targeta plana amb les quotes, validades el 03/11/2026, i el botó principal «Fes-te soci»).
- **Franja d'estat:**
  - Plana, gran i a tota l'amplada, just sota la portada.
  - Amb pendents: «◷ N pagaments pendents», el detall i el botó «Paga ara» de 56 px d'alçada. El text fa 15,2:1 i 12,3:1, i el botó 8,1:1 i 9,8:1.
  - Sense pendents: «✓ Tot al dia» i un enllaç a l'historial.
  - Porta `role="status"`.
- **Properes sortides:** targetes grans en un carril horitzontal amb scroll-snap. El carril es pot enfocar i desplaçar amb el teclat, i una pista de text («Llisca per veure'n més») hi indica que n'hi ha més.
- **Bitàcola** [A validar: d'on surten les dades i si el club vol insígnies]: sortides de l'any, hores sota l'aigua i anys de soci, i insígnies per fites. Cada insígnia diu el seu estat en text («✓ Aconseguida», «◌ Falten 11»). No hi ha cap dada de salut.
- **Dock (mòbil):** flotant a baix, en forma de pastilla, amb el botó del carnet al centre (60 px, fosc amb anell de zona) que sobresurt. L'element actiu porta barra groga, negreta i fons de zona.
- **Escriptori:** sense barra lateral; capçalera superior i graella bento asimètrica (§5.1).
- **Més contrast:** desapareixen els degradats, l'ona i les ombres; el fons és pla i les vores plenes de 2 px en `--c-text`.

### 6.6 Patrons adoptats de Magic Portfolio (decisió 034)
- **Sortida destacada** (`destacada`): una targeta amb vora superior de zona, una imatge, l'etiqueta «Sortida destacada», el títol, la data i el lloc, els xips d'estat i un enllaç. Va a la portada, al costat del titular. La portada té una sola acció principal (groga) i un enllaç de text.
- **Memòria de projecte** (`projecte`, `memoria`): sempre amb tres apartats, **Objectiu, Dades i Resultats**. Les etiquetes van en majúscules de 12 px amb el color de text de la zona, i les xifres en Barlow Condensed. Les dades d'exemple porten la marca [A validar] o «Exemple».
- **Entrada amb data** (`entrada`): `<time datetime>` amb el dia gran i el mes en text, un xip de tipus («Notícia» o «Conferència»), el títol enllaçat i un resum. Les entrades van en una llista ordenada (`<ol>`), de la més nova a la més antiga.
- **Galeria** (`galeria`): columnes CSS tipus maçoneria, amb `figure` i `figcaption` (lloc i any). No hi va cap foto sense drets (P-41).
- **Butlletí** (`butlleti`): el correu amb etiqueta visible, una casella de consentiment amb enllaç a la privacitat i la baixa, el botó «Subscriu-me» i un avís de confirmació per correu (P-42). No és neumòrfic.
- **Compte personal (només afinament):**
  - targetes planes amb vora fina, radi gran i sense ombra (el relleu queda per al carnet);
  - farciment de 16 px al mòbil i de 24 px a partir de la tauleta;
  - xips en forma de pastilla;
  - el títol «Properes sortides» i el de cada sortida a 32 px, i la data i el lloc a 14 px.

  Aquests afinaments són a l'estil de `socis.html`, no a `tokens.css`, i així no arriben a l'administració.

### 6.7 Patrons d'interacció i de seguretat del mòdul 01 (1.5)
Les accions equivalents fan servir els mateixos noms, passos i respostes a les tres zones:
- **Aprovar i validar:** botó principal («Aprova l'alta», «Aprova el canvi», «Valida la baixa») que canvia a «Aprovant…» i deixa el resultat en text, amb el focus a sobre.
- **Rebutjar i accions amb motiu:** «Rebutja…», «Marca impagat…» i «Crea una baixa» obren un diàleg amb el motiu obligatori. Sense motiu, error a prop del camp i el focus hi torna.
- **Formularis:** etiqueta sempre visible, error a sota del camp (`aria-invalid` i `aria-describedby`), focus al primer camp amb error i recompte d'errors anunciat.
- **Confirmacions:** la baixa del soci es confirma en un diàleg; l'esborrat del compte, amb una casella explícita («Entenc que no es pot desfer»).
- **Acció irreversible a l'administració (T-M01-22, `/gestio/rgpd/`):** aprovar un esborrat RGPD demana, al mateix formulari, la casella explícita, la contrasenya i el codi TOTP de qui aprova (reautenticació a la mateixa petició). Abans del formulari, una llista «Què passarà en aprovar-la» amb frases sense imports ni dades personals. Rebutjar és un formulari a part amb el motiu obligatori. Si no es pot aprovar, un `avis avis-error` diu per què i el formulari d'aprovar no surt. Pantalles sense wireframe propi: només components existents (`taula`, `dades-soci`, `targeta`, `formulari`, `camp`, `casella`, `avis`, `accions`, `boto`).
- **Descàrrega de les dades pròpies (T-M01-22, perfil):** un botó prepara el fitxer i, un cop preparat, un enllaç amb aspecte de botó el descarrega; al costat, fins quan es pot descarregar i l'avís que conté dades personals.
- **Resultat que no es desa:** «La sessió ha caducat» i «Ja no tens permís per fer aquesta acció» diuen que no s'ha desat res i no mostren cap dada.
- **Missatges que no revelen dades:** el formulari d'alta respon igual si el document ja existeix; la verificació respon igual per a un testimoni desconegut, revocat o impagat, i el límit de peticions no diu el llindar.
- **Accés denegat:** a l'administració, les pantalles noves fan servir el patró existent «Sense accés a aquesta pantalla» quan el rol no hi té permís. «No s'ha trobat la pàgina» només on el pla ho exigeix: un soci que obre dades d'un altre (CA-M01-25). Si l'administració també ha de respondre «no trobat» per rol és una diferència per revisar [A validar].
- **Minimització:** el document surt emmascarat al compte personal; el Tresorer i el President veuen «major d'edat» en lloc de la data de naixement; cap llistat porta la data de naixement; la importació de Cluber mostra els errors per línia sense repetir dades del fitxer.
- **Simulació i servidor:** amagar un element per rol al prototip és una simulació. Cada pantalla porta una nota «Al servidor» amb el control real.

Contrast comprovat amb els valors de `tokens.css` als dos temes, en 27 combinacions per tema (resum al diari de la T-M01-02). Per sota del mínim: el daurat de la barra activa sobre el fons de zona al tema clar (1,16:1; és decoratiu i ara porta una vora fosca de 6,98:1) i la pista de l'interruptor actiu al tema fosc (1,64:1; component existent, amb l'estat també en text) [A completar: T-M01-28].

### 6.8 Impressió i carnet en PDF (decisió 079)
El carnet es desa com a PDF amb la impressió del navegador; el servidor no genera cap PDF.
- **`no-imprimeix`:** classe per a tot el que no ha de sortir al paper (avisos, botons, enllaços, formularis). La capçalera i l'enllaç «Vés al contingut» ja no s'imprimeixen mai.
- **`[data-imprimeix]`:** botó que obre la impressió («Desa com a PDF»). Surt amagat (`hidden`) i el mostra `static/js/imprimeix.js`; sense JavaScript es pot imprimir igualment des del navegador.
- **Tema:** mentre s'imprimeix, `imprimeix.js` força el tema clar i després torna a posar el que hi havia.
- **`carnet-qr`:** el QR del carnet (peça `qr`, §6) centrat amb la seva explicació a sota.
- Estils a `static/css/comptes.css` (`@media print`), no a `tokens.css`.

## 7. Temes clar i fosc
- Per defecte, la pàgina segueix `prefers-color-scheme`, la preferència de color del sistema operatiu.
- El **selector de tema** és un control segmentat de tres opcions, **Sistema / Clar / Fosc** (◐ ○ ●), fet amb botons de ràdio dins d'un `fieldset` amb la llegenda «Tema». Funciona amb el teclat (Tab i fletxes). Cada opció es veu de 32 px d'alt, però té una àrea tàctil de 44 × 44 px (§4). Als prototips, al mòbil només es veuen les icones (el text continua disponible per al lector de pantalla) i a partir de tauleta, la icona i el text. **A la plataforma (T-M01-45), la capçalera de comptes, socis i administració mostra la icona i el text a totes les mides**, com demana la revisió de pantalles; a 320 px el selector passa a la seva fila (`comptes.css`).
- Desa la tria a `localStorage` amb la clau `cris-tema` (`light` o `dark`); a «Sistema», la clau s'esborra. Si una pàgina té més d'un selector (l'administració en té un a la barra lateral del mòbil i un a la barra superior), tots dos queden sincronitzats.
- Un petit script al `<head>` aplica el tema desat abans de pintar la pàgina, perquè no es vegi el canvi. Si `localStorage` no està disponible, el selector funciona igual però no se'n recorda.
- El tema manual es fixa a `<html data-theme="light|dark">`. Els tokens foscos són dues vegades a `tokens.css`: una per a la preferència del sistema i una altra per al tema triat amb el selector.

## 8. Logotips
| On | Fitxer |
|---|---|
| Tema clar | `assets/marca/CRIS_SenseFons.png` (text i contorns negres, fons transparent) |
| Tema fosc | `assets/marca/CRIS_Blanc_per fons Negre (Blanc).png` (text i contorns blancs, fons transparent), directament sobre el fons fosc |
| Barra lateral (fosca als dos temes) i carnet de soci (sempre fosc) | La versió per a fons fosc (`logo-sempre-fosc`) |
| Versió amb fons blanc | `assets/marca/CRIS_AmbFons.jpg` (no es fa servir als wireframes) |

Comprovat sobre `#08131e` i sobre `#062a47`: els contorns i el text blancs es llegeixen bé i «DES DE 1954» manté el contorn blanc. El canvi es fa amb les classes `logo-clar` i `logo-fosc`.

**Nom del club:** «Centre de Recuperació i d'Investigacions Submarines» (C.R.I.S.). És el que fan servir els títols de pàgina, els textos i el text alternatiu dels logotips de les tres zones: «Logotip del C.R.I.S., Centre de Recuperació i d'Investigacions Submarines». Els logotips decoratius, com el del carnet, porten `alt=""`.

**Regla del text alternatiu del logotip:**
- Si el logotip va al costat del nom en text, com a la capçalera pública, porta `alt=""`. Així el lector de pantalla no llegeix el nom dues vegades.
- Si el logotip no hi va acompanyat, com al peu, a les capçaleres dels socis i a la barra de l'administració, porta el text alternatiu complet. És el nom oficial, en singular i amb «d'», com al logotip, la Viquipèdia, l'Enciclopèdia Catalana i cris.barcelona.

**Regla: la capçalera pública porta el nom sencer** al costat del logotip, mai l'abreviatura «C.R.I.S.». Va en Barlow Condensed 600:
- al mòbil, en 3 línies de 12 px («Centre de Recuperació» / «i d'Investigacions» / «Submarines»);
- a partir de tauleta, en 2 línies de 14 px.

El nom pot fer més línies si cal i no es talla mai: amb el text al 200 %, la capçalera passa a més files. Per fer-hi lloc al mòbil, l'espai entre el selector i el menú passa a 4 px, i les àrees tàctils continuen de 44 px. Les capçaleres dels socis i de l'administració no canvien.

**Mides (decisió 032):** a la web pública, el logotip fa 52 px a la capçalera del mòbil (la capçalera queda en uns 68 px d'alçada), 72 px a partir de la tauleta i 120 px al peu. A 72 px, el text circular comença a ser llegible a la pantalla de l'ordinador. Als socis i a l'administració es manté en 40 px.

Falta [A validar]:
- **Versió reduïda per a la capçalera del mòbil i per a la icona de la PWA** (només les ampolles i «CRIS», sense el text circular). A 40-48 px, el text circular del logotip no es llegeix en cap de les dues versions.
- **Versió vectorial (SVG)** de totes dues variants, per a una nitidesa perfecta i fitxers més petits. Els PNG actuals fan 2717 × 2900 px (de 350 a 510 kB), massa per a una capçalera.
- **Nom del fitxer** de la versió fosca: té espais i parèntesis. Als wireframes s'enllaça codificat (`%20`). Recomanació: reanomenar-lo (per exemple, `CRIS_SenseFons_Blanc.png`) quan el club ho aprovi.

## 9. Accessibilitat (mínims dels wireframes)
- Focus visible a tot arreu: contorn de 3 px de `--c-focus`, groc a la barra lateral.
- Objectius tàctils de 44 px com a mínim. Cap acció depèn de passar el ratolí per sobre: els menús i els desplegables s'obren amb un clic o amb el teclat.
- Estats mai només amb color (§6.3); els símbols porten `aria-hidden` i el text és el que es llegeix.
- Enllaç «Salta al contingut», `lang="ca"`, etiquetes visibles als camps, `caption` a la taula i `aria-live` al recompte de resultats i a la descripció del rol.
- `prefers-reduced-motion`: el moviment del compte personal (entrada, ona i gir) s'anul·la (§4.1). Cap informació depèn del moviment.
- L'ona dura menys de 5 s i s'atura sola (WCAG 2.2.2).
- `prefers-contrast: more`: les peces neumòrfiques passen a vores plenes (§6.4) i, al compte personal, desapareixen els degradats, l'ona i les ombres (§6.5).
- Accions crítiques (pagar i avisos): sempre planes, grans i amb contrast ≥4,5:1.
- En saltar a una secció de la pública, el títol no queda amagat sota la capçalera fixa (`scroll-margin-top`).
- Pendent: revisió WCAG 2.2 AA amb eina i lector de pantalla (checklist B8), quan es faci el disseny final.

## 10. Referències (només estructura, components i estil)
No se n'ha copiat codi, imatges, logotips ni textos. Tampoc no s'ha fet servir l'MCP de 21st.

| Referència | Zona | Què se n'ha agafat | Llicència |
|---|---|---|---|
| [Card Stack Portfolio](https://21st.dev/@kedhareswer/templates/card-stack-portfolio-website-template) (Kedhareswer Naidu) | Socis | Targetes grans i navegació persistent (aquí, el dock). El moviment del carnet és disseny propi, en CSS | No indica cap llicència [A validar si se'n volgués reutilitzar codi] |
| [Saasly](https://21st.dev/@tailgrids/templates/tailgrids-saasly) (TailGrids) | Admin i pública | Xifres en targetes, jerarquia neta, targetes de preu per a `fer-se-soci` (ja no s'usen: des del 03/11/2026 els preus només surten al formulari d'alta). Nota: és una pàgina de presentació, no un panell, i la barra lateral i la taula són disseny propi | Llicència TailGrids: ús comercial i en projectes de clients permès; **no** es pot revendre, redistribuir ni fer servir en generadors d'interfícies [A validar si se'n reutilitzés codi] |
| [Magic Portfolio](https://21st.dev/@larsen66/templates/magic-portfolio-for-next-js) (Once UI; once-ui.com/products/magic-portfolio) | Pública, i socis només en tipografia | Barra de navegació en forma de pastilla, botó de tema a la capçalera, etiquetes de secció i xips. Des de la 034, també: treball destacat (sortida destacada), casos d'estudi (memòries de projectes), entrades amb data (notícies i conferències), galeria, subscripció al butlletí i ritme tipogràfic. Anàlisi completa a [analisi-magic-portfolio.md](analisi-magic-portfolio.md) | **CC BY-NC 4.0**: cal citar l'autor i no se'n permet l'ús comercial. No en copiem codi, textos ni imatges; si mai se'n volgués reutilitzar codi, cal validar si l'ús del club és «no comercial» [A validar] |

**Nota d'atribució:** alguns patrons visuals de la web pública i del compte personal s'inspiren en *Magic Portfolio*, de Once UI (llicència CC BY-NC 4.0). N'agraïm el treball. No se n'ha copiat codi, textos ni imatges: els patrons s'han reimplementat en HTML i CSS propis, amb els tokens d'aquest sistema.

## 11. Convencions de noms
- Tokens: `--c-` color, `--e-` espai, `--t-` mida de text, `--p-` pes, `--a-` alçada de línia, `--r-` radi, `--v-` vora, `--f-` família.
- Classes, tokens i ids en **català sense accents** (`capcalera`, `boto-principal`, `pagaments-pendents`). Els ids dels blocs són estables i coincideixen amb els de l'encàrrec. [A validar] Cal confirmar que el codi del frontend seguirà la mateixa convenció (CLAUDE.md: «decidir-ho una vegada i no barrejar»).

## 12. Pila del frontend: idees que només es podrien fer amb React i Tailwind [A validar]
No s'han implementat i no es decideixen aquí:
- El retrat que segueix el punter de Card Stack (depèn del ratolí; no s'implementa). El gir del carnet i l'ona ja es fan amb CSS pur (§4.1), sense dependències.
- La instal·lació de components amb el CLI de shadcn o de 21st (React i Tailwind).
- Una llibreria de components reutilitzables com a font del sistema de disseny, en lloc d'aquest CSS amb tokens.

Si s'adopta React i Tailwind, els tokens d'aquest document es poden traslladar a la configuració del tema de Tailwind sense canviar-ne els valors.

## 13. Com provar els wireframes
1. Obrir `design/wireframes/publica.html`, `socis.html` o `admin.html` directament al navegador (no cal servidor).
2. **Tema:** triar Sistema, Clar o Fosc al selector de la capçalera (a `admin.html` al mòbil, dins de «Menú»). La tria es manté en recarregar i en canviar de pàgina. **Més contrast:** a les eines de desenvolupament, *Rendering → Emulate CSS media feature prefers-contrast: more*. Per provar el mode «Sistema», cal canviar el tema del sistema operatiu o, a les eines de desenvolupament, *Rendering → Emulate CSS media feature prefers-color-scheme*.
3. **Mides:** a les eines de desenvolupament (F12), activar el mode de dispositiu (Ctrl+Maj+M) i provar 390 px (mòbil), 820 px (tauleta) i 1440 px (escriptori).
4. **Demostració:** a `socis.html`, triar «Soci amb pagaments pendents», «Soci al dia» o «Persona no sòcia (alumne)», i prémer «Mostra el darrere» per girar el carnet. A `admin.html`, canviar «Veure com» per veure els menús i blocs de cada rol.
5. **Mòdul 01 (1.5):** `publica.html#alta` i `#verificar`; `admin.html#vista-socis-llistat&rol=tresorer` (qualsevol vista de §5.2 amb qualsevol rol de la 059); `socis.html#perfil`, `#canvi-tipus`, `#baixa`, `#esborrar` i `#no-trobat`. Cada pantalla té la seva franja «Demostració» (per exemple, sessió caducada, llistat buit o resultat de la verificació), i la importació de Cluber té un CSV d'exemple inventat.
6. **Marques de revisió:** el botó «Amaga les marques de revisió» de la franja del prototip amaga les etiquetes [A validar] i les notes «Al servidor» per veure la pantalla neta. Es manté en recarregar i en canviar de pàgina. Només amaga peces de demostració: no canvia cap control ni cap permís simulat.
7. **Reduir moviment:** a les eines de desenvolupament, *Rendering → Emulate CSS media feature prefers-reduced-motion: reduce*. Cal recarregar la pàgina per veure-hi la portada sense animació d'entrada.

## 14. Pendents [A validar]
- Que el club validi la paleta, la regla de les fletxes i els ajustos de §2.3.
- Matriu de permisos dels menús i blocs (P-04).
- Què inclou cada quota (els preus, 35 € simpatitzant i 90 € ple dret, els va validar el responsable del projecte el 03/11/2026), adreça i horari del local, i tipus de llicència.
- Si el carnet té codi QR i foto.
- El nom del departament de les sortides.
- Versions del logotip (reduïda i SVG) i nom del fitxer de la versió fosca (§8).
- Allotjament i llicència de les fonts (§3).
- Pila del frontend (§12) i convenció de noms del codi (§11).
- Compte personal (032): la bitàcola (d'on surten les sortides i les hores, i si el club vol insígnies) i el contingut del darrere del carnet.
- Web pública (032): els textos de `centre-recuperacio-investigacio`. El nom del club ja és fixat (§8).
- Fase futura: bitàcola, insígnies i punts per participació en activitats i cursos (P-38 a `pendents.md`).
- 1.5: registrar com a decisió la paleta revisada el 31/10 i actualitzar §2; adaptar a la 059 les pantalles d'Activitats, Tresoreria i Usuaris i rols; si l'administració ha de respondre «no trobat» per rol; el contrast de l'interruptor actiu al tema fosc i el focus del selector de calendari natiu del camp de data (T-M01-28); documentar `boto-tactil`, `impressora` i el subratllat.
- Web pública (034): contingut real de projectes i notícies (P-40), fotos i drets d'imatge (P-41), servei del butlletí (P-42) i qui manté el contingut (P-43).
