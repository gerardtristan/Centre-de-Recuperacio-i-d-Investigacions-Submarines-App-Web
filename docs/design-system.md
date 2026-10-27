# Sistema de disseny — Plataforma C.R.I.S.

- **Versió:** 1.1 (27/10/2026), etapa 3: sistema de disseny i wireframes de baixa fidelitat. La 1.1 afegeix l'estil neumòrfic limitat (§6.4) i el selector de tema segmentat (§7).
- **Decisions:** [030](decisions/030-sistema-de-disseny.md) (substitueix la 009), ampliada per la [031](decisions/031-estil-neumorfic-limitat.md).
- **Fitxers:** `design/wireframes/tokens.css` (font de veritat dels valors), `publica.html`, `socis.html` i `admin.html`.
- **Abast:** estructura i regles. **No és el disseny final.** No hi ha l'editor (etapa 4) ni cap polit visual o animació.

## 1. Principis
1. Tres zones amb la mateixa identitat i estructura diferent: **pública** (escriptori primer), **compte personal** (mòbil primer) i **administració** (escriptori primer, densa).
2. Es veu de seguida en quina zona ets: el color de la zona marca la capçalera, l'etiqueta de secció i els detalls.
3. Cap valor de disseny directe als components: tot surt de variables CSS (tokens) i té valor als dos temes.
4. Els estats es llegeixen sense color: sempre hi ha **símbol + text + color**.
5. Mòbil, tauleta i escriptori són tres disposicions pensades per separat, no una sola que s'estira.

## 2. Tokens de color
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

