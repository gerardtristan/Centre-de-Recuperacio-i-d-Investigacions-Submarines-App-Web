# T-DX-60 · Escriptori, PR 4: inici del soci

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 18/11/2026 15:04 | 0e60ae1b | 4 unitàries noves i 2 e2e noves; 16 e2e (amb axe) i 4.684 unitàries del 00 i el 01 | [A comprovar] |

**En tres línies:** és la quarta de les nou PR del programa de l'escriptori que el propietari va aprovar el 18/11/2026 (secció 3.6). L'inici del soci aprofita l'amplada: la portada en dues columnes amb la quota i el carnet en petit, la franja de pendents només si n'hi ha, i a sota els pagaments recents, la història al C.R.I.S. i la llicència. Al mòbil, el mateix ordre, l'un a sota de l'altre.

## Què s'ha fet
- `templates/core/home.html`, de dalt a baix:
  - portada (Oleaje) amb `oleaje-graella`: 7/5 a l'escriptori, dues columnes iguals a la tauleta, una a sota de l'altra al mòbil. A l'esquerra, Monograma, salutació i «La teva quota»; a la dreta, el carnet en petit (número, tipus, estat i «vàlid fins al», sense QR);
  - «La teva quota»: «✓ Al dia» i «Es renova el dd/mm/aaaa» amb el mètode de «Com pago la quota». El compte enrere només des del primer dia d'avís. Si no està al dia, l'estat de sempre. «El meu carnet» és l'únic botó principal;
  - franja de pendents (`avis avis-avis franja-estat`), amb «Paga ara» de 56 px;
  - el lloc d'«Activitats per a tu» (PR 5), només com a comentari;
  - `inici-graella`, 8/4: «Pagaments recents» (3 quotes pagades i «Totes les quotes»); «La teva història al C.R.I.S.» (anys o «des de ~AAAA», insígnia de soci clàssic i una línia sobre la Bitàcola) i «Llicència» amb Vigencia.
- `apps/members/templatetags/member_notices.py`: `member_home` substitueix `member_home_summary` i torna les dades amb els serveis que ja existien (`roster.fee_state`, `preferences.fee_payment_method`, `cards`, `services.licence_record` i les files de «Les meves quotes»). `templates/members/_home_resum.html` s'esborra.
- `apps/members/templatetags/vigencia.py`: `in_fee_warning_window`, amb els dies d'avís de VC-02.
- `static/css/oleaje.css`: les dues graelles, la quota i el carnet sobre la superfície, i la franja.
- Sistema de disseny 1.29: §5.1, §6.5 i §6.18. Mapa e2e del hook. Fila a [`estat/DX.md`](../estat/DX.md).

## Decisions i perquè
- **La quota i el carnet sobre la superfície, no sobre el degradat:** Vigencia en avís i els estats perdien contrast sobre el blau fosc. El degradat és decoració; el que és important va pla (§6.5).
- **Llindars propis (34rem i 56rem) en lloc dels de `graella-2` (45rem i 60rem):** a la tauleta el cos fa 42rem i no arribava mai a dues columnes, i a 1024 px amb barra de desplaçament fa una mica menys de 60rem.
- **«Paga ara» amb `boto-mari`, no `boto-principal`:** un sol botó principal per pantalla (D19), i el propietari va triar «El meu carnet».
- **Sense `oleaje-seccio` a l'inici:** la pujada en desplaçar era una animació d'entrada (D20, B10). La peça continua a la portada pública de prova.
- **«Des de AAAA» en lloc de «0 anys»** per a un soci de menys d'un any.
- **Els pagaments recents són quotes pagades:** és el que el soci ja veu a «Les meves quotes». No hi ha cap altre càrrec propi encara.

## Problemes trobats
- **Fills del cos:** la regla de `comptes.css` per als fills directes del cos (gap de `--e-4`) és més específica que `.inici-graella`. **Arreglo:** el selector de 8/4 és `.cos-compte > div.inici-graella`.
- **Captures a pantalla sencera al mòbil:** Ramillete, fix a baix, surt al mig de la captura. És la captura, no la pàgina.

## Com se sap que funciona
- Unitàries:
  - `test_oleaje.py` (8): al dia sense compte enrere lluny de la renovació; compte enrere dins de la primera finestra (VC-02 canviat); pendent amb la franja i l'enllaç al càrrec; pagaments, anys i insígnia (VC-04); sense insígnia per sota del llindar o amb data aproximada; només el soci de la sessió; res per a un no soci ni per al compte d'administrador.
  - `test_vigencia.py`: la finestra segueix el primer dia d'avís, i sense dies d'avís no n'hi ha.
  - 00 i 01: 4.684 passen. `test_mail_limit` va fallar una vegada en l'execució llarga i passa sol (no toca res d'aquesta tasca).
- e2e: Oleaje (al dia i pendent: franja amb `role="status"` i «Paga ara» de 56 px, un sol botó principal, cap animació a la quota), Vigencia, quotes 079, fumada, disposició (1280: 7/5 i 8/4; 800: dues columnes iguals separades 24 px; 390: una columna; 320: res de costat), Monograma i axe del 01: 16 passen.
- Captures mirades: 1280, 1024, 800, 390 i 320, en clar i en fosc, amb un soci al dia i un amb la quota pendent.
- Comprovació de §15.5:
  - **B:** cap moviment nou; s'ha tret l'animació d'entrada de la quota. Botons de 44 px o més.
  - **C:** container queries (C8). Les targetes de dins la portada fan servir `--r-xl` i no `--r-interior`: la portada només té radi a dalt i no són concèntriques.
  - **D:** un sol botó principal; títols concrets; xifres tabulars (`import`); monoespai només al número de soci; espai i no línies entre els blocs de baix (D15); axe sense infraccions als dos temes.
  - **Tokens:** cap color, espai ni radi fora de `tokens.css`; cap `style=`.

## Evidències
- Soci al dia a 1280 px: portada 7/5 i, a sota, 8/4: `captures/2026-11-18_1504_T-DX-60_inici-al-dia-1280.png`

  ![Inici del soci a l'escriptori: salutació i quota a l'esquerra, el carnet en petit a la dreta, i a sota els pagaments recents, la història i la llicència](captures/2026-11-18_1504_T-DX-60_inici-al-dia-1280.png)

  *18/11/2026 15:04 (Europa/Madrid) · local, prova e2e, dades inventades · commit 0e60ae1b*
- Soci amb la quota pendent a 800 px, en fosc: dues columnes iguals i la franja amb «Paga ara»: `captures/2026-11-18_1504_T-DX-60_inici-pendent-800-fosc.png`
- El mateix a 390 px, l'un a sota de l'altre: `captures/2026-11-18_1504_T-DX-60_inici-pendent-390.png`

  *18/11/2026 15:04 (Europa/Madrid) · local, prova e2e, dades inventades · commit 0e60ae1b*
