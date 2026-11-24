# Sistema de disseny — Plataforma C.R.I.S.

- **Versió:** 1.44 (19/11/2026). La 1.44 retira la pantalla en construcció de rols i permisos (§16, T-DX-74): la pantalla real és a `/gestio/permisos/` (T-RP-03), amb la mateixa peça (`avisador.css`).
- La 1.43 (19/11/2026) ajusta la conciliació a l'escriptori (§6.22, T-DX-73): sense cap línia oberta, la taula fa tota l'amplada i el panell no ocupa lloc; amb una línia oberta, la taula a 8/12 sense la columna «Càrrecs». El concepte i cada càrrec van en una línia (el concepte s'endú l'amplada que sobra i acaba amb «…»; sencer al panell i al mòbil). Després d'un pas dins del panell (cercar, revisar), el focus va als resultats de la cerca, al missatge que diu que no n'hi ha o al títol del panell.
- La 1.42 (19/11/2026) fa la conciliació a l'escriptori (§5.3 i §6.22, T-DX-72, PR 9b): el títol amb el que queda per conciliar i els comptadors de Deposito; la taula (8/12) i el panell de la línia triada (4/12), que carrega «Casa a mà», «Casa amb moviments» i «Revisa i confirma» amb HTMX des de les mateixes vistes, amb l'esquelet (`esquelet`, ja descrit a §15.4, ara al CSS), J i K per passar de línia i Esc o «Tanca» per tancar-lo.
- La 1.41 (19/11/2026) fa les pantalles de pagaments i de tresoreria a l'escriptori (§5.3, T-DX-69, PR 7c): capçalera comuna, filtres en una fila al llistat de pagaments, la fitxa i el formulari a 40rem amb Errata al costat per tancar un intent o una liquidació i per revocar un mandat, i la campanya de mandats en 5/7.
- La 1.40 (19/11/2026) afegeix la pàgina «Activitats» del soci, en construcció, i el bloc «Activitats per a tu» (§16, T-DX-63), amb els colors dels tipus d'activitat (`--c-tipus-*`).
- La 1.39 (19/11/2026) agrupa el menú de l'administració en 6 grups plegables, amb icones i el carril de 72 px a la tauleta, i l'inici de l'administració en targetes per grup (§6.1, T-DX-62).
- La 1.38 (19/11/2026) fa el carnet de soci en 3D (§6.21, T-DX-61): s'inclina amb el ratolí i es gira per veure el QR; afegeix `--c-carnet-ok`, `--c-carnet-error` i `--ombra-carnet` (§2.6) i canvia la impressió del carnet (§6.8).
- La 1.37 (19/11/2026) porta Ramillete a totes les mides (§6.12, T-DX-59): la barra a baix fins a 1023 px (flotant i centrada a la tauleta) i un panell lateral clar i flotant a l'escriptori, amb «Mostra el QR» i el compte; la navegació de la capçalera queda només sense JavaScript.
- La 1.36 (19/11/2026) afegeix el joc d'icones (§6.20, T-DX-58): Lucide, allotjat al servidor, amb `{% icona %}`.
- La 1.35 (18/11/2026) fa la fitxa del soci de l'administració a l'escriptori (§5.2, §5.3 i §6.13; T-DX-67, PR 9a): dues columnes 5/7 (`fitxa-soci`), el resum i les dades al costat a la tauleta, un sol botó principal amb les accions rares a «Més» i l'historial d'estats amb la línia de passos de Tramite (`historial-estats`).
- La 1.34 (18/11/2026) redistribueix a l'escriptori el perfil, el mandat, el pagament i el rebut del soci i dos formularis de l'administració (alta presencial i edició de les dades d'un soci) (T-DX-65, §5.3, §6.10, §6.13 i §6.14): capçalera comuna, formulari a 40rem amb `lateral-formulari`, Errata i l'ajuda plegada a la columna lateral, els passos de Tramite al costat del pagament i el rebut estret amb les accions al costat.
- La 1.33 (18/11/2026) fa els llistats de l'administració a l'escriptori (§5.3, T-DX-66, PR 7b): capçalera comuna, la peça `barra-filtres`, la fila sencera clicable també quan l'enllaç és un botó i les seccions dins de `graella-2` amb el seu espai.
- La 1.29 (18/11/2026) redistribueix l'inici del soci a l'escriptori (T-DX-60, §5.1, §6.5 i §6.18): la portada només amb la salutació; a sota, la quota i el carnet en petit en dues columnes sobre el fons de la pàgina, la franja de pendents, i a sota els pagaments recents, la història i la llicència en 8/4; la quota ja no puja en desplaçar (D20, B10).
- La 1.26 (18/11/2026) afegeix la disposició a l'escriptori (§5.3, T-DX-57): el cos creix per trams, amplades noves i les peces `capcalera-pagina`, `disposicio-pagina`, `graella-2`, `amb-columna-lateral`, `graella-targetes` i `desplacable-x`; els imports passen a xifres tabulars sense monoespai.
- La 1.25 (16/11/2026) afegeix Monograma, l'avatar per defecte del soci (§6.19, T-DX-18).
- La 1.24 (16/11/2026) afegeix Oleaje, la portada de l'àrea del soci (§6.18, T-DX-17).
- La 1.22 (16/11/2026) fa l'etiqueta «En construcció», l'ajust i el permís (§6.9, T-DX-03).
- La 1.20 (16/11/2026) afegeix Autentico, el segell de la verificació del carnet (§6.16, T-DX-15).
- La 1.19 (16/11/2026) posa Vigencia a la llicència de la fitxa de l'administració (§6.15, T-DX-14) i deixa que un valor llarg passi a la línia següent a les taules apilades del mòbil.
- La 1.18 (16/11/2026) afegeix Vigencia, els dies que queden de la quota i de la llicència (§6.15, T-DX-13).
- La 1.17 (16/11/2026) afegeix el rebut amb la ranura i el segell (§6.14, T-DX-11).
- La 1.16 (16/11/2026) afegeix Tramite, els passos d'un pagament (§6.13, T-DX-10).
- La 1.15 (16/11/2026) afegeix Ramillete, la navegació de l'àrea del soci al mòbil (§6.12, T-DX-08).
- La 1.14 (16/11/2026) afegeix Solapas, les pestanyes de les fitxes obertes a l'administració (§6.11, T-DX-07).
- La 1.13 (16/11/2026) porta el tema a la configuració del compte (§7, T-DX-05b).
- La 1.12 (16/11/2026) posa Eclipse a la part pública (§7, T-DX-05).
- La 1.11 (16/11/2026) afegeix Errata, el resum d'errors dels formularis (§6.10, T-DX-06).
- La 1.10 (16/11/2026) posa el motor de tema de Duermevela (§7, T-DX-04).
- La 1.9 (16/11/2026) porta la paleta d'estats a OKLCH amb la mateixa lluminositat per rol, les vores amb transparència i la superfície flotant (§15.4, T-DX-02), i corregeix l'ordre d'elevació.
- La 1.8 (16/11/2026) porta a `tokens.css` els tokens de moviment i els radis concèntrics de §15.4 (T-DX-01), amb els noms que ja existien, i fa més grans els logotips (§4; decisió del propietari del 16/11/2026).
- La 1.7 (16/11/2026) afegeix les regles de disseny B, C i D amb els seus noms originals i els tokens que les concreten (§15), l'etiqueta «En construcció» (§6.9) i corregeix els radis de §4. Els tokens nous de §15.4 encara no són a `tokens.css`: hi entren a les tasques T-DX-01 i T-DX-02 del [pla dels recursos externs](plans/recursos-disseny-extern.md).
- La 1.6 (11/11/2026) descriu la navegació comuna tal com és a la plataforma (T-M01-46): la barra lateral de l'administració, el botó «Menú» i «Surt» (§6 i §6.1). No canvia cap token.
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
2. Es veu de seguida en quina zona ets: el color de la zona marca la capçalera, l'etiqueta de secció i els detalls. A l'escriptori, el soci té un panell lateral clar i flotant, i l'administració una barra lateral fosca i fixa (§6.1).
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
| `--c-carnet-ok` / `--c-carnet-error` | `#59D8B0` / `#FFA096` | igual | Estat del carnet («✓ Vàlid», «✕ No vàlid») sobre el carnet fosc (≥6,3:1 sobre `--c-carnet-1` i `--c-carnet-2`). Són els de `--c-ok-text` i `--c-error-text` del tema fosc: el carnet és fosc als dos temes (T-DX-61) |
| `--ombra-carnet` | ombra cap avall i a la dreta | la mateixa, més fosca | Ombra del carnet: la llum ve de dalt a l'esquerra, la mateixa que el reflex (B11, T-DX-61) |

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
- **Radis:** `--r-s` 6, `--r-m` 10, `--r-l` 16, `--r-xl` 22 i `--r-pastilla` (forma de pastilla), els valors de `tokens.css` (aquest punt deia 4, 8 i 12 i no hi coincidia). Un radi interior es calcula amb `--r-interior` (§15.4, regla C1).
- **Vores:** `--v-fina` 1 px; `--v-activa` 3 px (element actiu i vora de zona); `--v-focus` 3 px; `--v-plena` 2 px (peces neumòrfiques amb més contrast).
- **Avatar:** `--avatar` 56 px.
- **Tàctil:** `--tactil` 44 px. És l'alçada i l'amplada mínimes de tot element que es pot prémer, a totes les mides.
- **Estructura:** `--amplada-max` 1200 px, `--amplada-ample` 1440 px, `--amplada-tauleta` 45rem, `--amplada-formulari` 40rem i `--amplada-estreta` 28rem (els trams del cos, §5.3), `--lateral-ample` 240 px (administració), `--lateral-carril` 72 px (tauleta, administració), `--capcalera-alcada` 64 px. `--lateral-soci`, `--columna-dreta` i `--barra-inferior-alcada` són de l'estructura anterior dels socis; ara no es fan servir, però es conserven fins que es validi la nova.
- **Logotip:** `--logo-capcalera` 56 px (socis i administració), `--logo-lateral` 64 px (barra lateral), `--logo-publica-mobil` 64 px i `--logo-publica` 96 px (capçalera pública), `--logo-peu` 160 px (peu de la pública). Abans eren 40, 48, 52, 72 i 120 px; els va fer més grans el propietari el 16/11/2026 (T-DX-01). Amb el logotip de 56 px, la capçalera dels comptes fa 72 px d'alt (`--capcalera-alcada` és el mínim).
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
Al compte personal i mai en accions crítiques. Des de la 1.8, la llista sencera de tokens de moviment és a §15.4; aquí queden els de la 032, amb els valors de `tokens.css`:

| Token | Valor | On |
|---|---|---|
| `--m-entrada` | 300 ms (abans 700, B9) | Entrada de la portada (apareix i puja 24 px), una sola vegada |
| `--m-gir` | 400 ms (abans 650, B9) | Gir del carnet |
| `--m-ona` × `--m-ona-repeticions` | 2,4 s × 2 | Ona de la portada dels wireframes (032). S'atura sola abans de 5 s, així que no cal cap botó de pausa (WCAG 2.2.2). A la plataforma, Oleaje (§6.18) la substitueix |
| `--m-rapid` | 180 ms | Transicions petites (botons, enllaços, menús) |
| `--m-corba` | `cubic-bezier(.23, 1, .32, 1)` | Corba d'entrada |

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
| `capcalera-compte` + Ramillete (`ramillete`, 1.37, §6.12) | Logotip i «Surt» a dalt; la barra de Ramillete a baix, de vora a vora: Inici, Activitats, **Més** al centre, Carnet i Quotes (sense «Activitats», Inici, Perfil, Més, Carnet i Quotes) | Igual, amb la barra flotant i centrada (`--ramillete-amplada`, 30rem com a màxim, radi i ombra) | Sense capçalera: panell lateral clar i flotant a l'esquerra (`--lateral-ample`), amb el logotip, «Mostra el QR», les entrades, «Més» i el compte a baix (avatar, nom de pila, número i «Surt») |
| `portada` (amb `salutacio` i `carnet`) | Gairebé tota la pantalla: avatar, salutació i carnet gran, un a sota de l'altre; ona a baix | Igual, centrat | 2 columnes: salutació a l'esquerra, carnet a la dreta (×1,25) |
| Plataforma, inici (`templates/core/home.html`, T-DX-60) | Portada amb l'avatar i la salutació; a sota, «La teva quota» i el carnet en petit; la franja de pendents; els pagaments recents, la història i la llicència, un a sota de l'altre | Quota i carnet en 2 columnes iguals separades amb `--e-5`; la resta, una columna | Quota i carnet 7/5, sota la portada; franja a tota l'amplada; a sota, també 7/5 (V8, T-DX-77): pagaments recents; història i llicència |
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
| Fitxa del soci | `admin.html#vista-socis-fitxa` | Una columna: capçalera, resum, dades personals, carnet, quotes, llicència, historial i consentiments | Resum, dades i carnet (5) i, al costat, quotes, llicència, historial i consentiments (7); a la tauleta, el resum i les dades al costat i la resta a tota l'amplada (T-DX-67) |
| Sol·licituds | `admin.html#vista-socis-sollicituds` | Pestanyes (Altes, Canvis de tipus, Baixes) i una targeta per sol·licitud | Targetes en dues columnes |
| Alta presencial | `admin.html#vista-socis-alta` | Formulari en una columna | Formulari (7) i notes (5) |
| Quotes i impagats | `admin.html#vista-socis-quotes` | Generació a dalt; taula en blocs | Xifres en una fila i taula sencera |
| Importació de Cluber | `admin.html#vista-socis-cluber` | Fitxer, importació final i resultat, un a sota de l'altre | Fitxer (7) i importació final (5); resultat a tota l'amplada |
| El meu perfil | `socis.html#perfil` | Una columna | Dades (7) i, al costat, consentiments, llicència, sol·licituds i dades (5) |
| Canvi a ple dret, baixa, esborrar el compte | `socis.html#canvi-tipus`, `#baixa`, `#esborrar` | Una columna | Columna estreta centrada |
| No trobat | `socis.html#no-trobat` | Una targeta | Igual |

Les pantalles del compte personal són planes, com pagar i els avisos (§6.5): sense degradat, ona ni moviment.

### 5.3 Disposició a l'escriptori (T-DX-57)
A l'ordinador, les pantalles aprofiten l'amplada amb **el mateix ordre que al mòbil**, i es van estrenyent de manera fluida en fer la finestra més petita. Per sota de 600 px no canvia res. Full d'estil: `static/css/disposicio.css`, enllaçat a la base just després de `comptes.css`.

**El cos per trams (`cos-compte`)**
| Classe | Mòbil | Tauleta (600 px) | Escriptori (1024 px) | On |
|---|---|---|---|---|
| `cos-compte` | 28rem | `--amplada-tauleta` (45rem) | `--amplada-max` (1200 px) | Àrea del soci, fitxes i formularis |
| `cos-compte cos-ample` | 28rem | `--amplada-ample` (1440 px) | `--amplada-ample` | Llistats de l'administració i conciliació |
| `cos-compte cos-estret` | `--amplada-estreta` (28rem), centrat a totes les mides | | | Entrada, codi TOTP, recuperació, invitació, sessió caducada, verificació del carnet, 403 i 404 |

Dins del cos, un paràgraf no passa de `--amplada-text` (68ch), i un `formulari` o una llista `dades-soci` de `--amplada-formulari` (40rem), alineats a l'esquerra: l'etiqueta no queda lluny del seu valor. El cos és un contenidor (`container: cos`): les peces de sota s'adapten a l'amplada de la columna on són, no a la de la finestra (C8).

**Peces**
- `capcalera-pagina`: etiqueta, títol (i, si cal, una frase) a l'esquerra i les accions (`accions`) a la dreta, alineades a baix. Al mòbil, les accions a sota del títol. Un sol `boto-principal` per pantalla (D19).
- `disposicio-pagina`: els blocs d'una pantalla, separats amb `--e-6`. S'agrupa amb espai, no amb caixes i línies (D15).
- `graella-2`: dues columnes iguals quan la columna fa 34rem o més (el cos de la tauleta en fa unes 42); amb `graella-5-7`, `graella-7-5` o `graella-8-4`, les proporcions de 12 columnes a partir de 56rem (el cos de l'escriptori al costat d'una barra lateral i amb la barra de desplaçament en fa unes 59; T-DX-57b). A sota l'una de l'altra quan no hi caben.
- `amb-columna-lateral` (+ `columna-lateral` al fill): el contingut i una columna de `--lateral-ample` al costat (o a l'esquerra, amb `lateral-esquerra`), que es queda fixa en baixar a partir de 56rem. Per a l'ajuda, el resum d'errors d'Errata o els filtres.
- `lateral-formulari` (1.34, T-DX-65), amb `amb-columna-lateral`: per als formularis. La columna principal (`columna-principal`, un sol fill amb el formulari o els blocs) fa com a màxim `--amplada-formulari` i la lateral queda just al costat. Si hi ha errors, el resum d'Errata (`_errata.html`) va **abans** de la columna principal al DOM (el focus i el lector de pantalla el troben primer, com abans) i, a l'escriptori, a dalt de la columna lateral, d'una sola columna; l'ajuda (`columna-lateral`) a sota. Al mòbil, el mateix ordre del DOM: Errata, formulari i ajuda.
- Ajuda d'un formulari (1.34): a la `columna-lateral`, un `h2.etiqueta-seccio` «Ajuda» i una pregunta plegada per text d'ajuda que ja hi havia a la pàgina (`details.recoveco-p` de Recoveco, §16, amb `name="ajuda"`; la primera oberta, perquè es vegi sense tocar res). La pàgina enllaça `recoveco.css` al bloc `estils`. L'ajuda d'un camp concret es queda al camp. Sense caixes (D15).
- On (T-DX-65): el perfil, el mandat, l'alta presencial i l'edició de les dades d'un soci. El mandat i l'alta presencial només porten Errata al costat: el mandat no té text d'ajuda de pàgina, i l'única ajuda de l'alta presencial seria explicar el possible duplicat, que sense P3a ha de quedar neutra (no se'n parla). El perfil i l'edició, només l'ajuda (no fan servir Errata).
- `graella-targetes`: 1, 2 o 3 targetes per fila segons l'amplada (mínim 18rem cadascuna).
- Taules (`taula`), a partir de 600 px: capçalera fixa en baixar, fila ressaltada en passar-hi el ratolí i, si la fila porta un enllaç `enllac-fila`, la fila sencera hi porta (B14). L'enllaç continua sent l'element enfocable i el que llegeix el lector de pantalla.
- Taula apilada (`taula`, per sota de 600 px; T-DX-78): la fila buida d'un `{% empty %}` (una sola cel·la amb `colspan` i sense `data-etiqueta`) va a l'esquerra, a tota l'amplada; un formulari dins d'una cel·la (per exemple, el motiu de «Desfés») passa sota l'etiqueta i fa tota l'amplada de la cel·la.
- Cel·la d'accions d'una taula (`td.cel-accions`, T-DX-88): sense `data-etiqueta` i amb la capçalera «Accions» només per al lector de pantalla (`visualment-amagat`), també quan una fila no té cap acció. A partir de 600 px, les accions (també un `.accions` dins la cel·la) van a la dreta de la columna; a partir de 1024 px, el text d'un botó no es parteix.
- `barra-filtres` (al `formulari` de filtres d'un llistat, T-DX-66): fa tota l'amplada del cos (no el `--amplada-formulari`); quan la columna fa 37,5rem o més, els camps (`filtres`, mínim 11rem cadascun) en una fila que es parteix si no hi caben, i els botons al final, alineats a baix. Al mòbil, apilats com abans.
- **Llistats de l'administració (T-DX-66):** `cos-ample`, `capcalera-pagina` (etiqueta, títol, frase i, si n'hi ha, un enllaç a `accions`), `barra-filtres` i taula. `enllac-fila` només a l'enllaç que ja hi havia cap a la fitxa (socis, sol·licituds, remeses, RGPD, dades bloquejades); mai on la fila té una altra acció (casella, formulari o dos enllaços). Si l'enllaç és un `boto`, perd la posició i l'encongiment de `:active` dins la taula, perquè la capa ocupi la fila. Les columnes per rol les decideix el servidor; a la tauleta no s'amaga cap columna. Comptadors de Deposito (§6.17) només amb el que la vista ja dona (altes, sol·licituds, retornats, llicències per confirmar).
- **Fitxa del soci (T-DX-67, PR 9a):** `capcalera-pagina` amb un sol `boto-principal` («Edita les dades») i «Més» (el `<details class="menu-exporta">` del llistat, amb `menu-exporta.js`: Esc el tanca i torna el focus, i també un clic fora o el focus que en surt) amb les accions rares (corregir la data d'alta, crear una baixa i restablir el doble factor), amb les mateixes condicions que abans (D19, B15, B20). A la capçalera, la llista es col·loca respecte a la fila d'accions i, amb les accions a la dreta, s'obre cap a l'esquerra: no surt de la pàgina ni a 320 px. A sota, `graella-2 graella-5-7 fitxa-soci`: el resum (`dades-soci`), les dades personals i el carnet (`fitxa-carnet`) a l'esquerra i, a `fitxa-taules`, les quotes, la llicència, l'historial i els consentiments a la dreta; cada columna amb la seva alçada (una fila `1fr` al final). A la tauleta (34rem), el resum i les dades al costat i el carnet i les taules a tota l'amplada. Al mòbil, una columna en l'ordre del document, que és el de l'esquerra i després el de la dreta. Les dades que es veuen les continua decidint el servidor (`vis.*`) i cada acció torna a comprovar el permís a la vista.
- **Pagaments i tresoreria (T-DX-69, PR 7c):** `capcalera-pagina` a totes (etiqueta, títol i, si n'hi ha, la frase que ja hi havia). Llistats (pagaments, «A revisar», liquidacions): `cos-ample` i, als pagaments, `barra-filtres`; cap `enllac-fila`, perquè les files tenen una acció («Tanca», «Casa a mà…», «Confirma…») i no una fitxa. Decidir sobre un element (tancar un intent o una liquidació «a revisar», revocar un mandat): `lateral-formulari` com el mandat del soci, amb la fitxa i el formulari a la `columna-principal` i el resum d'Errata al costat, primer al DOM i amb el focus; el text que explica què passa en confirmar es queda al formulari i no es plega. Campanya de mandats: `graella-2 graella-5-7`, el recompte a l'esquerra i la invitació a la dreta (al mòbil, en aquest ordre). Traspàs, arqueig, anul·lació, pagament a mà i confirmació d'una liquidació: només la capçalera; el formulari ja fa `--amplada-formulari` i no tenen ni Errata ni ajuda per posar al costat. Els permisos i les dades que es veuen els continua decidint el servidor.
- **Conciliació (T-DX-72, PR 9b):** `capcalera-pagina` amb el títol del que queda («Queden N línies per conciliar», D13) i, a sota, els comptadors de Deposito (§6.17: pendents en ambre, proposades, conciliades i excloses). A l'escriptori, la taula i el panell de la línia triada en 8/4 (§6.22); a la tauleta i al mòbil, la taula sola i l'enllaç porta a la pàgina, com abans.
- `desplacable-x`: pestanyes o carrils que es desplacen de costat, amb la vora de la dreta esvaïda (C2).

**Sense moviment nou:** cap animació d'entrada de pàgina (D20, B10). Les pantalles es redistribueixen per tasques (T-DX-58 en endavant); fins llavors, una pantalla que no ha canviat queda més ampla amb el mateix ordre.

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
| Codi i import | `codi`, `import` (+ `import-entrada`, `import-sortida`); cel·la `cel-import` dins de `taula` | `codi` en JetBrains Mono; `import` amb la lletra del text i xifres tabulars (des de la 1.26, D7). El sentit d'un moviment porta signe («+» o «−») i color (`--c-ok-text` o `--c-error-text`), mai només color. A la `taula`, la columna d'imports (capçalera i cel·les) porta `cel-import` i va a la dreta (T-M04-15) |
| Marca pendent | `a-validar` | Senyala les dades o decisions [A validar] dins de les pantalles de l'administració i de les «En construcció». Mai a les pantalles que veu el soci (V17): allà, un text neutre o res, i la marca, a la documentació |
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
- Compte personal (1.37): Ramillete (§6.12). Fins a 1023 px, la barra a baix; a partir de 1024 px, un panell lateral **clar i flotant** (`--c-superficie-flotant`, radi i ombra, separat de les vores). El de l'administració és **fosc i fix**: les dues zones tenen panell a l'escriptori, però es veu de seguida en quina ets. Sense JavaScript, la navegació en text a la capçalera.
- Administració: barra lateral fosca amb els mòduls Socis, Activitats, Material, Tresoreria, Pagaments, Llicències, Web i Dashboard, **filtrada per rol** (§6.2).
- Element actiu: `aria-current="page"`, barra groga, negreta i fons (§2.5).

**Navegació a la plataforma (1.6, T-M01-46).** És la del wireframe `admin.html`, amb aquestes precisions:
- **Entrades.** Una per pantalla que existeix, no per mòdul: Inici, Llistat de socis, Altes pendents, Alta presencial, Sol·licituds de socis, Llicències de la fitxa per confirmar (abans «Llicències pendents de confirmar», T-DX-100), Quotes i impagats, Importació de Cluber, Comptes d'administrador i Registre d'activitat. Quan hi hagi més mòduls, s'agruparan com al wireframe.
- **Filtrada al servidor.** Una entrada només arriba a l'HTML si el compte té el permís que la ruta declara (`apps/members/permissions.py` i `apps/accounts/navigation.py`); no s'amaga amb CSS. No és cap control: cada vista torna a comprovar el permís.
- **Compte.** Sota les entrades: el nom d'usuari del compte actiu (`codi`), «Compte d'administrador · TOTP actiu» i «Surt» (formulari POST amb CSRF). Cap altra dada.
- **Escriptori (1024 px o més).** Columna fixa de `--lateral-ample`, sota la capçalera. El botó «Menú» no hi és.
- **Mòbil (fins a 599 px).** La barra va sota la capçalera, a tota l'amplada, plegada darrere del botó «☰ Menú». El botó l'obre i la tanca (Intro o Espai); Esc la tanca i torna el focus al botó. Sense JavaScript, la barra es veu sempre oberta.
- **Grups (1.39, T-DX-62; B15 i B16).** «Inici» solt a dalt i 6 grups plegables (`<details>`, sense JavaScript), cada un amb la seva icona (§6.20): Socis; Quotes i tresoreria; Pagaments; Importacions; Seguretat i RGPD; Ajustos. El grup de la pantalla actual surt obert. Els grups i el seu ordre són a `GROUPS` (`apps/accounts/navigation.py`), en l'ordre d'`ENTRIES`; el servidor continua filtrant cada entrada pel permís, i un grup sense cap entrada visible no surt. L'inici de l'administració mostra les mateixes entrades, agrupades igual, en targetes (`graella-targetes`, reixa de Parrilla, sense arrossegar ni desar; cap xifra nova).
- **Tauleta (600 a 1023 px, 1.39).** Amb JavaScript, carril fosc de `--lateral-carril` amb la icona de cada grup; cada icona porta el nom del grup com a nom accessible (text amagat visualment, no `aria-label`). Tocar-ne una n'obre les entrades al costat, d'un grup en un; Esc o tocar fora el tanca i el focus torna a la icona. El grup actual porta la barra daurada. El botó «Menú» continua obrint la barra sencera amb els noms, a tota l'amplada sota la capçalera. Sense JavaScript, la barra sencera, com al mòbil.
- **Entrada actual:** `aria-current="page"`, barra daurada (`--v-activa`, `--c-accent`), negreta i fons `--c-lateral-fons-2`; també quan s'és en una pantalla que en penja (la fitxa d'un soci marca «Llistat de socis»).
- **Contrast** (calculat amb els valors de `tokens.css`, clar i fosc): text de les entrades sobre la barra, 6,7:1 i 7,4:1; entrada actual sobre el seu fons, 7,9:1 i 9,2:1; focus daurat sobre la barra, 10:1 o més.
- **Compte personal.** Ramillete (§6.12): «Surt» és a la capçalera fins a 1023 px i al panell a partir de 1024 px (un sol «Surt» visible per pantalla). Sense JavaScript, navegació en text a la capçalera, amb «Surt» com a última peça.

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
  - A la plataforma (T-DX-60): `avis avis-avis franja-estat`, una fila per quota pendent (concepte i import amb `import`) i «Paga ara» amb `boto boto-gran` (56 px, `--tactil-gran`), pla. No és el `boto-principal`: amb un pendent, el principal és el «Paga ara» de «La teva quota» (D19; V20, T-DX-77; abans era `boto-mari`, d'un altre color que la resta de botons principals). Sense pendents no surt: l'estat «Al dia» ja és a «La teva quota».
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
- **Formularis:** etiqueta sempre visible, error a sota del camp (`aria-invalid` i `aria-describedby`; la vora de `--c-error` val per a `input`, `select` i `textarea`, T-DX-90), focus al primer camp amb error i recompte d'errors anunciat.
- **Confirmacions:** la baixa del soci es confirma en un diàleg; l'esborrat del compte, amb una casella explícita («Entenc que no es pot desfer»).
- **Acció irreversible a l'administració (T-M01-22, `/gestio/rgpd/`):** aprovar un esborrat RGPD demana, al mateix formulari, la casella explícita, la contrasenya i el codi TOTP de qui aprova (reautenticació a la mateixa petició). Abans del formulari, una llista «Què passarà en aprovar-la» amb frases sense imports ni dades personals. Rebutjar és un formulari a part amb el motiu obligatori. Si no es pot aprovar, un `avis avis-error` diu per què i el formulari d'aprovar no surt. Pantalles sense wireframe propi: només components existents (`taula`, `dades-soci`, `targeta`, `formulari`, `camp`, `casella`, `avis`, `accions`, `boto`).
- **Pantalles de tresoreria de només lectura (T-M04-15, primer tall: `/gestio/tresoreria/` i `/gestio/tresoreria/moviments/`):** sense wireframe propi; només components existents (`taula`, `formulari`, `filtres`, `camp`, `avis`, `estat`, `accions`, `boto`, `import` amb `cel-import`). L'únic formulari és el de filtres, amb GET. Un moviment anul·lat continua a la llista amb `estat estat-error` «✕ Anul·lat» (CA-T06.1). Sense el permís T1, «no trobat» (059); el menú no hi enllaça.
- **Importació de l'extracte bancari (T-M00-01, `/gestio/importacions/extracte/`):** sense wireframe propi; només components existents (`avis`, `targeta`, `formulari`, `camp`, `casella`, `taula`, `dades-soci`, `estat`, `import` amb `cel-import`, `accions`, `boto`). Tres moments a la mateixa pantalla: pujar (fitxer i ajuda amb les columnes del perfil), previsualitzar (recomptes, una fila per línia amb `estat-ok` «✓ Nova», `estat-neutre` «■ Duplicada: no s'importa» o `estat-error` «✕ Amb error» i el motiu, sense cap valor de la línia amb error) i la llista d'extractes amb «Desfés» i el motiu. Els números de compte i de targeta del concepte surten tapats («[número tapat]»). Confirmar amb línies amb error demana la casella d'excloure-les. Sense el permís M9, «no trobat»; el menú no hi enllaça.
- **Ajustos (T-AJ-02, `/gestio/ajustos/`):** sense wireframe propi; només components existents (`taula`, `dades-soci`, `targeta`, `formulari`, `camp`, `avis`, `accions`, `boto`, `codi`). La llista d'un apartat porta, per valor, el vigent, el programat, l'inicial i el rang, i un enllaç «Canvia: …» o «Historial: …» segons el permís. La pantalla del valor: dades, formulari (només a qui el pot editar; el tipus decideix el camp) i historial (quan, qui, anterior, nou, en vigor des de i nota). Un valor que no es desa mostra `avis avis-error` «No s'ha desat res.» amb el motiu. Sense el permís de l'apartat, «no trobat»; el menú no hi enllaça.
- **Clau d'un ajust a la llista (T-DX-80):** `codi clau-partible`, amb `<wbr>` després de cada «_» i «.»: la clau només es parteix allà, i no lletra a lletra quan una llista llarga (els països del mandat) s'endú l'amplada. Els valors llargs es parteixen dins de la seva cel·la.
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
- **El carnet en paper (T-DX-61):** les dues cares, una al costat de l'altra, sense gir ni inclinació, en clar (fons `--paper`, text del tema clar i el logotip per a fons clar), perquè el text no surti clar sobre paper blanc. La resta de la pàgina («Què veu qui l'escaneja», els botons i el formulari) no s'imprimeix. Estils a `static/css/carnet.css` (§6.21).
- Estils generals a `static/css/comptes.css` (`@media print`), no a `tokens.css`.

### 6.9 Etiqueta «En construcció»
Marca una pantalla, o un bloc d'una pantalla, que encara no és funcional ([pla dels recursos externs §1](plans/recursos-disseny-extern.md#1-abast)). **Feta a la T-DX-03:** `templates/_en_construccio.html` (`{% include "_en_construccio.html" with id="…" %}` dins d'un contenidor `en-construccio-bloc`), `static/css/en-construccio.css` i el decorador `apps/core/under_construction.py`.
- **Classe:** `en-construccio`. Pastilla petita a dalt a la dreta del bloc (`position: absolute` dins d'un contenidor `position: relative`), text `--t-xs`, `--c-text-2` sobre `--c-superficie-2`, vora amb transparència (C3), radi `--r-pastilla`, farciment `--e-1` `--e-2`. Sense icona, sense animació i sense color d'estat: no és cap estat del negoci (D1).
- **Text:** «En construcció», traduïble (`{% translate %}`). Per al lector de pantalla, el bloc porta `aria-describedby` cap a l'etiqueta.
- **On:** a tota la pantalla quan res no és funcional; només al bloc que no ho és quan la pantalla és en part funcional. Mai al costat d'una dada real.
- **Al servidor (control, no simulació):** la vista només accepta `GET`; els formularis van dins d'un `fieldset disabled`; el contingut és d'exemple, inventat i fix, i no llegeix ni escriu cap model. En local i a l'entorn de proves, `SHOW_UNDER_CONSTRUCTION` les mostra a tothom; a producció està apagat i només les veuen els comptes d'administrador amb el permís «Veure pantalles en construcció», mai els socis ni la web pública ([P-90](decisions/pendents.md), resposta C). El servidor no arrenca a producció amb l'ajust encès (T-DX-03). Sense accés, la ruta respon 404 i no surt al menú.
- **Prova:** `apps/core/tests/test_under_construction.py` recorre totes les rutes amb el decorador i comprova que cap mètode que escriu (`POST`, `PUT`, `PATCH`, `DELETE`) no és acceptat (405). Cada pantalla, a més, comprova que porta l'etiqueta. Quan la pantalla es torna funcional, la vista deixa el decorador, la prova se substitueix i l'etiqueta se'n va.
- **Permís:** `core.under_construction.view` (P-90, resposta C), sense cap rol al començament; l'assigna l'administrador des de l'editor de permisos. Els socis i la web pública no tenen permisos, així que a producció no les veuen mai.

### 6.10 Errata: resum d'errors d'un formulari (T-DX-06)
Del recurs Errata ([pla dels recursos externs](plans/recursos-disseny-extern.md)): la fulla de correccions amb el segell, el títol amb el nombre d'errors i un enllaç numerat per camp.
- **Peça:** `templates/_errata.html` (`{% include "_errata.html" %}` a dalt del formulari, amb `form` al context), `static/css/errata.css` i `static/js/errata.js`, carregats a la plantilla base.
- **Quan surt:** només si el servidor ha tornat el formulari amb errors. Un element per camp amb errors (el primer missatge) i un per als errors generals; el títol és concret: «Hi ha N errors» (`form.errors|length`; D17). Els errors d'un camp ocult i els generals surten com a «Formulari», sense enllaç.
- **Comportament:** en carregar la pàgina, el focus va al resum (`role="alert"`, `tabindex="-1"`); cada enllaç porta al seu camp i hi posa el focus. Sense JavaScript, el resum es veu igual i l'enllaç salta al camp. Els missatges al costat de cada camp es mantenen.
- **Estil:** vora `--v-plena` de `--c-error`, ombra desplaçada de `--c-error-fons`, fons `--c-superficie-flotant`; números amb `--c-error-fons` i `--c-error-text` i xifres tabulars; cada enllaç fa com a mínim `--tactil` d'alt.
- **Seguretat:** els missatges són els del servidor i no diuen mai si un compte existeix.
- **Encara no:** la validació en sortir de cada camp, l'índex de seccions i el «Tot correcte» del recurs. Demanen repetir al navegador les regles del servidor; es faran en una tasca pròpia.
- **On és:** el formulari «Fer-se soci» (web i alta presencial). Els altres formularis s'hi afegeixen quan es toquin.

- **A la columna lateral (T-DX-65):** a l'alta presencial i al mandat, el resum va fora del formulari, abans de la columna principal, i a l'escriptori a dalt de la columna lateral (§5.3, `lateral-formulari`), d'una sola columna com al mòbil. El focus en carregar i els enllaços als camps no canvien. `_join_form.html` el deixa de posar amb `errata_outside`; la web pública el continua tenint a dalt del formulari.
- **On (T-DX-48):** també als formularis del mandat (signar, revocar el soci i el tresorer) i a obrir la campanya. Substitueix l'avís separat dels errors generals: dos `role="alert"` llegirien el mateix dues vegades. El text del resum fa servir la mateixa barreja que Ramillete, perquè dins d'una targeta `--c-text-2` no arribava a 4,5:1 al fosc. «Com pago la quota» no en porta: no té formulari de Django (els errors són un missatge després de redirigir).

### 6.11 Solapas: pestanyes de les fitxes obertes (T-DX-07)
Del recurs Solapas ([pla dels recursos externs](plans/recursos-disseny-extern.md)): la pestanya arrodonida per dalt que s'uneix amb la fulla, la franja de color de l'activa, la × que surt en passar-hi o a l'activa, el punt de canvis sense desar i el menú «+N» amb les que no hi caben.
- **Peça:** `static/js/solapas.js` i `static/css/solapas.css`; la tira és a `base.html`, a dalt del contingut, només amb una sessió de l'administració. Una fitxa que es vol a les pestanyes posa `{% block solapa %}<meta name="cris-solapa" content="…">{% endblock %}`. De moment, la fitxa del soci («Soci 12») i la de les sol·licituds («Baixa 34»).
- **Què es desa (P-96, opció B):** la llista de pestanyes (adreça i etiqueta, **sense noms**) a `sessionStorage`, que només viu en aquesta pestanya del navegador. El contingut no es desa enlloc. «Surt» (el formulari de `.lateral-compte`) la buida.
- **Comportament:** cada pestanya és un enllaç a la fitxa, i el servidor torna a comprovar el permís en obrir-la. En tancar l'activa s'obre la de la dreta o, si era l'última, la de l'esquerra; sense cap pestanya, l'inici de l'administració. Es reordenen arrossegant o amb Alt+← i Alt+→. Quan no hi caben, les que fa més que no s'obren passen al menú «+N» (mai l'activa), i la tira té la vora emmascarada (C2). Si la fitxa activa té canvis sense desar, la pestanya porta un punt i, en tancar-la, es demana confirmació.
- **Mides:** cada pestanya fa `--tactil` d'alt; la × i el «+N» es veuen de `--selector-alcada` amb una àrea de 44 px.
- **Del recurs no s'hi fa:** el panell lateral de registres (la navegació és la barra lateral de sempre) i els esborranys en tancar una pestanya (P-96).