## 4. Espaiat, formes i mides
- **Espaiat:** `--e-1` a `--e-8` = 4, 8, 12, 16, 24, 32, 48 i 64 px. No se'n fan servir d'altres.
- **Radis:** `--r-s` 4, `--r-m` 8, `--r-l` 12 i `--r-pastilla` (forma de pastilla).
- **Vores:** `--v-fina` 1 px; `--v-activa` 3 px (element actiu i vora de zona); `--v-focus` 3 px; `--v-plena` 2 px (peces neumòrfiques amb més contrast).
- **Avatar:** `--avatar` 56 px.
- **Tàctil:** `--tactil` 44 px. És l'alçada i l'amplada mínimes de tot element que es pot prémer, a totes les mides.
- **Estructura:** `--amplada-max` 1200 px, `--lateral-ample` 240 px (administració), `--lateral-soci` 200 px, `--lateral-carril` 72 px (tauleta), `--columna-dreta` 22rem, `--capcalera-alcada` i `--barra-inferior-alcada` 64 px.

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
| `capcalera` (sobre el fons de pàgina) | Logotip, selector de tema només amb icones i botó ☰ de menú (hamburguesa, s'obre amb un clic) | Dues files: logotip, selector amb text i «Fes-te soci»; a sota, la pastilla de navegació centrada, amb 3 enllaços i «Més» | Dues files: logotip, selector, «Àrea de socis» i «Fes-te soci»; a sota, la pastilla amb tots els enllaços |
| `portada` | Text i, a sota, la imatge | Igual | 2 columnes |
| `properes-activitats` | 1 columna de targetes | 2 columnes | 3 columnes |
| `qui-som`, `medi-ambient` | Text i, a sota, la imatge | Igual, xifres en 3 columnes | 2 columnes; la imatge canvia de costat |
| `fer-se-soci` | 1 targeta per fila | 2 targetes | 2 targetes en 2/3 de l'amplada |
| `contacte` | Dades i, a sota, el formulari | 2 columnes | 2 columnes |
| `peu` | 1 columna | 2 columnes | 4 columnes |

**Compte personal (`socis.html`)**
| Bloc | Mòbil | Tauleta | Escriptori |
|---|---|---|---|
| Navegació | Barra inferior fixa de 5 botons | Carril fosc de 72 px (icona i text curt) | Barra lateral fosca de 200 px amb etiquetes |
| `salutacio` (sobre el fons, amb avatar) | 1r bloc | Amplada sencera | 2 columnes |
| `carnet` (sobre el fons, amb relleu) | 2n bloc | Amplada sencera | Columna dreta, al costat de 2 files |
| `pagaments-pendents`, `proximes-activitats` | Una a sota de l'altra | 2 columnes | 2 columnes |
| `llicencia`, `avisos` | Una a sota de l'altra | 2 columnes | `llicencia` a l'esquerra i `avisos` a la columna dreta |

**Administració (`admin.html`, fitxa d'una sortida)**
| Bloc | Mòbil (llegible) | Tauleta (utilitzable) | Escriptori |
|---|---|---|---|
| `barra-lateral` | Amagada; «Menú» l'obre com a panell sencer | Carril fosc de 72 px | Barra fosca de 240 px |
| `capcalera-fitxa` | Dades en 2 columnes; accions dins de «Accions» | Accions visibles a la dreta | Dades en una fila |
| `resum-economic` | 2×2 | 2×2 | 4 xifres en una fila |
| `participants` | Cada fila és un bloc apilat amb etiquetes | Taula sense Mètode ni Llicència | Taula sencera (8 de 12 columnes) |
| `material-assignat`, `activitat-recent` | A sota | A sota | Columna dreta (4 de 12 columnes) |
| `programa-i-notes` | 1 columna | 2 columnes | 2 columnes, amplada sencera |

## 6. Components
Tots són a `tokens.css` (components compartits) o a l'estil de cada pàgina (estructura). Classes en català.

| Component | Classe | Regles |
|---|---|---|
| Botó | `boto`, `boto-principal`, `boto-text`, `boto-petit` | Mínim 44 × 44 px. Un sol `boto-principal` per vista o bloc. Els desactivats porten `aria-disabled` i vora discontínua |
| Selector de tema | `selector-tema` (+ `neu-selector` a la pública i als socis; + `selector-lateral` a la barra fosca de l'administració) | Control segmentat amb botons de ràdio; vegeu §7 |
| Avatar | `avatar` (+ `neu-anell`) | Inicials en Barlow Condensed 700 i `--c-text`; és decoratiu (`aria-hidden`), perquè el nom ja hi és en text |
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

### 6.1 Navegació
- Pública: barra superior en forma de pastilla. Al mòbil, una hamburguesa que s'obre i es tanca amb un clic o amb Esc.
- Compte personal: barra inferior al mòbil (Inici, Activitats, Carnet, Pagaments, Perfil) i barra lateral fosca a partir de la tauleta.
- Administració: barra lateral fosca amb els mòduls Socis, Activitats, Material, Tresoreria, Pagaments, Llicències, Web i Dashboard, **filtrada per rol** (§6.2).
- Element actiu: `aria-current="page"`, barra groga, negreta i fons (§2.5).

### 6.2 Menús i blocs per rol (matriu provisional, P-04)
Surt de la spec 00, §2.4 i §2.5. **No està validada per la junta**, i el wireframe ho diu amb l'avís «Matriu de permisos provisional (pendent de la junta)».

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
| Avatar | `socis.html` (`salutacio`) | Anell tou (relleu petit i ombra interior); inicials amb `--c-text` (15,7:1 i 15,8:1) |
| Carnet de soci | `socis.html` (`carnet`) | Relleu suau i vora superior del color de zona; el número de soci en JetBrains Mono 500 i `--c-text` |
| Pastilla de navegació | `publica.html`, de la tauleta en amunt | Contenidor en relleu petit; l'enllaç actiu porta **ombra interior + negreta + barra groga** i `aria-current`. Al mòbil, el menú desplegat és pla |

**On no:** `admin.html` (tot, inclòs el selector de tema, que hi és pla), taules, formularis i camps, avisos, estats, targetes generals, botons principals («Fes-te soci», «Paga ara», «Inscriu-t'hi»), barra lateral i barra inferior.

**Regles:**
- Les peces neumòrfiques només es posen sobre `--c-fons`. Per això, la capçalera de la pública i la del compte personal, `salutacio` i `carnet` van sobre el fons de pàgina i no dins de targetes blanques. Al tema clar, damunt de `#ffffff` no pot haver-hi cap ombra més clara que el fons, i l'efecte no funcionaria.
- Cada peça té vora `--neu-vora` (≥3:1), focus visible (`--c-focus`: 6,3:1 i 9,65:1) i text ≥4,5:1 (`--c-text-2` sobre la superfície: 5,4:1 i 7,6:1).
- **Cap estat s'indica només amb l'ombra:** l'element actiu sempre porta també negreta i una marca (✓ o la barra) i el seu estat a l'HTML (`checked` o `aria-current`). Les ombres tenen un contrast baix a propòsit (1,5:1 i 1,3:1) i són decoratives.
- **`prefers-contrast: more`** (l'usuari demana més contrast al sistema): les ombres desapareixen i passen a vora plena de 2 px en `--c-text`. L'opció activa del selector es mostra invertida (`--c-fons` sobre `--c-text`, 15,7:1) i l'enllaç actiu de la pastilla porta una barra en `--c-text`.
- En mode de colors forçats (alt contrast de Windows), el navegador treu les ombres i l'estat continua indicat per la ✓, la negreta i la barra.

## 7. Temes clar i fosc
- Per defecte, la pàgina segueix `prefers-color-scheme`, la preferència de color del sistema operatiu.
- El **selector de tema** és un control segmentat de tres opcions, **Sistema / Clar / Fosc** (◐ ○ ●), fet amb botons de ràdio dins d'un `fieldset` amb la llegenda «Tema». Funciona amb el teclat (Tab i fletxes) i cada opció fa 44 px com a mínim. Al mòbil només es veuen les icones, però el text continua disponible per al lector de pantalla. A partir de tauleta es veuen la icona i el text.
- Desa la tria a `localStorage` amb la clau `cris-tema` (`light` o `dark`); a «Sistema», la clau s'esborra. Si una pàgina té més d'un selector (l'administració en té un a la barra lateral del mòbil i un a la barra superior), tots dos queden sincronitzats.
- Un petit script al `<head>` aplica el tema desat abans de pintar la pàgina, perquè no es vegi el canvi. Si `localStorage` no està disponible, el selector funciona igual però no se'n recorda.
- El tema manual es fixa a `<html data-theme="light|dark">`. Els tokens foscos són dues vegades a `tokens.css`: una per a la preferència del sistema i una altra per al tema triat amb el selector.

## 8. Logotips
| On | Fitxer |
|---|---|
| Tema clar | `assets/marca/CRIS_SenseFons.png` (text i contorns negres, fons transparent) |
| Tema fosc | `assets/marca/CRIS_Blanc_per fons Negre (Blanc).png` (text i contorns blancs, fons transparent), directament sobre el fons fosc |
| Barra lateral (fosca als dos temes) | La versió per a fons fosc (`logo-sempre-fosc`) |
| Versió amb fons blanc | `assets/marca/CRIS_AmbFons.jpg` (no es fa servir als wireframes) |

Comprovat sobre `#08131e` i sobre `#062a47`: els contorns i el text blancs es llegeixen bé i «DES DE 1954» manté el contorn blanc. El canvi es fa amb les classes `logo-clar` i `logo-fosc`.

Falta [A validar]:
- **Versió reduïda per a la capçalera del mòbil i per a la icona de la PWA** (només les ampolles i «CRIS», sense el text circular). A 40-48 px, el text «Centre de Recuperació i d'Investigacions Submarines» no es llegeix en cap de les dues versions.
- **Versió vectorial (SVG)** de totes dues variants, per a una nitidesa perfecta i fitxers més petits. Els PNG actuals fan 2717 × 2900 px (de 350 a 510 kB), massa per a una capçalera.
- **Nom del fitxer** de la versió fosca: té espais i parèntesis. Als wireframes s'enllaça codificat (`%20`). Recomanació: reanomenar-lo (per exemple, `CRIS_SenseFons_Blanc.png`) quan el club ho aprovi.

## 9. Accessibilitat (mínims dels wireframes)
- Focus visible a tot arreu: contorn de 3 px de `--c-focus`, groc a la barra lateral.
- Objectius tàctils de 44 px com a mínim. Cap acció depèn de passar el ratolí per sobre: els menús i els desplegables s'obren amb un clic o amb el teclat.
- Estats mai només amb color (§6.3); els símbols porten `aria-hidden` i el text és el que es llegeix.
- Enllaç «Salta al contingut», `lang="ca"`, etiquetes visibles als camps, `caption` a la taula i `aria-live` al recompte de resultats i a la descripció del rol.
- `prefers-reduced-motion`: no hi ha animacions, i si n'hi ha mai, s'anul·len.
- `prefers-contrast: more`: les peces neumòrfiques passen a vores plenes (§6.4).
- Pendent: revisió WCAG 2.2 AA amb eina i lector de pantalla (checklist B8), quan es faci el disseny final.

## 10. Referències (només estructura, components i estil)
No se n'ha copiat codi, imatges, logotips ni textos. Tampoc no s'ha fet servir l'MCP de 21st.

| Referència | Zona | Què se n'ha agafat | Llicència |
|---|---|---|---|
| [Card Stack Portfolio](https://21st.dev/@kedhareswer/templates/card-stack-portfolio-website-template) (Kedhareswer Naidu) | Socis | Pila de targetes que es despleguen; navegació persistent (aquí, la barra inferior) | No indica cap llicència [A validar si se'n volgués reutilitzar codi] |
| [Saasly](https://21st.dev/@tailgrids/templates/tailgrids-saasly) (TailGrids) | Admin i pública | Xifres en targetes, jerarquia neta, targetes de preu per a `fer-se-soci`. Nota: és una pàgina de presentació, no un panell, i la barra lateral i la taula són disseny propi | Llicència TailGrids: ús comercial i en projectes de clients permès; **no** es pot revendre, redistribuir ni fer servir en generadors d'interfícies [A validar si se'n reutilitzés codi] |
| [Magic Portfolio](https://21st.dev/@larsen66/templates/magic-portfolio-for-next-js) (Once UI) | Admin i pública | Barra de navegació en forma de pastilla, botó de tema a la capçalera, etiquetes de secció i xips | **CC BY-NC 4.0**: cal citar l'autor i no se'n permet l'ús comercial. No en copiem codi; si mai se'n volgués reutilitzar, cal validar si l'ús del club és «no comercial» [A validar] |

## 11. Convencions de noms
- Tokens: `--c-` color, `--e-` espai, `--t-` mida de text, `--p-` pes, `--a-` alçada de línia, `--r-` radi, `--v-` vora, `--f-` família.
- Classes, tokens i ids en **català sense accents** (`capcalera`, `boto-principal`, `pagaments-pendents`). Els ids dels blocs són estables i coincideixen amb els de l'encàrrec. [A validar] Cal confirmar que el codi del frontend seguirà la mateixa convenció (CLAUDE.md: «decidir-ho una vegada i no barrejar»).

## 12. Pila del frontend: idees que només es podrien fer amb React i Tailwind [A validar]
No s'han implementat i no es decideixen aquí:
- El retrat que segueix el punter i les targetes animades de Card Stack: requereixen animació, i aquesta etapa no en vol.
- La instal·lació de components amb el CLI de shadcn o de 21st (React i Tailwind).
- Una llibreria de components reutilitzables com a font del sistema de disseny, en lloc d'aquest CSS amb tokens.

Si s'adopta React i Tailwind, els tokens d'aquest document es poden traslladar a la configuració del tema de Tailwind sense canviar-ne els valors.

## 13. Com provar els wireframes
1. Obrir `design/wireframes/publica.html`, `socis.html` o `admin.html` directament al navegador (no cal servidor).
2. **Tema:** triar Sistema, Clar o Fosc al selector de la capçalera (a `admin.html` al mòbil, dins de «Menú»). La tria es manté en recarregar i en canviar de pàgina. **Més contrast:** a les eines de desenvolupament, *Rendering → Emulate CSS media feature prefers-contrast: more*. Per provar el mode «Sistema», cal canviar el tema del sistema operatiu o, a les eines de desenvolupament, *Rendering → Emulate CSS media feature prefers-color-scheme*.
3. **Mides:** a les eines de desenvolupament (F12), activar el mode de dispositiu (Ctrl+Maj+M) i provar 390 px (mòbil), 820 px (tauleta) i 1440 px (escriptori).
4. **Demostració:** a `socis.html`, triar «Persona no sòcia amb compte»; a `admin.html`, canviar «Veure com» per veure els menús i blocs de cada rol.

## 14. Pendents [A validar]
- Que el club validi la paleta, la regla de les fletxes i els ajustos de §2.3.
- Matriu de permisos dels menús i blocs (P-04).
- Quotes d'exemple (35 € simpatitzant i 90 € ple dret, del context v4), què inclou cada quota, adreça i horari del local, i tipus de llicència.
- Si el carnet té codi QR i foto.
- El nom del departament de les sortides.
- Versions del logotip (reduïda i SVG) i nom del fitxer de la versió fosca (§8).
- Allotjament i llicència de les fonts (§3).
- Pila del frontend (§12) i convenció de noms del codi (§11).