### 6.12 Ramillete: navegació de l'àrea del soci (T-DX-08 i T-DX-59)
Del recurs Ramillete ([pla dels recursos externs](plans/recursos-disseny-extern.md)): la barra a baix amb la marca de la pàgina activa i el botó central rodó que gira (+ → ×) i obre en ventall cap amunt les opcions rares, una darrere l'altra, amb un vel darrere (B3, B15). Des de la 1.37 (decisió del propietari del 18/11/2026), a totes les mides.
- **Peça:** `templates/members/_ramillete.html` (inclosa a `base.html` **abans** de `<main>`, per als comptes personals: l'ordre del teclat és salt, navegació i contingut a totes les mides), `static/css/ramillete.css`, `static/js/ramillete.js` i les etiquetes `preview_url`, `has_pending_fee` i `may_request_new_card` (`apps/members/templatetags/member_nav.py`). Icones del joc comú (§6.20): 24 px a la barra (`icona-nav`), 20 px al panell.
- **Fins a 1023 px (mòbil i tauleta):** la barra porta Inici, Activitats, **Més** (al centre), Carnet i Quotes. Al ventall: El meu perfil, Com pago la quota, Mandat de domiciliació (amb `MANDATE_SIGNING_ENABLED` o un mandat actiu, com abans), Canvi de tipus, Baixa i Seguretat i aparença. Al mòbil va de vora a vora; a la tauleta (600–1023 px) és flotant i centrada, de `--ramillete-amplada` (30rem) com a màxim, amb `--r-xl` i `--ombra-flotant`. La capçalera només deixa el logotip i «Surt», a la mateixa fila.
- **«Activitats»:** porta a «Les meves activitats» (`activities:mine`; T-DX-95), que també queda marcada a la inscripció del soci (`activities:member_enrol`). Sempre hi és: la barra porta Inici, Activitats, «+», Carnet i Quotes, i «El meu perfil» és el primer element del ventall. A la navegació sense JavaScript (`_personal_nav.html`), «Les meves activitats» després d'«Inici».
- **A partir de 1024 px:** un panell lateral clar i flotant a l'esquerra (`--c-superficie-flotant`, `--r-xl`, `--ombra-flotant`, de `--lateral-ample`, separat `--e-4` de les vores) i sense capçalera. De dalt a baix: el logotip i «Àrea de socis»; l'acció partida «Mostra el QR» (va a `members:card#qr`) amb una fletxa que obre un menú petit amb «Paga ara» (només si el soci té una quota pendent; va a «Les meves quotes») i «Demana un carnet nou» (`members:card#carnet-nou`; amb la regla de la pàgina del carnet, `cards.may_request_new_card`: soci actiu i amb «vàlid fins al»), només per als socis (sense cap de les dues accions, no hi ha fletxa); les entrades Inici, Activitats (la mateixa condició), Les meves quotes, Com pago la quota, Mandat de domiciliació (la mateixa condició), El meu carnet i El meu perfil; «Més», que desplega Canvi de tipus, Baixa i Seguretat i aparença (ja obert si la pàgina actual hi és); i, a baix, el compte: Monograma (§6.19), el nom de pila, «Soci núm. N» (`codi`) i «Surt», l'únic de la pantalla. L'acció partida fa servir el botó normal, no el principal: el botó principal és el de cada pantalla (D19).
- **Entrada actual:** `aria-current="page"`, fons de la zona (`--c-zona-fons`), barra daurada (`--v-activa`, `--c-zona`) i negreta; mai només el color. A la barra, la marca daurada a dalt de la pestanya.
- **Quan:** només amb JavaScript (`ramillete.js` posa `.ramillete-actiu` a `<html>`). Sense JavaScript, la navegació en text de la capçalera (`_personal_nav.html`), que té els mateixos enllaços i condicions.
- **Teclat:** al ventall, el focus va a la primera opció en obrir; Tab i les fletxes hi queden atrapats; Esc el tanca i torna al botó; tocar fora també el tanca. Al panell, la fletxa del QR obre el menú amb Intro o Espai i hi porta el focus; les fletxes el recorren; Esc, tocar fora o sortir-ne amb Tab el tanquen (Esc torna el focus a la fletxa). «Més» és un desplegable: Intro l'obre i el tanca, i Esc el plega i torna el focus al botó.
- **Moviment:** el ventall surt amb `--m-panell`, `--m-corba-molla` i `--m-escalonat` entre opcions; el botó s'encongeix en prémer (`--escala-premut`). Al panell, només gira la fletxa en obrir (`--m-rapid`). Cap altre moviment; amb `prefers-reduced-motion`, res.
- **Seguretat i privacitat:** el menú es construeix al servidor amb el compte de la sessió; amagar un enllaç no és cap control (cada vista ho torna a comprovar). Només el nom de pila, el número i l'avatar del soci de la sessió. «Surt» és un POST amb CSRF. «Paga ara» surt d'una sola consulta a les quotes pendents del soci de la sessió; mai de les d'un altre. Un compte personal sense soci veu només Inici, El meu perfil i Seguretat i aparença.
- **Del recurs no s'hi fa:** les fulles de cada acció.

- **Contrast (T-DX-48, P-283):** les pestanyes inactives fan servir `color-mix(in srgb, var(--c-text-2) 55%, var(--c-text))`: `--c-text-2` sobre la barra flotant feia 4,18:1 al fosc. Continuen diferents de l'activa (`--c-text` i la marca).
- **Barreja en sRGB (T-DX-52):** barrejant dos grisos en oklch, el resultat té el to «none», i axe no en sap calcular el contrast (el deixa per a revisió manual). En sRGB, axe el calcula: més de 4,5:1 als dos temes, i la prova de `test_accessibilitat_mandat.py` ho comprova. Errata fa servir la mateixa barreja. Regla: un color de text fet amb `color-mix()` es barreja `in srgb`. Les ombres i els vels poden continuar en oklch.
- **Subpàgines i pàgines sense menú (T-DX-76, V4 i V19):** una subpàgina marca l'entrada d'on s'obre: pagar una quota i el rebut marquen «Les meves quotes»; la targeta guardada, «Com pago la quota»; revocar el mandat, «Mandat de domiciliació»; les pàgines de `socis/perfil/…`, «El meu perfil»; el carnet nou, «El meu carnet»; el doble factor, «Seguretat i aparença». A la barra, si l'entrada és al ventall, el «Més» no porta cap marca (la porta l'opció en obrir-lo). A l'acceptació de les polítiques (soci importat, primera entrada) no hi ha cap menú, ni la barra ni el panell ni la navegació de la capçalera: el servidor hi torna des de qualsevol pàgina de l'àrea, i la pantalla ja porta «Sortir sense acceptar». Un compte sense soci té a la barra Inici, «Més» i Perfil, amb «Més» al centre (la segona pestanya passa després de «Més»). A l'administració, cada ruta de `administration:` penja d'una entrada de `ENTRIES` o és a la llista de pantalles sense menú de `test_navigation_subpages.py` (entrar, sortir, el doble factor de la primera entrada i els fitxers privats).

### 6.13 Tramite: els passos d'un pagament (T-DX-10)
Del recurs Tramite ([pla dels recursos externs](plans/recursos-disseny-extern.md)): la línia de passos que s'omple d'una etapa a la següent, l'etapa en groc quan el proveïdor no completa el pagament i el segell en confirmar-se.
- **Peça:** `templates/payments/_tramite.html` (dins de `_status.html`, que HTMX torna a demanar cada 3 s mentre és en curs) i `static/css/tramite.css`.
- **Passos:** 1 «Tria com pagar», 2 «Confirmació del proveïdor», 3 «Pagament completat». Surten de l'estat que diu el servidor (`payments.payment_status`): pendent → pas 1 ara; en curs → pas 2 ara; fallat o «No s'ha confirmat a temps» → pas 2 en avís (!); pagat → els tres fets i el segell. Un càrrec que no es pot pagar no porta passos. El pas actual porta `aria-current="step"` i cada pas diu el seu estat al lector de pantalla.
- **Regles:** sense temps simulat (el recurs omplia la línia amb la durada de cada pas, que aquí no se sap) i sense animació contínua (D20). El segell només surt quan el servidor ha confirmat el pagament (B10), mai en tornar del proveïdor. El pas 3 no es diu «Pagat»: aquest text és el de l'estat, i només surt quan ho és.
- **Encara no:** el rebut que surt per la ranura i la impressió en blanc i negre (T-DX-11).
- **Al costat del pagament (T-DX-65):** a la pantalla de pagament (`pagament-amb-passos`), quan el cos fa 56rem o més, els passos van en vertical a la dreta del pagament, que es queda a `--amplada-formulari`; la línia va del centre d'una marca a la següent. Només CSS a `tramite.css`: `_status.html` no canvia, perquè HTMX el torna a demanar sencer. Al mòbil i a la tauleta, a dalt i en horitzontal, com abans.
- **Historial d'estats (`tramite historial-estats`, T-DX-67):** la mateixa línia, en vertical i només de lectura, a l'historial d'estats i tipus de la fitxa del soci: cada canvi és un `tramite-pas` amb la `tramite-marca` buida (decorativa) i el text al costat, del més recent al més antic. És neutra: el primer (l'estat d'ara) porta `es-actual` (la marca del color del text) i la línia és `--c-linia-forta`; cap verd, perquè un estat antic no és cap pas fet (pot ser una baixa o un impagat). Sense moviment.

### 6.14 El rebut: la ranura i el segell (T-DX-11)
De Tramite, el comprovant que surt d'una ranura i s'imprimeix en blanc i negre; d'Emisor (P-93, opció C), el segell que cau sobre el document ([pla dels recursos externs](plans/recursos-disseny-extern.md)).
- **Peça:** `templates/payments/receipt.html` i `static/css/ranura.css`. El paper és `--paper`, clar als dos temes, com el justificant.
- **Moviment:** en carregar la pàgina, el rebut surt de la ranura (`--m-panell` × 1,2) i després cau el segell «Pagat» amb la data (`--m-corba-molla`). Una sola vegada; sense moviment amb `prefers-reduced-motion`.
- **El segell només hi és perquè el rebut existeix:** el rebut només es crea quan el servidor ha confirmat el pagament (B10, RN-M05b-19). Va sota les dades, alineat a la dreta, i no en tapa cap. Per al lector de pantalla és decoratiu (les dades ja ho diuen).
- **Imprimir o desar com a PDF:** sense ranura ni animació, el paper sense fons i el segell en blanc i negre.
- **Captures:** la *fixture* `capture` de les e2e espera que acabin les animacions finites abans de fer la foto.
- **Rebut anul·lat (T-DX-11b; 045, M05b-6):** si el rebut té una anul·lació (`receipt.cancellation`), el segell diu «Anul·lat» amb la data de l'anul·lació, en `--grana` (primitiu nou, igual als dos temes, 8,3:1 sobre `--paper`), i no cau: no és cap celebració (B10). A sota, «Rebut anul·lat el dd/mm/aaaa.» i la nota. Mai el segell «Pagat» en un rebut anul·lat. El rebut no s'esborra (només s'hi afegeix l'anul·lació).
- **Disposició (T-DX-65):** el rebut és un document: no passa de `--amplada-text`, l'amplada de la ranura (`rebut-document`). Quan el cos fa 56rem o més, «Desa com a PDF» (l'únic `boto-principal`) i «Tornar al pagament» van al costat (`rebut-costat`); al mòbil, a sota, com abans.
- **Amplada (arreglat a la T-DX-11b):** el marge negatiu de `.rebut-sortida` iguala el farciment de `.cos-compte`; abans sobresortia 8 px a 320 px.

### 6.15 Vigencia: els dies que queden (T-DX-13)
Del recurs Vigencia ([pla dels recursos externs](plans/recursos-disseny-extern.md)): els dies exactes que queden sobre una regla, amb els dies d'avís marcats i la barra que canvia de color en passar-los.
- **Peça:** l'etiqueta `{% vigencia data "quota" %}` o `"llicencia"` (`apps/members/templatetags/vigencia.py`), `templates/members/_vigencia.html` i `static/css/vigencia.css`.
- **El servidor fa el compte:** dies = data − data local (`local_today`), mai el rellotge del navegador. La data és la que ja dona el servidor: «Pagada fins al» o «Eximida fins al» (070, P-71) o la caducitat de la llicència.
- **Dies d'avís:** per a la quota, els recordatoris d'abans del venciment (VC-02, l'ajust `members.fee_reminder_offsets`, que el tresorer edita a «Ajustos» des de la T-M01-32). Cap valor nou al codi. La llicència no en té cap de definit i no en porta.
- **Trams:** verd; avís des del primer dia d'avís; vermell un cop vençuda. L'escala del dibuix és de 60 dies (no és cap regla: a partir d'aquí, la barra és plena) i s'allarga si un dia d'avís és més llunyà.
- **Dibuix:** un SVG amb atributs (cap `style=`), decoratiu; el text («Queden 23 dies», «Venç avui», «Va vèncer fa 2 dies») ho diu tot.
- **On:** «Les meves quotes» i la llicència, al perfil del soci i a la fitxa de l'administració (T-DX-14), si té data de caducitat i no és declarada pendent de confirmar. La confirmació en bloc no en porta: hi surten llicències sense data. Del recurs no s'hi fa: el lliscador de temps, «Renovar» (renovar és pagar) ni l'`.ics` d'avisos.

### 6.16 Autentico: el segell de la verificació del carnet (T-DX-15)
Del recurs Autentico ([pla dels recursos externs](plans/recursos-disseny-extern.md)): un segell de goma que cau sobre el resultat, amb la icona i el color del veredicte. El resultat fa servir la superfície del tema i no el paper clar del recurs: amb el paper, al tema fosc el text d'estat no arribava al contrast mínim (axe).
- **Peça:** `templates/members/card_verify.html` (pàgina pública de verificació, T-M01-20) i `static/css/autentico.css`.
- **Segell:** «Vàlid» (✓, `--c-ok-text`) o «No vàlid» (✕, `--c-error-text`), sota les dades i a la dreta, una sola vegada amb `--m-panell` i `--m-corba-molla`. Decoratiu (`aria-hidden`): el títol ja diu el resultat. Quan la verificació està bloquejada per massa comprovacions, no hi ha segell.
- **Seguretat:** la pàgina diu exactament el mateix que abans (RN-M01-26: si és vàlid, el número i el nom de pila; si no, res). La verificació la fa el servidor amb el testimoni de l'enllaç; del recurs no s'hi fa el codi HMAC calculat al navegador, perquè la clau no pot sortir del servidor.

### 6.17 Deposito: el panell de revisió (T-DX-16)
Del panell del negoci del recurs Deposito ([pla dels recursos externs](plans/recursos-disseny-extern.md)): els comptadors de dalt i les accions de cada element en una sola fila.
- **Peça:** `static/css/deposito.css`. Comptadors `deposito-comptadors` (llista: número en xifres tabulars i text, «es-pendent» amb la vora i el número en ambre; el fons no, perquè semblaria el botó principal, D19) i fila d'accions `deposito-accions` (aprovar i rebutjar al costat, B13; el motiu del rebuig s'obre a sota a tota l'amplada). Si el formulari d'aprovar porta caselles, es desfà dins la fila (`display: contents`): les caselles a tota l'amplada i el botó al costat de «Rebutja…» (V3, T-DX-81).
- **On:** «Altes pendents» («N altes per revisar»; «Aprova l'alta» i «Rebutja…» a la mateixa fila) i «Sol·licituds» (canvis de tipus i baixes per revisar).
- **Seguretat:** cap canvi en el que es pot fer. El servidor torna a comprovar el permís en aprovar o rebutjar; el motiu continua sent obligatori.
- **Del recurs no s'hi fa:** els motius de rebuig predefinits (seria una llista de negoci, i el pla no en defineix cap) ni els comptadors de confirmades i rebutjades (caldria una consulta nova). La part de les transferències és la T-DX-12, quan existeixi la pantalla (T-M05b-06).

### 6.18 Oleaje: la portada de l'àrea del soci (T-DX-17)
Del recurs Oleaje ([pla dels recursos externs](plans/recursos-disseny-extern.md)): la secció que puja amb la vora en ona. Substitueix l'ona de la portada de la 032.
- **Peça:** `static/css/oleaje.css`. `oleaje-portada`: capçalera amb degradat marí (`--abisme` → `--casc` → `--posidonia`, interpolat en OKLCH dins de `@supports`), la salutació i, a baix, una ona SVG (`oleaje-vora`, `aria-hidden`, de `--ona-alcada`) del color del fons de la pàgina, amb una franja d'escuma. `oleaje-seccio`: el bloc de sota, amb el fons de superfície i l'ona a sobre, fora del flux, perquè no quedi cap buit.
- **Moviment:** el bloc puja i s'aclareix en entrar a la vista, lligat al desplaçament (`animation-timeline: view()`), només amb CSS. Sense suport, el bloc ja és al seu lloc. Cap animació contínua, així que no cal cap ajust per desactivar-la (D20); amb `prefers-reduced-motion`, `tokens.css` l'atura. Funció (D6): marca el canvi de secció.
- **On:** l'inici del compte personal i la portada pública de prova (Desfile). A l'inici, des de la T-DX-60 la portada només porta la salutació (el degradat és decoració) i la quota no és a `oleaje-seccio`: va a sota, sobre el fons de la pàgina, sense animació d'entrada (D20, B10).
- **L'inici del soci (T-DX-60):** dades de l'etiqueta `{% member_home as soci %}` (`apps/members/templatetags/member_notices.py`; la 00 no importa cap mòdul), amb els serveis de «Les meves quotes», «Com pago la quota» i «El meu carnet». De dalt a baix:
  - `oleaje-portada`: Monograma i salutació, res més.
  - `inici-portada`: sota la portada, sobre el fons de la pàgina i sense caixes, agrupats amb espai (D15): 7/5 quan el cos fa 56rem o més, dues columnes iguals separades amb `--e-5` a partir de 34rem, l'una a sota de l'altra per sota. A l'esquerra, «La teva quota» (`inici-quota`); a la dreta, el carnet en petit (`inici-carnet`: número, tipus, estat i «vàlid fins al», sense QR, i l'enllaç al carnet). Decisió del propietari: cap caixa sobre el degradat. El text fa 4,5:1 o més als dos temes (la prova e2e ho mesura).
  - «La teva quota»: «✓ Al dia» i «Es renova el dd/mm/aaaa» amb el mètode (domiciliació, targeta guardada o cada vegada, el de «Com pago la quota»). El compte enrere de Vigencia només des del primer dia d'avís (VC-02, `in_fee_warning_window`). Si no està al dia, l'estat de sempre; amb una quota pendent que encara no ha vençut (sense estat a `fee_state`), l'etiqueta «Pendent» del càrrec i, a sota, l'import i «venç el dd/mm/aaaa» (o «vençuda el») (V20, T-DX-77). Accions: sense pendents, «El meu carnet» (l'únic `boto-principal`, D19) i «Les meves quotes»; amb un pendent, «Paga ara» (el `boto-principal`, al costat de l'import, B13, cap al primer pendent), «El meu carnet» com a botó normal (no hi és si el soci encara no té carnet) i «Les meves quotes».
  - «El teu carnet» sense carnet (T-DX-86): «Ara no tens cap carnet.» i, amb una quota pendent, «El tindràs quan es confirmi el pagament de la quota.» (`text-2`) en lloc de «Obre el carnet», que només repetiria que no n'hi ha. Sense pendents (un carnet revocat), «Obre el carnet» es queda: allà es demana un carnet nou.
  - La franja de pendents (§6.5), només si n'hi ha.
  - Aquí anirà «Activitats per a tu» (programa de l'escriptori, PR 5).
  - `inici-graella`: 7/5 quan el cos fa 56rem o més, com `inici-portada`, perquè la història i la llicència comencin on comença el carnet (V8, T-DX-77; abans 8/4). A l'esquerra, «Pagaments recents» (les 3 quotes pagades més recents i «Totes les quotes»); a la dreta, «La teva història al C.R.I.S.» (l'antiguitat amb el filtre `antiguitat`, `apps/members/templatetags/antiguitat.py`: «Soci des de 2026» amb menys d'un any, mai «0 anys»; «Soci des de 2025 (1 any)» a partir d'un; «Soci des de ~AAAA» amb la data aproximada; el mateix text que farà servir el carnet; i la insígnia de soci clàssic amb el llindar VC-04, com el carnet; una línia diu que hi arribarà la Bitàcola) i «Llicència» (amb Vigencia, com fins ara). Separats amb espai (D15).
  - Els llindars de 34rem i 56rem són del cos i no de `graella-2` (45rem i 60rem): a la tauleta el cos no arriba mai a 45rem, i a 1024 px amb barra de desplaçament fa una mica menys de 60rem.
- **Seguretat i privacitat:** només les dades del soci de la sessió, i només al compte personal (el d'administrador no en mostra res, decisions 015 i 018). Sense soci, cap bloc. L'estat de la quota, els dies, el mètode, els pendents, els pagaments, els anys i la llicència surten del servidor (070, P-71); el navegador no calcula res. «Paga ara» porta a la pantalla de pagament, que torna a comprovar que el càrrec és del soci.
- **Del recurs no s'hi fa:** l'ona que s'agita segons la velocitat i la paral·laxi (demanarien JavaScript i una animació contínua sense una funció escrita) ni la web pública (la 07 no té pantalla encara).

### 6.19 Monograma: l'avatar per defecte (T-DX-18)
Del recurs Monograma ([pla dels recursos externs](plans/recursos-disseny-extern.md)): un avatar generatiu fet de blocs, ones o mosaic, amb paletes, que dona sempre la mateixa imatge per a la mateixa entrada. Aquí l'entrada és la llavor del soci, **mai el nom** (RN-M01-30, T-M01-11).
- **Peça:** les etiquetes `{% monograma llavor %}` i `{% session_monograma %}` (`apps/members/templatetags/monograma.py`) i `static/css/monograma.css`. El servidor dibuixa un SVG en línia de 120 × 120 a partir de l'SHA-512 de `Member.avatar_seed`: el primer octet tria el patró (blocs 3 × 3 o mosaic 5 × 5, simètrics, o ones amb un sol) i el segon, una de quatre paletes; la resta, les formes. Cada forma porta una classe (`monograma-fons`, `monograma-c1` a `monograma-c4`) i la paleta (`monograma-paleta-0` a `-3`) hi posa colors de la marca (`--abisme`, `--casc`, `--posidonia`, `--boira`, `--pissarra`, `--pissarra-fosca`, `--llauto`, `--paper`): cap color ni `style=` a l'SVG. Rodó, de `--e-8`, amb una vora fina de `--c-linia-forta` perquè el fons no es perdi sobre un fons del mateix color. `monograma-titol` el posa al costat del títol.
- **On:** la portada de l'àrea del soci (dins d'`oleaje-portada`, §6.18) i «El meu perfil», al costat del títol. Cap pantalla de l'administració.
- **Seguretat i privacitat:** només l'avatar del soci de la sessió, i a la portada només al compte personal (com el bloc de la quota, decisions 015 i 018). El dibuix surt només de la llavor, aleatòria i fixada en l'alta, així que no revela res de la persona i corregir el nom no el canvia; la llavor no surt a la pàgina. Decoratiu (`aria-hidden`, sense `title` ni text): el nom o el títol del costat són el text. Sense llavor o sense soci, res.
- **Del recurs no s'hi fa:** les inicials (sortirien del nom), «Otra variante» (l'avatar no es tria), el selector de paleta i d'estil, l'animació en canviar, ni copiar o descarregar l'SVG. Els avatars de fauna marina són el mòdul 12.

### 6.20 Icones (T-DX-58)
Un sol joc d'icones a tota la plataforma (C9, D4): **Lucide** (llicència ISC), allotjat al servidor.
- **Peça:** l'sprite `static/img/icones.svg` (un `<symbol>` per icona, només les de `apps/core/icones.py`), la classe `icona` de `tokens.css` i l'etiqueta de plantilla `{% load icones %}{% icona "nom" %}` (amb una classe més, opcional: `{% icona "nom" "classe" %}`).
- **Mida i traç:** caixa de `--icona` (20 px; 24 px a la barra de navegació del mòbil, `--icona-nav`, amb la classe `icona-nav` des de la 1.37), traç de `--icona-gruix` (1,75), que segueix el pes del text (C9). El color és el del text (`currentColor`). Cap icona no fa servir colors propis.
- **Accessibilitat:** sempre `aria-hidden="true"` i `focusable="false"`. El nom el porta el text que l'acompanya o el nom accessible del botó o de l'enllaç; una icona mai no és l'única manera de saber què fa un control ni l'estat d'una cosa (amb l'estat, també el text).
- **Origen i llicència:** `static/img/README.md` (versió, adreça oficial, integritat de npm i SHA-256) i `static/img/LICENSE-lucide.txt`. Per afegir-ne una: el nom a `apps/core/icones.py` i es torna a generar l'sprite amb `tools/icones/genera.py`, des del mateix paquet. Un nom que no és a la llista fa fallar la plantilla.
- **Els símbols de text** (✓ ✕ ◷) dels estats es mantenen on ja hi són: van amb el text de l'estat i no són icones decoratives.

### 6.21 El carnet en 3D (T-DX-61)
Decisió del propietari del 18/11/2026 (programa d'escriptori, PR 5): el carnet de soci és una targeta que s'inclina i es gira, com al wireframe `socis.html` (`carnet-escena`), però només amb tokens.
- **Peça:** `static/css/carnet.css` (enllaçat al bloc `estils` de `templates/members/personal_card.html`) i `static/js/carnet.js` (fitxer propi, `defer`, sense xarxa). `carnet-escena` > `carnet-interior` > dues `carnet-cara`: `carnet-davant` i `carnet-darrere` (`id="qr"`). Les cares són `radi-concentric` (`--r-xl` i farciment `--e-4`), amb la franja superior de `--c-carnet-zona`, el degradat `linear-gradient(in oklch, --c-carnet-1, --c-carnet-2)` amb l'alternativa en sRGB a la línia anterior (C7) i un reflex suau a dalt a l'esquerra, d'on ve la llum de l'ombra (`--ombra-carnet`, B11).
- **Davant:** el logotip per a fons fosc, «C.R.I.S.», el Monograma petit (§6.19, decoratiu, de la llavor), el nom, el número de soci (`codi`), «Vàlid fins al», «Soci des de» (any i anys de soci; «~any» si la data és aproximada), la insígnia «Soci clàssic» si toca (`carnet-insignia`) i el segell d'Autentico (§6.16) amb l'estat: «✓ Vàlid» (`--c-carnet-ok`) o «✕ No vàlid» (`--c-carnet-error`). Al carnet el segell no cau: és quiet (D20), i és text que es llegeix (no `aria-hidden`).
- **Darrere:** el QR gran sobre `--paper`, amb la zona de silenci del mateix SVG i el radi `--r-interior` (C1); el tipus, l'alta, la quota, la llicència i el text legal amb el NIF del club. Les mateixes dades d'abans, cap de nova. Amb una cara de menys de 18rem (el mòbil de 320 px), el QR va a dalt i les dades a sota, en dues columnes.
- **Gir:** el botó `carnet-gira` («Mostra el QR» / «Mostra el davant», `aria-pressed`) o un clic o toc al carnet. `--m-gir` amb `--m-corba-molla` (B5); un clic durant el gir el desfà des d'on és (B9: és una transició de CSS). La icona canvia amb opacitat, escala i desenfocament en `--m-rapid` (C4). La cara amagada porta `aria-hidden="true"` i `inert`. Amb `#qr` a l'adreça (la navegació del soci hi enllaça), la pàgina s'obre pel darrere.
- **Inclinació:** només amb `(hover: hover) and (pointer: fine)` i sense `prefers-reduced-motion`; fins a 6 graus, seguint el ratolí, amb `--rx` i `--ry` que el JavaScript posa amb `style.setProperty` (cap `style=` a la plantilla). En sortir, torna al repòs. Cap giroscopi.
- **Moviment reduït:** cap inclinació i el gir és instantani (`tokens.css` posa `--m-gir` a 0).
- **Sense JavaScript:** les dues cares, una sota l'altra, sense gir ni botó: el QR es veu igualment.
- **Pista:** la primera vegada, «Toca el carnet per veure el QR», amb la píndola i la baliza de Baliza (§16, T-DX-09; un sol batec en aparèixer). El navegador només en recorda un identificador (`localStorage`, clau `cris-pista-carnet`, P-98); si no s'hi pot escriure, no surt. Desapareix en girar el carnet.
- **Pàgina:** `graella-2 graella-7-5` (§5.3): a l'escriptori, el carnet gran a l'esquerra (fins a `--carnet-amplada` × 1,5) i, a la dreta, «Què veu qui l'escaneja», «Desa com a PDF» i «Has perdut el carnet o el mòbil?» (`id="carnet-nou"`, la navegació hi enllaça); a la tauleta i al mòbil, el carnet centrat i la resta a sota.
- **Més contrast:** sense degradat ni reflex ni ombra, i amb vora plena.
- **Seguretat i privacitat:** el QR només porta l'adreça de verificació, calculada al servidor a cada visita (resposta `no-store`); qui l'escaneja veu «vàlid», el número i el nom de pila. La cara amagada no la llegeix el lector de pantalla. Cap dada nova. La còpia sense connexió del service worker és la mateixa pàgina, amb l'avís de l'última comprovació; ara també desa els estils i el JavaScript que fa servir el carnet (`carnet.css`, `carnet.js`, `disposicio.css`, `autentico.css`, `monograma.css`, `baliza.css` i `imprimeix.js`: fitxers públics, sense dades). El logotip i les icones no hi són (només es desen `.css`, `.js` i fonts): sense connexió, el carnet surt sense.
- **Del wireframe no s'hi fa:** les isòbates (adorn que no informa, D6), els colors escrits a mà i el bloqueig de la inclinació amb un temps fix (aquí, el de `--m-gir`).

### 6.22 Conciliació: el panell de la línia triada (T-DX-72 i T-DX-73)
Programa de l'escriptori aprovat pel propietari el 18/11/2026 (secció 3.8, PR 9b).
- **Peça:** `conciliacio` a `static/css/disposicio.css` (la taula a `conciliacio-taula` i el panell `panell-linia`, amb `panell-linia-cos`) i `static/js/conciliacio.js` (fitxer propi, `defer`). El panell només existeix amb JavaScript (el guió li treu `hidden`), quan el cos fa 56rem o més (container query, C8; el CSS hi posa `--conciliacio-panell`, que llegeix el guió) i amb una línia oberta (`.amb-linia`): llavors, la taula a 8/12 i el panell a 4/12, fix en baixar, amb la vora fina a l'inici i sense caixa (D15). A 1024 px el cos, al costat de la barra lateral, no hi arriba: es comporta com la tauleta (P-316, opció A).
- **Amplada de la taula (T-DX-73):** sense cap línia oberta, la taula fa tota l'amplada i la pista de J i K és a sobre. El concepte va en una línia: s'endú l'amplada que sobra i, si no hi cap, acaba amb «…» (`max-width: 0` a la cel·la; sencer al panell, al mòbil i a la tauleta). Cada càrrec, sencer en una línia: és el que es confirma. Amb una línia oberta, la columna «Càrrecs» s'amaga: les línies que s'obren al panell no en tenen o en tenen la liquidació, que el panell mostra.
- **Estat i accions amb el panell obert (T-DX-79):** l'etiqueta d'estat i cada acció (`boto`, «Exclou…») en una línia; el motiu d'«A revisar» (`conciliacio-motiu`) va a sota de l'etiqueta, en una línia amb «…» que no eixampla la columna. Sense panell, al mòbil i a «A revisar», el motiu surt sencer.
- **Accions a l'escriptori (T-DX-85):** a partir de 1024 px, amb el panell obert o sense, cada acció de la fila (`boto`, «Exclou…», «Desfés…» i el botó del formulari) va en una línia; un formulari obert dins de la cel·la (`details[open]`) fa com a mínim la meitat de `--amplada-estreta`, perquè el motiu no quedi espremut. A la tauleta i al mòbil, com abans.
- **Obrir:** «Casa a mà…», «Casa amb moviments…», «Revisa i confirma…» i «Revisa i tria…» (`data-panell-enllac`) carreguen la mateixa vista amb HTMX (`HX-Request`) i en reben només el títol i el cos (`templates/treasury/_panell.html`). Mentre carrega, l'`esquelet` (§15.4) i «Carregant la línia…» per al lector; quan arriba, el focus va al títol del panell. La fila triada porta `aria-current` i el fons tenyit amb la vora marina. Ctrl, Maj o el botó del mig obren la pàgina com sempre.
- **Dins del panell:** la cerca i la revisió es queden al panell (`hx-get` i `hx-post` amb el CSRF del formulari). Després de cada pas, el focus va al que la plantilla marca amb `data-panell-focus` (el grup de càrrecs o de moviments per triar, o el missatge que diu que no n'hi ha cap) o, si no, al títol del panell: el botó que ha enviat el pas ja no hi és (T-DX-73); la confirmació és el POST normal i torna a la conciliació sencera amb el missatge. Un pas que acaba a la conciliació (per exemple, una liquidació que ja no és proposada) respon amb `HX-Redirect`: la pàgina no s'encasta dins del panell.
- **Tancar:** Esc o «Tanca» (`aria-keyshortcuts="Escape"`, a la dreta del títol i primer al DOM) amaguen el panell (la taula torna a tota l'amplada) i el focus torna a l'enllaç que l'ha obert. «Cancel·la» de la confirmació d'una liquidació també el tanca.
- **J i K** (de Teletipo, T-DX-39): passen a la línia següent o a l'anterior (`aria-keyshortcuts="J K"` a la taula, posat pel guió). Sense modificadors i mai dins d'un camp: no trepitgen cap drecera del navegador. Amb el panell obert, hi carreguen la línia nova si té enllaç; si no, el tanquen. La pista amb `kbd` és la de Teletipo (`teletipo-drecera`), a sobre de la taula. «Casa amb moviments» també s'obre al panell (P-317, opció A).
- **Estats:** error, accés denegat (la vista respon «no trobat») o sense xarxa: «No s'ha pogut obrir la línia», un `avis avis-error` i l'enllaç a la pàgina; HTMX no l'escriu a la consola. Sessió caducada: el servidor respon amb `HX-Redirect` i tota la pàgina va a l'entrada (o a «La sessió ha caducat»).
- **Seguretat i privacitat:** cap IBAN ni número de compte (el concepte arriba tapat per la importació). El panell no és cap control: cada vista torna a comprovar el permís T4, l'estat de la línia i el CSRF, i sense T4 no hi ha ni panell ni enllaços. Sense JavaScript, al mòbil i a la tauleta, l'enllaç porta a la pàgina, com abans.
- **Estat de les línies «a revisar»:** la píndola només diu «! A revisar» i el motiu va al costat, en text: dins d'una columna estreta, el motiu dins de la píndola en feia un oval.

### 6.23 Gastos: l'anell de segments (T-DX-106)
Del recurs Gastos ([pla dels recursos externs](plans/recursos-disseny-extern.md#9-inventari-dús)): on van els diners, en un anell de segments amb el total al mig i una llegenda. Era la peça de la pantalla en construcció «Finances per àmbit» (§16, T-DX-33) i ara és un component.
- **Peça:** l'etiqueta `{% anell_gastos segments etiqueta %}` (`apps/margins/templatetags/gastos.py`), el parcial `templates/_gastos_anell.html` i `static/css/gastos.css` (al bloc `estils`). `segments` són parelles (nom, cèntims); el servidor ordena, calcula els percentatges i els segments sobre `pathLength="100"`, i el navegador només pinta l'SVG (cap `style=`).
- **Colors:** cinc de `tokens.css` (`gastos-seg-1` a `-5`). Amb més de cinc segments, els menors s'ajunten a «Altres» (el cinquè, en `--c-text-2`), perquè un grup no passi de cinc colors (B16). Cada segment també surt en text a la llegenda: «nom · N %» i l'import, mai només color.
- **Sense moviment:** del recurs no s'hi fa el total que roda, la porció que se separa ni el filtre amb FLIP (D20).
- **On:** el marge d'una activitat (previst i real, 09): on van els costos, per categoria i el cost de material, amb «Costos» i el total al mig; al costat de les xifres a partir de 1024 px (`gastos-cols`), a sobre al mòbil, i més petit dins d'una targeta (192 px): la xifra principal és el marge (D13). Sense costos, no surt.

## 7. Temes clar i fosc
- Per defecte, la pàgina segueix `prefers-color-scheme`, la preferència de color del sistema operatiu.
- El **selector de tema** és un control segmentat de tres opcions, **Sistema / Clar / Fosc** (◐ ○ ●), fet amb botons de ràdio dins d'un `fieldset` amb la llegenda «Tema». Funciona amb el teclat (Tab i fletxes). Cada opció es veu de 32 px d'alt, però té una àrea tàctil de 44 × 44 px (§4). Als prototips, al mòbil només es veuen les icones (el text continua disponible per al lector de pantalla) i a partir de tauleta, la icona i el text. **A la plataforma (T-M01-45), la capçalera de comptes, socis i administració mostra la icona i el text a totes les mides**, com demana la revisió de pantalles; a 320 px el selector passa a la seva fila (`comptes.css`).
- Desa la tria a `localStorage` amb la clau `cris-tema` (`light` o `dark`); a «Sistema», la clau s'esborra. Si una pàgina té més d'un selector (l'administració en té un a la barra lateral del mòbil i un a la barra superior), tots dos queden sincronitzats.
- Un petit script al `<head>` aplica el tema desat abans de pintar la pàgina, perquè no es vegi el canvi. Si `localStorage` no està disponible, el selector funciona igual però no se'n recorda.
- El tema manual es fixa a `<html data-theme="light|dark">`. Els tokens foscos són dues vegades a `tokens.css`: una per a la preferència del sistema i una altra per al tema triat amb el selector.

- **Motor Duermevela (T-DX-04, 1.10).** `static/js/tema.js` (es manté el nom del fitxer) porta el motor del recurs Duermevela adaptat: (1) la tria passa a les altres pestanyes obertes amb l'esdeveniment `storage`, sense recarregar ni cortina; (2) la barra del navegador (`<meta name="theme-color">`, que crea el mateix guió) pren `--c-fons` del tema actiu, també quan el sistema canvia amb «Sistema»; (3) el canvi es revela amb una cortina circular que surt de l'opció triada (`document.startViewTransition`), de `--m-panell` i amb `--m-corba-entra-surt`. Sense l'API, amb moviment reduït o si el color no canvia (per exemple, «Sistema» quan el sistema ja demana el mateix tema), el canvi és directe. `tokens.css` treu el fos per defecte de `::view-transition-old(root)` i `::view-transition-new(root)`. La funció de la cortina (regla D6) és dir d'on ve el canvi. La il·lustració de l'habitació i el mesurador de destells del recurs no s'hi fan servir.
- **Eclipse a la part pública (T-DX-05, 1.12; decisió del propietari del 16/11/2026).** Sense sessió, la capçalera porta l'interruptor de dia i nit del recurs Eclipse (`templates/_eclipse.html`, `static/css/eclipse.css`, `static/js/eclipse.js`) en lloc del selector. En obrir la pàgina mostra el tema que es veu, és a dir, el del sistema si no s'ha triat res. Si es canvia, la tria queda fixada i surt el botó «Com el sistema», que torna a seguir el sistema. El tema el posa `tema.js` (`window.CrisTema`, amb la cortina de Duermevela que surt de l'interruptor), i l'interruptor segueix els canvis que arriben d'una altra pestanya o del sistema (esdeveniment `cris:tema`). El sol és el daurat de marca. Mida: `--selector-alcada` d'alt i àrea tàctil de 44 px amb un pseudoelement. Respecte del recurs, sense animacions infinites (D20: les estrelles no titil·len i la corona no gira) i sense l'onda pròpia de canvi de tema. Els valors que calcula el JavaScript van a variables de CSS. Amb sessió, de moment continua el selector de tres opcions; passarà a la configuració del compte a la T-DX-05b.
- **El tema a la configuració del compte (T-DX-05b, 1.13; decisió del propietari del 16/11/2026).** Amb sessió, la capçalera ja no porta cap control de tema. El selector de tres opcions (Sistema / Clar / Fosc; per defecte, «Sistema») és a la configuració del compte: a l'àrea de socis, al bloc «Aparença» de «Seguretat del compte» (`compte/seguretat/`); a l'administració, al mateix bloc de l'inici, perquè no té cap altra pàgina de configuració del compte. Peça: `templates/_selector_tema.html` (classe `selector-tema-ajust`, que mostra el text a totes les mides). Substitueix el que va decidir la T-M01-45 (selector a la capçalera, punts 2 i 6). La tria continua sent del dispositiu (`cris-tema`) i passa a les altres pestanyes. El que diuen més amunt el selector de la capçalera i la barra lateral és la història anterior a la T-DX-05b.
## 8. Logotips
| On | Fitxer |
|---|---|
| Tema clar | `assets/marca/CRIS_SenseFons.png` (text i contorns negres, fons transparent) |
| Tema fosc | `assets/marca/CRIS_Blanc_per fons Negre (Blanc).png` (text i contorns blancs, fons transparent), directament sobre el fons fosc |
| Barra lateral (fosca als dos temes) i carnet de soci (sempre fosc) | La versió per a fons fosc (`logo-sempre-fosc`) |
| Versió amb fons blanc | `assets/marca/CRIS_AmbFons.jpg` (no es fa servir als wireframes) |

Comprovat sobre `#08131e` i sobre `#062a47`: els contorns i el text blancs es llegeixen bé i «DES DE 1954» manté el contorn blanc. El canvi es fa amb les classes `logo-clar` i `logo-fosc`.

**A la web (T-DX-51; F5 de la [revisió de les portes del nivell 2](estat/portes-nivell-2.md)):** els originals d'`assets/marca/` (2717 × 2900 px, 501 i 344 KB) són la font i no surten a cap pàgina. Les pàgines fan servir les versions de `static/img/marca/`, `cris-clar-192` i `cris-fosc-192` (192 × 205 px: n'hi ha prou per als 56 px de la capçalera fins a 3x), en AVIF i WebP, amb un PNG de reserva, dins d'un `<picture>`. La classe `logo-clar` o `logo-fosc` va al `<picture>`, i la imatge porta `loading="lazy"`, `width` i `height`: el logotip del tema que no es veu (`display: none`) no es descarrega, i el selector Sistema/Clar/Fosc continua funcionant sense JavaScript nou. En total, uns 14 KB per pàgina en lloc de 845 KB. Quan una pantalla necessiti el logotip més gran (`--logo-publica`, `--logo-peu`: fins a 160 px), s'hi afegeix una versió de 320 px amb `srcset`. Comprovat a `apps/core/tests/e2e/test_logotip.py` a Chromium, Firefox i WebKit, el motor de Safari (T-DX-54): als tres, en clar, en fosc i amb el tema triat a mà, només es descarrega un logotip, i en AVIF o WebP.

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

## 15. Regles B, C i D dels recursos externs
Tres llistes de regles que valen per a **tota la interfície**: les pantalles noves i les que es toquin. Vénen amb els recursos de `design/extern/` ([pla dels recursos externs](plans/recursos-disseny-extern.md)). Es copien tal com les va donar el propietari: el nom de cada regla és l'original, en anglès, i no es tradueix ni es reanomena; l'ordre i el text no canvien. Els conflictes amb regles anteriors es resolen al [§5 del pla](plans/recursos-disseny-extern.md#5-conflictes-i-com-es-resolen).

### 15.1 Taula B. 20 Principles of UX & Animation (com s'apliquen al C.R.I.S.)
| # | Regla | Com s'aplica al C.R.I.S. |
|---|---|---|
| 1 | Squash & stretch | només en elements tàctils petits quan es premen (botó primari, Marcador, Seguir, Comanda per apuntar-se), amb una escala del 4 al 6 % com a màxim. Mai en text, imports, dates ni dades d'un soci. |
| 2 | Anticipation wind-up | una preparació breu (60–120 ms) abans dels moviments grans: obrir una pestanya nova de Solapas, desplegar Tramite o Camilla, tancar un diàleg. |
| 3 | Staging the focus | una sola cosa en focus. En obrir un diàleg de confirmació (pagar, aprovar una sol·licitud, assignar un número de soci), la resta de la pantalla queda en segon pla. Mai dues animacions grans alhora. |
| 4 | Pose to pose | cada component animat té un estat inicial i un de final amb nom (keyframes o variables CSS, i les classes d'HTMX htmx-added i htmx-settling), mai cadenes de setTimeout. |
| 5 | Follow through | les molles acaben amb un petit rebot, i els fills arriben 20–40 ms després del pare (stagger), per exemple les files d'una llista que es carrega amb HTMX. |
| 6 | Slow in & slow out | cap transició lineal, tret dels progressos continus. Tres tokens: entrada (ease-out), sortida (ease-in) i desplaçament (ease-in-out). |
| 7 | Moving in arcs | els desplaçaments llargs segueixen una corba: una activitat que «vola» cap a la icona de Marcador en guardar-la, la transició de Duermevela, l'entrada a Convite. |
| 8 | Secondary action | les partícules i els detalls només acompanyen una acció principal (guardar, apuntar-se, una fita) i mai no la tapen. |
| 9 | Snappy timing | microinteraccions de 100–200 ms, panells de 200–300 ms, i res que bloquegi més de 400 ms. Tota animació es pot interrompre. |
| 10 | Exaggerated feedback | només en moments rars i importants, com l'alta confirmada amb el carnet emès, la quota pagada o la primera inscripció a una sortida, i mai a cada clic. El d'un pagament només surt quan el servidor l'ha confirmat, mai pel navegador sol. |
| 11 | Solid drawing in 3D | el mapa 3D dels llocs d'immersió (Illes Medes, quan existeixi), Oleaje i els avatars de fauna comparteixen llum, profunditat i perspectiva, amb una sola font de llum per a les ombres. |
| 12 | Overall appeal | els avatars de fauna marina (Monograma) tenen personalitat, però no distreuen de la feina. Cap mascota inventada. |
| 13 | Fitts's law | el que més s'usa és gran i a prop de l'acció anterior: «Pagar» al costat de l'import, «Aprovar» al costat de la sol·licitud. |
| 14 | Bigger hit areas | mínim 44×44 px al mòbil (la web instal·lable és la principal per als socis) i 32×32 px a l'escriptori, mai menys de 24×24 (WCAG 2.5.8). Si la icona és petita, s'amplia l'àrea amb un pseudoelement, i les files de taula es poden clicar senceres. |
| 15 | Hick's law | poques opcions visibles alhora, i les rares sota «Més». A Ajustos, la informació es mostra a poc a poc (divulgació progressiva). |
| 16 | Miller's law | grups de 5 a 9 elements: el menú de l'administració, les targetes de Parrilla, les columnes per defecte de les taules. |
| 17 | Doherty threshold | resposta visible en menys de 400 ms. El que trigui més (importar l'extracte, preparar una remesa, generar el PDF del rebut o del carnet) mostra un esquelet o el progrés, i es pot cancel·lar si es pot. |
| 18 | Postel's law | les entrades són tolerants (dates com «dl», «15/11» o «demà»; imports com «35», «35,00», «35.00 €» o «35 €», que es desen en cèntims; telèfons amb espais o sense). La sortida és estricta, en format català: 1.234,56 € i dd/mm/aaaa. |
| 19 | Jakob's law | convencions conegudes: Ctrl+K per cercar, Esc per tancar, Ctrl+Z i desfer on el pla en preveu (per exemple, importar un extracte), doble clic per editar, arrossegar per reordenar, i un calendari com els habituals. Els registres econòmics no s'esborren mai: no tenen «Supr». |
| 20 | Frequency of use | les accions freqüents al lloc més accessible, i les rares als menús. Si cal mesurar-ho, només en local i sense enviar res enlloc. |

### 15.2 Taula C. 10 Niche Design Hacks
| # | Regla | Com s'aplica al C.R.I.S. |
|---|---|---|
| 1 | Concentric radius | radi interior = radi exterior − padding, amb una variable calculada als tokens. |
| 2 | Masked edges | mask-image amb degradat a les llistes i els panells desplaçables (moviments del tresorer, Teletipo, Solapas quan no hi caben, calendari), en lloc de tallar en sec. |
| 3 | Alpha borders | les vores, sempre amb transparència sobre el fons i mai amb grisos opacs, perquè funcionin en clar i en fosc. |
| 4 | Blurred icon swaps | quan una icona canvia (Marcador «guardar» → «guardat», Seguir → Seguint, copiar la referència de transferència → ✓), opacitat + escala + desenfocament durant 150–200 ms. |
| 5 | OKLCH palettes | tokens.css passa a oklch(), amb la mateixa lluminositat percebuda entre els colors d'estat (pagat, pendent, retornat i anul·lat; actiu, impagat i baixa). Els temes clar i fosc (Eclipse i Duermevela) només canvien L i C, sense tocar els components. Hi ha alternativa per als navegadors sense oklch, i els contrastos es tornen a comprovar després de convertir. |
| 6 | Dark mode depth | com més elevació, més clara és la superfície (no més ombra). L'ordre queda documentat als tokens. |
| 7 | OKLCH gradients | linear-gradient(in oklch, …) i radials en oklch, per evitar el gris del mig (Oleaje, capçaleres, Vistazo). |
| 8 | Dynamic viewport | dvh/dvw i container queries, perquè la web s'adapti al mòbil quan surt el teclat, en girar la pantalla o en obrir un panell. |
| 9 | Matched icon weight | el traç de les icones segueix el pes del text que acompanyen, amb un sol joc d'icones i una sola caixa. |
| 10 | Multiply blending | per a superposicions de color sobre fotos en el tema clar (Vistazo, Convite, Fototeca, Expositor); en fosc, screen o plus-lighter quan toqui. Només on aporti. |

### 15.3 Taula D. 20 Ways to Unslop AI Designs
| # | Regla | Com s'aplica al C.R.I.S. |
|---|---|---|
| 1 | Delete filler badges | fora les insígnies decoratives («Nou», «IA», «Beta»); només insígnies d'estat amb significat (pagat, pendent, retornat, actiu, impagat, baixa). |
| 2 | Add an accent colour | un sol color d'accent, el de la marca del C.R.I.S. (assets/marca/), fet servir amb mesura. |
| 3 | Drop redundant labels | fora les etiquetes que repeteixen el que ja es veu. |
| 4 | Keep icons consistent | icones coherents, d'un sol joc. |
| 5 | Unitalicize random words | cap cursiva aleatòria. |
| 6 | Remove embellishments | fora els adorns que no informen. |
| 7 | Mono only where needed | monoespai només on calgui (número de soci, referència de transferència, número de rebut). Per a les xifres, tabular-nums. |
| 8 | Inner radius = outer - padding | com a la taula C, punt 1. |
| 9 | Use a design system | cap color, radi, ombra, espai o durada escrits a mà fora de tokens.css. |
| 10 | Improve text contrast | 4,5:1 per al text normal, i 3:1 per al text gran i les icones. Cal revisar el text «suau». |
| 11 | Show the actual product | estats buits i portades amb dades de la demostració (seed_demo_data, sempre inventades) o fotos reals del club, no il·lustracions genèriques. Les fotos amb persones identificables només amb consentiment. |
| 12 | Wrap headlines properly | text-wrap: balance als títols i pretty als paràgrafs. |
| 13 | Enlarge the main feature | la funció principal de cada pantalla, més gran: a l'àrea del soci, l'estat de la quota i el carnet; a Tresoreria, el saldo i el que queda per conciliar; a Pagament, el botó de pagar. |
| 14 | Align by eye, not pixels | correcció òptica de les icones, i xifres alineades a la dreta. |
| 15 | Group with spacing | agrupar amb espai, no amb caixes i línies, i l'escala d'espais als tokens. |
| 16 | Use tabular nums | xifres tabulars a taules, imports, saldos, comptadors i dates. |
| 17 | Make headlines specific | títols concrets («2 quotes pendents de pagament», no «Tauler»). |
| 18 | Add loading states | estats de càrrega a tot el que pugui trigar (millor esquelets que un spinner sol). |
| 19 | Emphasize the CTA | un sol botó primari per pantalla. |
| 20 | Animate useful feedback | cada animació respon a una acció o a un canvi d'estat. L'única animació contínua permesa és Oleaje, lenta i desactivable, i s'atura amb prefers-reduced-motion. |

### 15.4 Tokens que concreten les regles
Tots són a `tokens.css`: els de moviment i els radis des de la T-DX-01 (amb els noms que ja existien) i els de color des de la T-DX-02.

**Moviment** (B2, B5, B6, B9, B17, C4). Amb `prefers-reduced-motion: reduce`, totes les durades passen a 0 i l'escala de premut a 1, com ja fa `tokens.css`.

| Token | Valor | Regla |
|---|---|---|
| `--m-rapid` | 180 ms | B9 i C4: microinteraccions i canvi d'icona (100–200 ms) |
| `--m-sortida` | 150 ms | B6: les sortides, més curtes que les entrades |
| `--m-panell` | 250 ms | B9: panells, diàlegs, Solapas, Tramite, Camilla (200–300 ms) |
| `--m-amplada` | 260 ms | B9: canvis d'amplada (barra lateral) |
| `--m-preparacio` | 90 ms | B2: preparació abans d'un moviment gran (60–120 ms) |
| `--m-escalonat` | 30 ms | B5: retard de cada fill respecte de l'anterior (20–40 ms) |
| `--m-llindar` | 400 ms | B9 i B17: cap animació bloqueja més; si el servidor triga més, esquelet o progrés |
| `--m-entrada` | 300 ms (abans 700) | Entrada de la portada del soci (032 revisada, B9) |
| `--m-gir` | 400 ms (abans 650) | Gir del carnet (032 revisada, B9) |
| `--m-oleaje` | 8 s per cicle | D20: l'única animació contínua, lenta |
| `--m-corba` | `cubic-bezier(.23, 1, .32, 1)` | B6: entrada, ease-out |
| `--m-corba-sortida` | `cubic-bezier(.4, 0, 1, 1)` | B6: sortida, ease-in |
| `--m-corba-entra-surt` | `cubic-bezier(.77, 0, .175, 1)` | B6: desplaçament, ease-in-out |
| `--m-corba-molla` | `linear(0, .36 18%, .81 36%, 1.04 52%, 1.06 62%, 1.01 78%, 1)`; sense suport de `linear()`, `--m-corba` | B5: rebot final petit |
| `--escala-premut` | 0.95 | B1: 5 % (entre el 4 i el 6 %) |

La 1.7 proposava `--m-icona`, `--m-corba-entrada` i `--m-corba-desplacament`: no es creen, perquè `--m-rapid`, `--m-corba` i `--m-corba-entra-surt` ja fan aquesta feina i canviar-los el nom tocaria tots els components.

**Radis concèntrics** (C1, D8). Una propietat personalitzada es resol on es declara, així que `--r-interior` no pot anar a `:root`: va a la classe `radi-concentric` del contenidor, que defineix `--r-exterior` i `--farciment`, i els fills fan servir `border-radius: var(--r-interior)`.

```css
.radi-concentric { --r-interior: max(0px, calc(var(--r-exterior) - var(--farciment))); }
```

**Color** (C3, C5, C6, C7, D2, D10). A `tokens.css` des de la T-DX-02:
- **OKLCH amb alternativa:** els colors d'estat i la superfície flotant es declaren primer en hexadecimal i després, dins de `@supports (color: oklch(0 0 0))`, en `oklch()`. L'hexadecimal és el mateix color arrodonit, així que tots els navegadors veuen el mateix. Els primitius de marca (`--abisme`, `--llauto`, `--posidonia`…) i la resta de tokens queden en hexadecimal: són exactes i no tenen res a igualar.
- **Mateixa lluminositat als estats** (`ok`, `avis`, `error`, `info` i `sistema`, que pinten pagat, pendent, retornat, anul·lat, actiu, impagat i baixa): al clar, decoratiu L 0,42, text L 0,33 i fons tenyit L 0,84; al fosc, decoratiu i text L 0,80 i fons tenyit L 0,31. El to (H) de cada estat és el mateix als dos temes. El fons tenyit de l'avís al clar continua sent el daurat de marca (`--llauto`, L 0,84).
- **Vores amb transparència:** dins de `@supports (color: color-mix(in oklch, red, blue))`, `--c-linia` és el color del text amb un 14 % (clar) o un 20 % (fosc), que fa 1,3:1 com abans, i `--c-linia-forta` amb un 68 % (clar) o un 48 % (fosc), que dona 3:1 o més sobre el fons, el contenidor i el pou (WCAG 1.4.11). Sense `color-mix()`, els hexadecimals d'abans.
- **Profunditat al fosc:** l'ordre d'elevació és `--c-fons` (0) < `--c-superficie-2` (el pou intermedi) < `--c-superficie` (1: targetes) < `--c-superficie-flotant` (2, nou: menús, diàlegs, avisos). Al fosc, cada nivell és més clar que l'anterior (L 0,24, 0,28, 0,33 i 0,37) i l'ombra no creix. Al clar, la flotant és la més clara (L 0,90) i l'ombra fa la resta. (La 1.7 posava el pou per sobre del contenidor: era un error.)
- **Degradats:** els nous, en `linear-gradient(in oklch, …)` o `radial-gradient(in oklch, …)`, amb un degradat en sRGB a la línia anterior com a alternativa. Els que ja hi ha són gairebé neutres (blancs i transparents sobre el mateix to) i ja barregen en `oklab`: no tenen gris al mig i no es canvien.
- **Accent:** un de sol, `--c-accent` (el daurat de `tokens.css`). Si és o no el color del logotip depèn de la decisió de la paleta, encara pendent (§2) [A validar].
- **Contrast:** el text d'estat fa com a mínim 4,82:1 i el decoratiu 3,32:1 sobre el fons, el contenidor, el pou i el seu fons tenyit, als dos temes. Ho comprova `apps/core/tests/test_tokens_color.py`, que també vigila que l'hexadecimal i l'`oklch()` siguin el mateix color.

**Xifres** (D7, D14, D16). `font-variant-numeric: tabular-nums` a taules, imports, saldos, comptadors i dates, alineats a la dreta. Monoespai (`--f-codi`) només per al número de soci, la referència de transferència i el número de rebut: els imports deixen de ser monoespai.

**Estats de càrrega** (B17, D18, D20). Classe `esquelet` (a `comptes.css` des de la T-DX-72, amb `esquelet-bloc`, `esquelet-titol` i `esquelet-curt`): blocs de la forma del contingut, de color `--c-superficie-2`, **estàtics** (sense brillantor que es mogui, per D20). Es mostren al moment de la petició (`htmx-request`); si el procés pot superar `--m-llindar`, una barra de progrés i «Cancel·la» quan es pot.

### 15.5 Comprovació per a cada pantalla nova
Abans de donar per acabada una pantalla nova o tocada, es comprova i s'anota al diari de construcció:
1. **Taula B:** cap animació bloqueja més de 400 ms ni s'encavalca amb una altra de gran; totes es poden interrompre i fan servir els tokens de moviment; amb `prefers-reduced-motion` no es mou res. Àrees tàctils de 44×44 px al mòbil i 32×32 px a l'escriptori. Un sol focus en els diàlegs. Entrades tolerants i sortida en format català.
2. **Taula C:** radis interiors amb `--r-interior`; vores amb transparència; llistes desplaçables amb vora emmascarada; alçades amb `dvh`; icones del joc comú amb el traç del text.
3. **Taula D:** cap insígnia decorativa; un sol botó primari; títols concrets; xifres tabulars; monoespai només on toca; estats buits amb dades de la demostració; esquelet a tot el que pot trigar; contrast 4,5:1 i 3:1 als dos temes.
4. **Tokens:** cap color, radi, ombra, espai ni durada fora de `tokens.css`; cap `style=`.
5. **Captures** a 1280 i 390 px, en clar i en fosc, mirades.

## 16. Pantalles «En construcció»
Com es fa una pantalla del carril de disseny que encara no funciona (etiqueta i control al servidor: §6.9). **Feta a la T-DX-09.**
- **Una pantalla, fitxers nous i res més:** `apps/previews/screens/<nom>.py` (amb `TITLE`, traduïble, i, si cal, `CONTEXT`, contingut d'exemple inventat i fix, mai cap consulta), `templates/previews/<nom>.html` i, si cal, `static/css/<recurs>.css`, que la plantilla enllaça al bloc `estils` de la base. La ruta és `/en-construccio/<nom>/` (els «_» passen a «-»), i l'índex de totes és a `/en-construccio/`. Rutes, índex i proves les troben soles: afegir una pantalla no toca cap fitxer de codi comú, i diverses pantalles es poden fer alhora (decisió 094, punt 3).
- **La plantilla:** el contingut va dins d'un `en-construccio-bloc` amb l'etiqueta (`{% include "_en_construccio.html" with id="ec-<nom>" %}`) i `aria-describedby`; els formularis i els botons que farien alguna cosa, dins d'un `fieldset disabled`. Només classes i tokens del sistema; una peça nova, primer en aquest document: una subsecció per pantalla, titulada amb el número de la tasca («### T-DX-NN Recurs: pantalla»), perquè diverses pantalles fetes alhora no xoquin.
- **Proves, comunes:** `apps/previews/tests/test_screens.py` (títol i plantilla, etiqueta, cap `style=`, només GET, 404 sense accés, a l'índex) i `apps/core/tests/e2e/test_previews.py` (etiqueta visible i captures a 1280, 390 i 320 px, en clar i en fosc). Quan la pantalla es torna funcional, el fitxer surt de `apps/previews/screens` i les proves de la tasca la cobreixen.
- **Al menú (T-DX-50):** «Pantalles en construcció», a l'administració, només amb el permís DX1 (`core.under_construction.view`, P-90), encara que `SHOW_UNDER_CONSTRUCTION` les ensenyi a tothom. Les pantalles també es munten a `/<administració>/en-construccio/` (espai de noms `administration:previews`): un compte d'administrador és a la zona d'administració, i a `/en-construccio/` (zona de socis) rebria un 401, de manera que a producció el permís no servia de res. L'índex enllaça les pantalles del mateix espai de noms d'on s'obre, i l'entrada del menú queda marcada a totes.

### T-DX-09 Baliza: novetats i avisos
Del recurs Baliza ([pla dels recursos externs](plans/recursos-disseny-extern.md)): la baliza al costat del que és nou, la nota que s'obre i la píndola amb el comptador. Lloc: el centre d'avisos del soci (P-98, resposta C).
- **Peça:** `static/css/baliza.css`. `baliza-pindola` (comptador «N novetats per descobrir»), `baliza-punt` (la baliza, de `--c-accent`, amb **un sol batec en aparèixer**, no continu, D20) i `baliza-item` (un `details` per novetat: la nota i «Entès» s'obren a sota; les vistes, amb ✓ i el text secundari).
- **Pantalla:** `/en-construccio/novetats/`, «Novetats i avisos», a l'àrea del soci, amb tres novetats d'exemple.
- **Quan funcioni:** una novetat no mostrarà mai dades d'una altra persona, i el navegador només recordarà quins identificadors s'han vist (pla dels recursos externs). «Entès» i les preferències (Avisador) són d'aquella tasca.
- **Del recurs no s'hi fa:** el batec continu (D20), el marc que ensenya un element de la pantalla ni «Amagar consells».

### T-DX-27 Vistazo: projectes
Del recurs Vistazo ([pla dels recursos externs](plans/recursos-disseny-extern.md)): l'índex en files grans, les altres files que s'apaguen i la finestra amb la imatge que apareix amb un rebot. Lloc: els projectes del Departament d'Història (11).
- **Peça:** `static/css/vistazo.css`. `vistazo-fila` (un `details` per projecte: número, nom, tipus; obert, la imatge i la nota), `vistazo-finestra` (de tauleta amunt, en passar-hi per sobre o amb el focus, decorativa i darrere del text) i `vistazo-imatge` (a la fila oberta; al mòbil, el primer toc la mostra). En lloc de foto, degradats en OKLCH dels tokens d'estat (`vistazo-to-1` a `-4`, C7).
- **Pantalla:** `/en-construccio/projectes/`, «Projectes», a l'àrea del soci, amb quatre projectes d'exemple.
- **Quan funcioni:** projectes i fotos com a dades; només fotos amb el consentiment de les persones que s'hi reconeixen (T-M01-08, P-41), sense EXIF i desades a la UE.
- **Del recurs no s'hi fa:** la finestra que segueix el cursor i s'inclina amb la velocitat (cal JavaScript continu), la cortina entre fotos ni les fotos de la demostració (D11).
### T-DX-28 Recoveco: ajuda i preguntes freqüents
Del recurs Recoveco ([pla dels recursos externs](plans/recursos-disseny-extern.md)): l'índex de temes amb el número romà i el comptador, les preguntes plegades per tema i la cerca del navegador que obre la resposta. Lloc: l'ajuda de l'àrea del soci (i, amb la mateixa peça, la de l'administració i les preguntes freqüents de la web pública, 07).
- **Peça:** `static/css/recoveco.css`. `recoveco-index` (temes amb `recoveco-rom` i el nombre de preguntes; a l'escriptori, a l'esquerra i fix en desplaçar), `recoveco-grup` (un tema) i `recoveco-p` (un `details` per pregunta, amb `name` per tema: obrir-ne una tanca l'anterior; la ratlla marina i el «+» que es torna «−»). La drecera que es mostra és <kbd>Ctrl</kbd> <kbd>F</kbd> (B19; al Mac, ⌘F).
- **Pantalla:** `/en-construccio/ajuda/`, «Ajuda i preguntes freqüents», a l'àrea del soci, amb tres temes i sis preguntes d'exemple. La cerca pròpia i «Copiar l'enllaç a aquesta resposta» van dins d'un `fieldset disabled`.
- **Quan funcioni:** preguntes i respostes com a dades editables (regla «Valors i llistes»); cap resposta no revela dades d'un compte ni si un correu hi és registrat.
- **Del recurs no s'hi fa:** el cercador propi amb comptador i fletxes, «Copiar l'enllaç» amb el subratllat de la frase exacta (cal JavaScript; per a quan funcioni) ni les dreceres `/`, `R` i les fletxes.
### T-DX-23 Horario: calendari general
Del recurs Horario ([pla dels recursos externs](plans/recursos-disseny-extern.md)): la setmana en graella, cada activitat com un bloc a la seva hora i les hores que es trepitgen ratllades. Lloc: el calendari general del soci (§4 del pla). Solape (els xocs entre els calendaris del club, a l'administració) és un pas posterior i no es fa aquí.
- **Peça:** `static/css/horario.css`. `horario-graella` (regle d'hores i set columnes, a partir de 1024 px; al mòbil i a la tauleta, una agenda per dies), `horario-acte` (el bloc; `es-inscrit` amb el fons d'estat correcte i ✓, `es-xoc` amb la vora d'avís), `horario-tope` (la franja ratllada de `--c-avis` a les hores exactes del xoc) i `horario-llegenda`. Les files són classes per tram (`h08`–`h21` per a l'hora d'inici, `d1`–`d6` per a les hores), perquè la plantilla no porti cap `style=`. Pantalla ampla (`cos-ample`).
- **Pantalla:** `/en-construccio/calendari/`, «Calendari», a l'àrea del soci: una setmana d'exemple (abril del 2027) amb dues sortides, un curs, un entrenament i una xerrada, i un encavalcament explicat en text a l'avís.
- **Quan funcioni:** el soci només veu les activitats publicades i les seves inscripcions, mai qui més hi va (si la 02 no ho permet). Els encavalcaments els calcula el servidor; el navegador només mostra l'avís abans d'apuntar-se. La vista per defecte (setmana o mes) serà un ajust.
- **Del recurs no s'hi fa:** triar el grup de cada assignatura, la cerca de combinacions ni l'animació del ratllat; Solape (lectura de `.ics`, «Moure», «Ometre», exportar) queda per a la seva tasca.
### T-DX-19 Avisador: rols i permisos
Del recurs Avisador ([pla dels recursos externs](plans/recursos-disseny-extern.md)): la matriu, el resum «en paraules» que acompanya cada canvi i les files bloquejades. Aquí la matriu és permís × rol, no avís × canal. Lloc: l'editor de permisos (T-RP-03).
- **Peça:** `static/css/avisador.css`. La matriu és una `taula` (apilada al mòbil, amb el rol a cada cel·la) amb un `select` per cel·la; la cel·la canviada porta la vora daurada i «abans: …» en text (`es-canviada`), i la fila protegida, «■ Protegit: només l'Administrador» (`es-protegida`). A sota, dues `targeta`: «En paraules» (cada cel·la que canvia i els comptes afectats) i «Desa els canvis» (nota, codi TOTP, casella de revisió, «Desa els canvis» i «Torna a la configuració inicial…»).
- **Pantalla:** `/gestio/permisos/`, «Rols i permisos», a l'administració (T-RP-03). La pantalla en construcció (`/en-construccio/rols-permisos/`) es va retirar a la T-DX-74, quan la real ja funcionava (§6.9).
- **Quan funcioni:** només el rol Administrador obre l'editor (M3b, protegit; la resta, «no trobat», CA-RP-03). Desar demana el TOTP i la nota (RN-RP-06, CA-RP-04) i el resum confirmat amb cada cel·la i cada compte afectat (RN-RP-07); cada canvi deixa una versió de la matriu i una entrada al registre per cel·la, i s'avisa per correu (RN-RP-08 i 09). Les regles protegides no tenen cap control (RN-RP-05, CA-RP-09) i cap canvi no pot deixar menys d'un administrador operatiu (RN-RP-13). «Torna a la configuració inicial» és un canvi més, amb resum i nota. El servidor ho torna a comprovar tot en desar; amagar un control no ho és.
- **Del recurs no s'hi fa:** la vista prèvia de cada canal (és de les preferències d'avisos, no dels permisos), «Només l'important» (seria un canvi de permisos com qualsevol altre, sense regla al pla) ni el resum que es reescriu al navegador (el calcularà el servidor).
### T-DX-24 Camilla i Comanda: inscripció a una activitat
Dels recursos Camilla i Comanda ([pla dels recursos externs](plans/recursos-disseny-extern.md); [P-94](decisions/pendents.md), resposta A): Camilla és el flux d'inscripció per passos i Comanda, les opcions de cada activitat amb les seves regles i el botó que no s'encén fins que tot val.
- **Peces:** `static/css/camilla.css`: `camilla-passos` (la línia de passos de Tramite, §6.13, amb quatre: Activitat, Sessió, Opcions, Confirmar; el pas actual porta `aria-current="step"`), `camilla-sessio` (la sessió triada, en un `details` que s'obre per canviar-la) i `camilla-franja` (una sessió; `es-completa` apagada i ratllada, amb el text «Completa»). `static/css/comanda.css`: `comanda-grup` (un `fieldset` per grup, amb el nom, la regla «Tria'n un» o «Tria'n fins a 3» i l'estat del grup; `es-incomplet` amb la vora d'avís), `comanda-total` i `comanda-continua` (el botó principal amb `aria-disabled` i el motiu en text, `comanda-falta`, lligat amb `aria-describedby`).
- **Pantalla (retirada, T-DX-95: la real és `activities:member_enrol` i `activities:guest_enrol`; la peça es queda):** `/en-construccio/inscripcio/`, «Inscripció a una activitat», a l'àrea del soci: la Sortida a les Medes al pas 3, tres grups d'opcions (material de lloguer, vestit i transport, aquest per triar), el total i «Les meves inscripcions» (el «Les meves cites» del recurs).
- **Quan funcioni:** cap camp de salut a cap pas ni a cap opció. Les regles de les opcions, les places que queden, els imports (en cèntims) i el total els calcula i els valida el servidor; el navegador només encén el botó. Un no soci s'inscriu com a convidat amb un enllaç segur (decisió 021) i el pas de les dades només li demana les mínimes; el soci no n'ha d'escriure cap. El pagament el fan Tramite i Deposito; l'`.ics` del pas final es genera al servidor i no porta dades de cap persona. Les opcions i les regles de cada activitat seran dades.
- **Del recurs no s'hi fa:** les especialitats, els professionals i les dades del pacient de Camilla (és una clínica), el telèfon que l'emmarca, ni la cuina simulada, les taules ni els rellotges de Comanda.
### T-DX-21 Cartola: pendents per antiguitat
Del recurs Cartola ([pla dels recursos externs](plans/recursos-disseny-extern.md)): una fila per soci, una columna per tram de dies i una fitxa per càrrec, amb els filtres per estat i l'exportació. **Pantalla proposada:** el pla no la té (D1), i els trams (0–30, 31–60 i més de 60 dies, els del recurs) són d'exemple fins que una decisió els fixi. Lloc: tresoreria, càrrecs pendents i retornats (05b).
- **Peça:** `static/css/cartola.css`. Els totals de cada tram reutilitzen els comptadors de Deposito (§6.17; el tram més antic, «es-pendent», en ambre). La matriu és una `taula` (apilada al mòbil, amb el tram a cada cel·la) i cada càrrec, una fitxa `cartola-fitxes` amb el concepte, l'`import` i l'`estat` («◷ Pendent» o «✕ Retornat»). Filtre per estat amb el `segmentat` i «Exporta CSV», desactivats.
- **Pantalla:** `/en-construccio/pendents-antiguitat/`, «Pendents per antiguitat», a l'administració, amb quatre socis inventats (número i nom de pila).
- **Quan funcioni:** només tresoreria (T1; la resta, «no trobat»). Els trams, les xifres i els estats els calcularà el servidor (imports en cèntims). Cap IBAN ni dada bancària. L'exportació demanarà el seu permís i deixarà una entrada al registre d'activitat.
- **Del recurs no s'hi fa:** la «disputa» (el pla no té aquest estat), aïllar un soci tocant-ne el nom ni el detall que s'obre (caldria JavaScript i la fitxa del soci ja existeix).
### T-DX-35 Parrilla: dashboard
Del recurs Parrilla ([pla dels recursos externs](plans/recursos-disseny-extern.md)): la reixa de ginys de dotze columnes, la capçalera de cada giny (agafador, nom, etiqueta i «Treure»), el tirador de la mida, la paleta de ginys i la disposició com a dades. Lloc: el dashboard de l'administració (08).
- **Peça:** `static/css/parrilla.css` i `templates/previews/_parrilla_cap.html` (la capçalera i el tirador). `parrilla-giny` amb l'amplada `parrilla-amp-3` a `-6` (columnes de la reixa a l'escriptori; dues columnes a la tauleta i una al mòbil), i els continguts d'exemple: `parrilla-xifra`, `parrilla-barres` (SVG), `parrilla-anell` (SVG, percentatge), `parrilla-calor` (quatre nivells del marí, no és cap estat) i `parrilla-llista`. Al costat, `parrilla-panell`: la paleta i la disposició `[x, y, amplada, alçada]`.
- **Pantalla:** `/en-construccio/dashboard/`, «Dashboard», a l'administració, amb cinc ginys d'exemple. «Restaurar», «Desar la disposició», la paleta i els botons dels ginys van dins d'un `fieldset disabled`.
- **Quan funcioni:** només xifres agregades (recomptes i percentatges): veure el dashboard no dona accés a cap dada personal, ni cap giny no enllaça a la fitxa d'una persona. La disposició es desa per compte al servidor, com a dades.
- **Del recurs no s'hi fa:** arrossegar, encaixar i redimensionar amb el ratolí o les fletxes, els veïns que s'aparten amb ressort ni el vol de «Restaurar» (cal JavaScript; per a quan funcioni, amb una sola animació curta, D20).
### T-DX-25 Marcador: activitats guardades
Del recurs Marcador ([pla dels recursos externs](plans/recursos-disseny-extern.md)): la cinta de punt de llibre que cau del cantell de la targeta quan es guarda una activitat. Lloc: guardar activitats, per als socis i els no socis (§4 del pla).
- **Peça:** `static/css/marcador.css` i `templates/previews/_marcador_targeta.html`. `marcador-targeta` (una `targeta` amb el tipus, la data, les places i el botó), `marcador-cinta` (la cinta de `--c-accent` amb l'osca en V, `aria-hidden`, que **cau una sola vegada en aparèixer** amb `--m-corba-molla`, B5 i B8) i `marcador-boto` (`aria-pressed`: «Guarda» o «✓ Guardada», amb el títol de l'activitat per al lector de pantalla).
- **Pantalla:** `/en-construccio/guardades/`, «Activitats guardades», a l'àrea del soci: dues guardades i dues properes per guardar.
- **Quan funcioni:** per als socis, el que guarden es desa al servidor; per als no socis, només els identificadors de les activitats al `localStorage`, sense cap dada personal i sense compte (pla dels recursos externs, §3.6). Les places que queden les diu el servidor i mai qui hi va. El canvi de «Guarda» a «Guardada» farà el canvi d'icona amb desenfocament (C4).
- **Del recurs no s'hi fa:** la física de cadena, el balanceig, la tinta que l'amara ni l'enrotllament en treure-la (demanarien JavaScript i un llenç); el butlletí «avisa'm quan s'obri» és de la web pública.
### T-DX-30 Reasigna: reassignar sessions
Del recurs Reasigna ([pla dels recursos externs](plans/recursos-disseny-extern.md)): marcar qui falta, la proposta de cada sessió («→ qui» o «sense lloc»), el marge d'hora i confirmar-ho tot alhora. Lloc: el calendari de l'administració, sessions d'un instructor que falta (mòdul 02, aparcat, D6).
- **Peça:** `static/css/reasigna.css`. L'agenda del dia és una `taula` (apilada al mòbil) amb les sessions de qui falta marcades amb una vora ambre i «! Falta» (`es-afectada`); la columna «Proposta» diu «→ nom (marge)», «✕ Sense lloc» (`estat-error`) o «—». Al costat a l'escriptori i a sota al mòbil, la `targeta` «Què es mou»: el marge d'hora amb el `segmentat` (mateixa hora, ± 30 min, ± 1 h), la llista dels moviments en frases i «Confirma els canvis» i «Desfés», desactivats.
- **Pantalla:** `/en-construccio/reassignar/`, «Reassignar sessions», a l'administració, amb un dia i tres instructors inventats.
- **Quan funcioni:** només qui gestiona activitats; l'instructor només veu les seves sessions. La proposta la calcularà el servidor (qui pot fer la mateixa sessió i té l'hora lliure) i res no canviarà fins a «Confirma els canvis»; reassignar avisarà els afectats i quedarà al registre d'activitat. El marge d'hora serà un ajust.
- **Del recurs no s'hi fa:** el vol de les cites d'una columna a l'altra (moviment sense funció, D6 de la taula D), canviar cada proposta a mà ni passar una sessió a un altre dia (caldria el calendari, T-DX-23).
### T-DX-36 Probador i Pregon: editor de la web
Dels recursos Probador i Pregon ([pla dels recursos externs](plans/recursos-disseny-extern.md)): la galeria de plantilles com a miniatures vives, el marc d'escriptori amb els botons de dispositiu i el color d'accent (Probador), i la vista en compartir amb el comptador de caràcters en anell i les tres targetes que es reescriuen alhora (Pregon). Lloc: l'editor i la configuració de la web pública a l'administració (07).
- **Peça:** `static/css/probador.css` (`probador-miniatura`, `probador-mini` i la variant gran `es-gran` dins de `probador-marc`, `probador-color` amb `probador-mostra-<token>`) i `static/css/pregon.css` (`pregon-compte`, `pregon-targeta` en tres formes: `pregon-bombolla`, `pregon-caixa`, `pregon-fila`). Peces de plantilla: `_probador_mini.html` (blocs genèrics, cap imatge), `_pregon_compte.html` (anell amb `pathLength=100`) i `_pregon_imatge.html` (il·lustració decorativa amb els tokens). El dispositiu és un `segmentat`; el color triat porta anella i negreta, mai només el color.
- **Pantalla:** `/en-construccio/editor-web/`, «Editor de la web», a l'administració, amb tres plantilles i un text d'exemple per compartir. Tots els controls, «Copiar les etiquetes» i «Publicar» van dins d'un `fieldset disabled`.
- **Quan funcioni:** només qui té el permís d'editar la web; plantilles i colors com a dades, i el color només pot ser un token; les etiquetes `meta` es generen al servidor; publicar demana permís i les imatges, el consentiment de les persones que s'hi reconeixen.
- **Del recurs no s'hi fa:** el lliscador de matís lliure, l'obertura FLIP fins al marc, el marc que s'estreny amb ressort, el punt focal arrossegable de la imatge ni el text que es reescriu lletra a lletra (cal JavaScript; per a quan funcioni).
### T-DX-26 Desfile i Oleaje: portada de la web pública
Dels recursos Desfile i Oleaje ([pla dels recursos externs](plans/recursos-disseny-extern.md)): la capçalera amb l'ona (Oleaje, §6.18) i, a sota, el carril de les properes activitats (Desfile). Lloc: la portada de la web pública (§6.5 del pla).
- **Peça:** `static/css/desfile.css`. Oleaje no es copia: la pantalla fa servir les classes de `oleaje.css` (`oleaje-portada`, `oleaje-vora`, `oleaje-seccio`, `oleaje-contingut`). `desfile-pista` (llista amb `scroll-snap` del navegador, que es pot enfocar amb el teclat, una targeta i un tros al mòbil, dues a la tauleta i tres a l'escriptori, i la vora de la dreta emmascarada, C2), `desfile-targeta` (tipus, títol, data i preu d'exemple), `desfile-controls` (comptador «1 / 5» i fletxes) i `desfile-progres` (un `<progress>` amb el color d'accent). Zona pública (`zona-publica`) i pantalla ampla.
- **Pantalla:** `/en-construccio/portada-publica/`, «Portada de la web pública»: la capçalera amb «Fes-te soci» i cinc activitats d'exemple. Es veu dins de l'àrea del soci perquè les pantalles en construcció demanen sessió; la de debò serà pública i sense sessió.
- **Quan funcioni:** **sense avanç automàtic** (D20); si mai s'encén com a ajust, porta el botó Pausa del recurs. El comptador, la barra i les fletxes surten de la posició real del carril (JavaScript que només anima; sense JavaScript, el carril es desplaça igual). Les targetes fora de vista, inertes. Només activitats publicades, sense dir qui hi va; preus en format català. Fotos només amb consentiment (P-41) i sense persones identificables si no n'hi ha.
- **Del recurs no s'hi fa:** l'avanç automàtic i la pausa, les fotos d'arxiu, el ✓ en recórrer-lo sencer ni el botó «Guardar» (és Marcador, T-DX-25); d'Oleaje, l'ona que s'agita amb la velocitat i la paral·laxi.
### T-DX-32 Averia: comunicar una avaria del material
Del recurs Averia ([pla dels recursos externs](plans/recursos-disseny-extern.md)): triar el tipus d'equip, les preguntes que porta cada tipus, explicar-ho amb paraules pròpies i afegir-hi fotos. **Pantalla proposada:** el pla té l'estat «a revisió» d'una peça (P-M03-D i P-M03-F), però no aquest formulari ni les preguntes per tipus (D1). Lloc: material (03).
- **Peça:** `static/css/averia.css`. El tipus amb el `segmentat`; la peça amb un `select` (codi `MAT-NNNN` i tipus); les preguntes del tipus, cadascuna amb un `segmentat` «Sí / No», dins d'un grup amb vora; la descripció i les fotos amb `camp`. Al costat a l'escriptori i a sota al mòbil, la `targeta` «La peça» amb `dades-soci` (codi, tipus, estat i propera revisió). Tot desactivat.
- **Pantalla:** `/en-construccio/avaries-material/`, «Comunicar una avaria», a l'administració, amb un regulador inventat i tres preguntes d'exemple.
- **Quan funcioni:** només els rols amb permís sobre el material. Les preguntes de cada tipus seran dades, no codi. Les fotos es validaran pel contingut (`core.validate_upload`) i se'n traurà l'EXIF al servidor, encara que el navegador ja ho faci; només la peça, sense persones identificables ni cap dada de salut. Passar la peça a revisió continua sent del responsable de material (P-M03-F), i mentre hi és no es pot assignar.
- **Del recurs no s'hi fa:** la franja de visita i el folio (són d'un servei tècnic, no del club), ni la reducció de les fotos al navegador amb un llenç (vindrà amb la pujada real, com a ajuda i no com a control).
### T-DX-33 Gastos: finances per àmbit
Del recurs Gastos ([pla dels recursos externs](plans/recursos-disseny-extern.md)): l'anell de segments amb el total al mig, la llegenda per categoria i el canvi de mes; aquí les categories són els àmbits (centres de cost). Lloc: finances, ingressos, despeses i resultat per àmbit (mòdul 09).
- **Peça:** `static/css/gastos.css`. L'anell és SVG amb atributs (`pathLength="100"`, `stroke-dasharray` i `stroke-dashoffset` calculats al servidor; cap `style=`), amb un color de `tokens.css` per segment (`gastos-seg-N`) i cada àmbit també en text a la llegenda («nom · N %»), mai només color. Al costat a l'escriptori i a sota al mòbil, una `taula` amb ingressos, despeses i resultat (`import` i `cel-import`; el resultat amb signe «+» o «−» i `import-entrada` o `import-sortida`) i la fila del total. A dalt, el mes amb les fletxes i «Registra una despesa», desactivats.
- **Pantalla:** `/en-construccio/finances-ambit/`, «Finances per àmbit», a l'administració, amb un mes i quatre àmbits d'exemple; els imports surten en format català (`1.234,56 €`).
- **Quan funcioni:** només tresoreria i junta (la resta, «no trobat»). Imports en cèntims, sumats al servidor; tot ingrés i tota despesa té departament i les comissions de les quotes van a «General / Quotes de socis». El marge d'una activitat és ingressos − despeses − cost de material; aquí és el resultat de l'àmbit. Cap dada personal. Els àmbits són la llista de departaments, que encara no és fixada (Q-17): els que no són «General» són d'exemple.
- **Del recurs no s'hi fa:** el total que roda com un comptaquilòmetres, la porció que se separa i la llista que es filtra amb FLIP (moviment sense funció, D20), ni «Afegir despesa» que fa créixer la porció (registrar una despesa és del 09, amb factura i departament).
### T-DX-37 Fototeca i Expositor: fotos
Dels recursos Fototeca i Expositor ([pla dels recursos externs](plans/recursos-disseny-extern.md)): la biblioteca amb el lateral de carpetes i l'espai, la graella amb la selecció i el panell de detalls (Fototeca), i la graella de pujada amb l'anell, la foto massa petita ratllada amb el motiu i «Fer portada» (Expositor). Lloc: les fotos de l'àrea del soci (12; les d'una activitat o d'un projecte, 07, amb la mateixa peça).
- **Peça:** `static/css/fototeca.css` (`fototeca-carpeta`, `fototeca-foto` amb la casella amagada i la marca ✓, `fototeca-detall`, i els degradats `fotos-to-1` a `-4` que fan de foto) i `static/css/expositor.css` (`expositor-cel` amb `es-llesta`, `es-pujant` i `es-petita`, `expositor-portada`, `expositor-anell`). La zona de pujada és la `zona-magnetica` existent. L'estat de cada foto és una `estat` amb text i símbol, mai només el color; la ratllada porta el motiu escrit.
- **Pantalla:** `/en-construccio/fotos/`, «Fotos», a l'àrea del soci, amb tres carpetes, sis fotos i quatre pujades d'exemple. Tot va dins de `fieldset disabled`.
- **Quan funcioni:** fotos a l'emmagatzematge de París; EXIF fora al servidor; persones identificables només amb consentiment (T-M01-08; cal la resposta de P-41 abans de fer-les funcionals); cap dada de salut; la mida mínima com a dada.
- **Del recurs no s'hi fa:** el rectangle elàstic, el ventall cap a la carpeta, «Desfer», reordenar arrossegant ni el creuament de «Fer portada» (cal JavaScript), ni les fotos de la demostració (D11).
### T-DX-29 Asueto: calendari d'un dia
Del recurs Asueto ([pla dels recursos externs](plans/recursos-disseny-extern.md)): el dia concret amb les nanses d'obrir i tancar, el dia tancat, les activitats que ja no hi caben ratllades amb la primera hora lliure, «Mou-la» i «Aplica». Lloc: el calendari d'un dia de l'administració (§4 i §6.4 del pla).
- **Peça:** `static/css/asueto.css`. `asueto-excepcio` (el control segmentat «Com sempre», «Un altre horari» o «Tancat», les hores i el motiu), `asueto-linia` (la línia del dia, `aria-hidden`: l'horari habitual amb vora discontínua, el que queda obert amb les dues nanses i cada activitat com una barra; `es-fora` ratllada amb `--c-avis`, com a Horario), `asueto-acte` (la mateixa informació en text, amb l'estat, la primera hora lliure i «Mou-la») i `asueto-accions` («Restableix» i «Aplica l'excepció»). Les columnes són classes per tram (`c17`–`c22`, `s1`–`s6`). Pantalla ampla.
- **Pantalla:** `/en-construccio/calendari-dia/`, «Calendari d'un dia», a l'administració: un dimecres d'exemple que tanca a les 19:00 per una assemblea i dues activitats que en queden fora.
- **Quan funcioni:** l'excepció s'aplica al servidor i res no es mou fins a «Aplica»; la primera hora lliure la calcula el servidor sense trepitjar cap altra activitat. Moure una activitat avisa les persones inscrites. Només qui gestiona activitats ho pot fer (permís de la 02, amb motiu i registre d'activitat). L'horari del local serà un ajust.
- **Del recurs no s'hi fa:** arrossegar les nanses (demanaria JavaScript; quan funcioni, el teclat i les hores escrites també hi seran), el mes amb els dies afectats ni la llista de dies amb excepció.
### T-DX-39 Teletipo i Amanuense: xats
Del recurs Teletipo ([pla dels recursos externs](plans/recursos-disseny-extern.md)), la carcassa dels xats (P-97, resposta A): el lateral de converses amb els comptadors, el rotlle de missatges en tires, «Tot llegit» i J/K. D'Amanuense, només el caixó d'escriure, **sense veu** (P-95). Lloc: els xats de l'àrea del soci (10).
- **Peça:** `static/css/teletipo.css` (`teletipo-fila` amb `teletipo-compte`, `teletipo-tira` amb `es-nou`, que porta el punt i el text «Nou:» per al lector, i `es-meu`, a la dreta amb la vora marina; cada tira entra **una sola vegada**, D20) i `static/css/amanuense.css` (`amanuense`: el camp de text amb «Envia»).
- **Pantalla:** `/en-construccio/xats/`, «Xats», a l'àrea del soci, amb tres converses (dues d'activitat i una general) i quatre missatges d'exemple, amb rols i no noms. Tot dins de `fieldset disabled`. Prova pròpia: `apps/previews/tests/test_xats.py` (cap micròfon ni dictat).
- **Quan funcioni:** una conversa d'activitat només la veuen els inscrits i qui la gestiona; un missatge no s'obre fora de la conversa; text escapat pel servidor, sense HTML ni rastrejadors; els llegits es desen al servidor, no al navegador.
- **Del recurs no s'hi fa:** el lector de canals RSS/Atom i OPML (Teletipo), el dictat per veu, el text provisional, la puntuació dictada ni «Desfer dictat» (Amanuense: el reconeixement de veu del navegador no es fa servir mai; el dictat, si arriba, amb un reconeixement instal·lat al servidor de la UE, `risc:alt`).
### T-DX-34 Emisor: factures
Del recurs Emisor ([pla dels recursos externs](plans/recursos-disseny-extern.md)): triar rebut o factura, el formulari de la factura (identificador fiscal, raó social, adreça), les empreses desades i la fulla que s'omple al costat. Lloc: facturació del 09 (P-93, resposta C; el segell ja és al rebut, §6.14).
- **Peça:** `static/css/emisor.css`. A dalt, `avis avis-avis` «La facturació està desactivada» (RN-M09-19). El formulari amb el `segmentat` «Rebut / Factura» i `camp`; al costat a l'escriptori i a sota al mòbil, la fulla `emisor-full`: paper clar als dos temes (`--paper` i `--abisme`, com el rebut), amb `dades-soci` (número, emissor, destinatari, NIF, concepte, departament i import) i sense segell, perquè la factura encara no existeix. Les dades fiscals del club van marcades `a-validar`.
- **Pantalla:** `/en-construccio/factures/`, «Factures», a l'administració, amb un càrrec i una empresa d'exemple; el NIF es deixa buit perquè cap número inventat sembli real.
- **Quan funcioni:** només tresoreria (MG9). La plataforma no numera: demana la factura a un servei homologat per Verifactu darrere d'un adaptador i en desa el número, el PDF i el QR (RN-M09-17). El NIF, el NIE o el CIF es validen amb la lletra de control al servidor (`core.normalize_document`). Cap IBAN. Les empreses es desen al servidor, amb permís, mai al navegador. Cap factura emesa s'edita ni s'esborra; una devolució porta la seva rectificativa (RN-M09-18, 058). Mentre la facturació estigui desactivada (P-02, P-47), el justificant és el rebut.
- **Del recurs no s'hi fa:** el RUT xilè amb el mòdul 11 (aquí, NIF, NIE o CIF), desar les empreses al `localStorage` ni el número de document que posa el navegador.
### T-DX-31 Averia i Pregon: publicar una activitat
Dels recursos Averia i Pregon ([pla dels recursos externs](plans/recursos-disseny-extern.md)): Averia posa el formulari amb les preguntes segons el tipus i la foto; Pregon, la vista prèvia de com es veurà l'activitat en compartir-la. Lloc: publicar sortides i activitats, a l'administració (§4 i §6.4 del pla).
- **Peces:** `static/css/averia-publicar.css`: `averia-form` (tipus d'activitat amb el control segmentat, títol amb el comptador de caràcters, descripció, `averia-preguntes`, les preguntes del tipus triat agrupades amb una vora a l'esquerra, i la imatge) i `averia-accions` («Desa l'esborrany» i «Publica»). `static/css/pregon-publicar.css`: `pregon-targeta` (xat, xarxa social i correu, cadascuna amb el títol i la descripció retallats a la seva mida i `caixa-imatge` mentre no n'hi ha) i `pregon-comprovacions` (estats amb ✓ o !). Dues columnes a partir de 1024 px. Pantalla ampla.
- **Pantalla:** `/en-construccio/publicar-activitat/`, «Publicar una activitat», a l'administració: la Sortida a les Medes d'exemple, sense imatge.
- **Quan funcioni:** publicar demana el permís d'activitats (02) i queda al registre d'activitat. Les preguntes de cada tipus seran dades. La imatge es valida pel contingut (`core.validate_upload`) i se'n treu l'EXIF també al servidor, encara que el navegador la redueixi; sense persones identificables sense consentiment (P-41). Les etiquetes `meta` i l'enllaç es generen al servidor, amb el domini de la plataforma. Cap dada personal a les targetes.
- **Del recurs no s'hi fa:** el text que es reescriu lletra a lletra, l'anell de caràcters, el punt focal que s'arrossega ni «Copiar etiquetes» (Pregon); els equips, les franges i el folio d'Averia, que són de les avaries del material (T-DX-32).
### T-DX-38 Convite: capçalera de la fitxa d'una activitat
Del recurs Convite ([pla dels recursos externs](plans/recursos-disseny-extern.md); [P-99](decisions/pendents.md), resposta A): la targeta d'un esdeveniment, que aquí és la capçalera de la fitxa d'una activitat (i, més endavant, de les conferències de l'11). Sense fotos ni mapa.
- **Peça:** `static/css/convite.css`. `convite-full` (la data com un full de calendari, `aria-hidden` perquè la data ja hi és en text; **entra una sola vegada** amb la molla, B5), `convite-dades` (dia i hora, lloc i preu, en una llista de definicions), `convite-places` (el text «Queden N places de M» i una casella per plaça, plena si està ocupada, `aria-hidden`) i `convite-accions` («M'hi apunto» com a botó principal, «Afegeix al calendari» i el recordatori).
- **Pantalla (retirada, T-DX-95: la real és `activities:public_detail`; la peça es queda):** `/en-construccio/fitxa-activitat/`, «Fitxa d'una activitat», a l'àrea del soci: la Sortida a les Medes d'exemple amb 6 places de 12.
- **Quan funcioni:** les places que queden surten del servidor i mai no diuen qui hi va. «M'hi apunto» obre el flux d'inscripció (Camilla, T-DX-24) i no apunta ningú pel navegador. L'`.ics` es genera al servidor i no porta dades de cap persona; l'enllaç que es copia és el de la plataforma. Totes les hores són locals. El recordatori per defecte serà un ajust.
- **Del recurs no s'hi fa:** «La meva hora», la foto d'arxiu, el full que vola en arc fins a la icona, el comptador que roda ni la campana que es balanceja; les fotos del lloc són de Fototeca i Expositor (T-DX-37) i el mapa 3D, de més endavant (12).
### T-DX-41 Antefirma: signatures de correu
Del recurs Antefirma ([pla dels recursos externs](plans/recursos-disseny-extern.md)): les dades de la signatura, les plantilles, el color, la vista prèvia en un full de correu i els botons de copiar. Lloc: eina de signatures de correu de l'administració, fora de mòdul (P-92, resposta A).
- **Peça:** `static/css/antefirma.css`. `antefirma-dades` (càrrec, àrea, correu del club, telèfon opcional; plantilla amb `segmentat` i color entre tokens, triat amb anella i negreta), `antefirma-full` (el full de correu amb la `antefirma-signatura`, que entra **una sola vegada**, D20) i `antefirma-segell`.
- **Pantalla:** `/en-construccio/signatures/`, «Signatures de correu», a l'administració, amb la signatura d'exemple d'un càrrec (cap nom). Les dades, «Copiar amb format», «Copiar el text pla» i «Veure el codi» van dins d'un `fieldset disabled`.
- **Quan funcioni:** només dades de càrrec i de contacte del club (cris@cris.es), mai el telèfon personal si la persona no ho vol; plantilles i colors com a dades (tokens); res no es desa ni s'envia: la signatura s'arma i es copia. Només el text copiat porta estils en línia, perquè és per als clients de correu i no es pinta a cap pantalla nostra.
- **Del recurs no s'hi fa:** la línia nova que es ressalta en escriure, la validació en directe del correu i del telèfon ni la còpia al porta-retalls (cal JavaScript; per a quan funcioni).
### T-DX-22 Deposito: transferències i pagaments a revisar
Del recurs Deposito ([pla dels recursos externs](plans/recursos-disseny-extern.md)): el panell del negoci que confirma o rebutja amb motiu el que arriba per revisar. Reutilitza el panell de revisió de §6.17. Lloc: tresoreria, transferències per revisar (T-M04-12) i pagaments a revisar (T-M05b-16).
- **Peça:** `static/css/deposito-revisar.css`, només el bloc de la pantalla i el de cada element; els comptadors (`deposito-comptadors`, «per revisar» en ambre) i la fila d'accions (`deposito-accions`, aquí un `fieldset disabled`) són els de `deposito.css`. Cada element és una `targeta` amb l'import i la data o el mètode, l'`estat` («✓ Proposada» o «! A revisar») i `dades-soci`. Transferències: «Confirma la conciliació» i «Exclou…» amb el motiu que s'obre a sota; si l'import no coincideix, un `avis avis-avis` «No es pot confirmar» al lloc del botó. Pagaments: el motiu (per exemple, un pagament duplicat) i «Fes la devolució…».
- **Pantalla:** `/en-construccio/revisar-pagaments/`, «Transferències i pagaments a revisar», a l'administració, amb dues transferències i un pagament inventats.
- **Quan funcioni:** només el tresorer (T4 i T10 de la 04; B6 del 05b). La plataforma proposa i mai concilia sola (RN-T16); una transferència només paga un càrrec si coincideixen la referència i l'import (RN-T18), i un pagament de menys queda «a revisar» (RN-T17b). Excloure una línia demana motiu i queda al registre (RN-T15). Un pagament duplicat es retorna (RN-M05b-08). **Cap IBAN**, ni el de qui ordena ni emmascarat; de l'extracte només surten l'import, la data i la referència.
- **Del recurs no s'hi fa:** la part del soci (copiar les dades del compte i pujar el comprovant, T-DX-12) ni els motius de rebuig predefinits (cap llista al pla, §6.17).
### T-DX-42 Apoderado: avisos i textos legals
Del recurs Apoderado ([pla dels recursos externs](plans/recursos-disseny-extern.md)): l'avís que passa a llegit en obrir-lo, el que demana confirmar la lectura amb un toc i queda confirmat amb el dia i l'hora, i l'acceptació que no es fa dues vegades. Lloc: l'àrea del soci (01), per confirmar la lectura dels avisos de la junta i acceptar els textos legals (P-91, resposta A); les autoritzacions d'activitat són de la 02.
- **Peça:** `static/css/apoderado.css`. `apoderado-avis` (un `details` per avís, amb `es-confirmar`, `es-confirmat` o `es-llegit`; l'estat és una `estat` amb text: «Cal confirmar», «✓ Confirmat», «Llegit») i `apoderado-legal` (la versió acceptada amb la data o, amb `es-nou`, la casella «He llegit i accepto» i «Acceptar»).
- **Pantalla:** `/en-construccio/avisos-junta/`, «Avisos i textos legals», a l'àrea del soci, amb tres avisos i dos textos legals d'exemple. Tot dins de `fieldset disabled`.
- **Quan funcioni:** cada confirmació i cada acceptació guarda la versió del text, el canal i l'hora (T-M01-08) i només s'hi afegeixen files; una acceptació no es pot fer dues vegades; cap dada de salut.
- **Del recurs no s'hi fa:** la signatura amb el dit, el calendari de proves ni l'assistència amb percentatge (no són d'aquest lloc; les autoritzacions, a la 02), ni la barra de pestanyes de telèfon.
### T-DX-40 Seguir i Monograma: social
Del recurs Seguir ([pla dels recursos externs](plans/recursos-disseny-extern.md)): el botó «Seguir» que passa a «✓ Seguint», el comptador de seguidors i l'anell de l'avatar. De Monograma, els avatars: la peça de la T-DX-18 (`{% monograma llavor %}`, §6.19), dibuixada a partir d'una llavor, mai del nom. Lloc: la part social i els avatars de l'àrea del soci (12).
- **Peça:** `static/css/seguir.css`. `seguir-perfil` (l'avatar, «Privat» i la casella per obrir el perfil), `seguir-variant` (les variants de l'avatar; la triada amb anella de dues capes), `seguir-fila` amb `seguir-anell` (`es-seguit`: l'anell marí) i `seguir-boto` amb `aria-pressed` i el ✓ en text.
- **Pantalla:** `/en-construccio/social/`, «Social», a l'àrea del soci, amb llavors d'exemple per als avatars i tres socis d'exemple (només un nom inventat i el recompte de seguidors). Tot dins de `fieldset disabled`.
- **Quan funcioni:** seguir és opcional i els perfils són privats per defecte; el comptador el dona el servidor; l'avatar surt de `Member.avatar_seed` (RN-M01-30), mai del nom; els avatars de fauna marina, amb la bitàcola (12).
- **Del recurs no s'hi fa:** la goma del botó, el comptador que roda, el batec de l'avatar ni les partícules (cal JavaScript i són moviment de més, D20); de Monograma, l'avatar a partir del nom, «Copiar SVG» ni «Descarregar».

### T-DX-12 Deposito: pagar per transferència i el comprovant
Del recurs Deposito ([pla dels recursos externs](plans/recursos-disseny-extern.md)): copiar les dades del compte, un camp o tots, i pujar el comprovant i seguir-ne l'estat.
- **Funcional, a la pantalla de pagament (`templates/payments/_status.html`):** a més dels «Copia» de cada dada (T-M05b-06), «Copia-ho tot» copia l'IBAN del club, l'import i la referència, una per línia, amb el mateix `copia.js`. Surt amagat sense porta-retalls, com els altres.
- **En construcció, `/en-construccio/comprovant-transferencia/`:** el comprovant (imatge o PDF), els passos amb Tramite (enviat, en revisió, confirmat o rebutjat amb el motiu) i l'estat. És una proposta: el pla no té comprovant (D1).
- **Quan funcioni:** el comprovant serà un fitxer privat (`core.validate_upload`), només el veuran la persona i la tresoreria, i confirmar o rebutjar serà una acció amb permís, motiu i registre. El pagament es continua confirmant només amb l'extracte del banc (B10).
- **Del recurs no s'hi fa:** el panell del negoci per revisar comprovants (és la T-DX-22, en construcció).

### T-DX-63 Activitats: la pàgina del soci i el bloc «Activitats per a tu»
Programa de l'escriptori aprovat pel propietari el 18/11/2026 (apartat 3.7), PR 8 de 9. És una pantalla proposada: el pla no la té (D1, [P-312](decisions/pendents.md)). Depèn del 02 (cursos i sortides), de l'11 (conferències d'Història) i de S-M02-11 (la llista de nivells).
- **Peça:** `static/css/activitats.css`, `static/js/activitats.js` (propi, `defer`, sense xarxa ni `eval`), `templates/previews/_activitats_targeta.html`, `_activitats_buit.html` i `_activitats_per_a_tu.html`.
  - **Capçalera** (`capcalera-pagina`): l'etiqueta «Activitats», un títol concret amb el recompte («12 activitats properes, 8 per a tu», D17) i «Llista» o «Calendari» (`activitats-vista`: dos enllaços amb l'aspecte del `segmentat`; el de la pàgina actual porta `aria-current`, ✓ i relleu). «Calendari» és Horario (T-DX-23).
  - **Pestanyes per tipus** (`pestanyes desplacable-x activitats-pestanyes`), amb el patró ARIA de §6 (fletxes, Inici i Fi, amb la volta; activació en enfocar) i un comptador `activitats-n` que segueix els filtres: Totes, Sortides, Cursos i especialitats, Conferències d'Història, Medi ambient i Guardades. Sense el subratllat elàstic: la triada porta negreta i una ratlla `--v-activa` de `--c-zona`. Al mòbil, es desplacen de costat amb la vora esvaïda (C2). A «Totes», una secció per tipus (`activitats-grup`: icona, nom, recompte, les 3 més properes i «Veure-les totes ›», que obre la pestanya); dins d'un tipus i a «Guardades», agrupades per mes.
  - **Filtres** (`activitats-filtres`): «Només les que puc fer» (`interruptor`, amb el recordatori «Titulació B1 · llicència vigent», RN-M02-10 i RN-M02-27), «Quan» (`segmentat`: aquest mes, 3 mesos, tot), «On» (llocs d'exemple) i «Només amb places lliures» (`interruptor`). Escriptori: columna fixa de `--lateral-ample` a l'esquerra (`amb-columna-lateral lateral-esquerra`, §5.3). Tauleta o columna estreta: en una fila a dalt. Mòbil (< 600 px): darrere del botó «Filtres» (`aria-expanded`), a pantalla sencera (`100dvh`) amb «Fet»; mentre és obert, la resta de la pàgina és `inert`, i Esc o «Fet» el tanquen i tornen el focus al botó. «N de 12 activitats» s'anuncia (`aria-live`).
  - **Sense resultats** (`activitats-buit`): «Cap activitat amb aquests filtres» i un botó per cada filtre actiu («Treu el filtre Quan: Aquest mes»), que el treu.
  - **Targeta** (`activitats-targeta`, sobre `targeta`): el full de calendari de Convite sense l'entrada animada (`activitats-full`, `aria-hidden`: la data ja hi és en text), el tipus amb icona i nom, l'estrella de Marcador (`activitats-estrella`, `aria-pressed`, «Guarda «[nom]»»; plena si està guardada), el títol, quan, el lloc, el nivell («✓ Nivell B1: el tens», «◷ Et falta B2 · el curs que hi porta» o «Oberta a tothom» per a les conferències; amb les icones `check` i `clock`) i les places («Queden 4 places» o «Llista d'espera»). Graella d'1, 2 o 3 columnes segons l'amplada de la columna (contenidor `activitats`, a 34rem i 50rem; C8).
  - **«Activitats per a tu»** (`_activitats_per_a_tu.html`, per a la portada, que l'inclourà més endavant): les 3 més properes que el soci pot fer, amb les mateixes targetes, i «Totes les activitats (12) ›». Al mòbil, el carril de Desfile (`desfile-pista activitats-carril`) amb el comptador «1 / 3», que segueix la posició real; **sense avanç automàtic** (D20). A l'escriptori hi caben les tres i no hi ha vora esvaïda.
- **Colors dels tipus** (`tokens.css`, clar i fosc): `--c-tipus-sortida`, `--c-tipus-curs`, `--c-tipus-conferencia` i `--c-tipus-medi`, per al nom i la icona del tipus i la franja del mes del full (amb `--c-fons` al damunt). Fan ≥ 4,7:1 sobre el fons, el contenidor i el pou als dos temes (prova `test_tokens_color.py`; axe sense violacions). Sempre amb icona i nom, mai només color.
- **Pantalles (retirades, T-DX-95: les reals són `activities:mine` i `activities:public_list`; la peça es queda per reaprofitar-la):** `/en-construccio/activitats/`, «Activitats», a l'àrea del soci (12 activitats d'exemple inventades, a la costa i a Barcelona; el soci d'exemple té B1 i la llicència vigent), i `/en-construccio/activitats-per-a-tu/`, el bloc sol.
- **Al servidor (control, no simulació):** com tota pantalla en construcció (§6.9), només `GET`, contingut fix i cap model. Les pestanyes i els filtres treballen al navegador sobre el contingut d'exemple i no envien res; l'estrella és desactivada (`disabled`) perquè guardar es desarà al servidor.
- **Quan funcioni:** «per a tu» i «Només les que puc fer» els calcularà el servidor amb les titulacions i la llicència del soci de la sessió (RN-M02-10, RN-M02-27), mai el navegador. De les places només es dirà el nombre, mai qui hi va. Guardar es desarà al servidor (Marcador, T-DX-25). Els llocs de «On» i els tipus seran una llista editable des de l'app (dades, no codi), i els nivells, els de S-M02-11. Les conferències obertes també podran sortir a la web pública (07). Els filtres podran anar a l'adreça (`?quan=…`) perquè es puguin compartir, sense cap dada personal.
- **Del programa no s'hi fa:** la portada no s'edita (inclourà el bloc més endavant) i la navegació del soci ja enllaça la pantalla des de la seva PR.
