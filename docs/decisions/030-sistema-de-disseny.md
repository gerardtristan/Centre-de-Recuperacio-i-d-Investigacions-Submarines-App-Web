# 030 — Sistema de disseny

- **Data:** 27/10/2026
- **Estat:** Acceptada (paleta, tipografia, punts de canvi i regles d'ús; [A validar] pel club: regla de les fletxes, versions del logotip, allotjament de les fonts i pila del frontend). Substitueix la [009](009-sistema-de-disseny.md). Ampliada per la [031](031-estil-neumorfic-limitat.md) (estil neumòrfic limitat). Ampliada per la [032](032-immersio-socis-i-centre.md).

## Context
La 009 deixava el sistema de disseny pendent perquè no hi havia cap document d'origen (P-10). A l'etapa 3, l'equip ha fixat la paleta (clar i fosc) i la tipografia, i ha demanat wireframes de baixa fidelitat de les tres zones (pública, compte personal i administració) per fixar-ne l'estructura abans d'especificar les pantalles. El club ha afegit el logotip per a fons fosc a `assets/marca/`.

## Alternatives
1. **CSS amb tokens (variables CSS) en dos temes, sense framework.** És el que demana l'encàrrec per als wireframes i serveix per a qualsevol pila del frontend.
2. **Partir d'una plantilla de React i Tailwind** (les referències de 21st.dev). Lligaria la pila del frontend abans de decidir-la, i dues de les referències tenen restriccions de llicència (CC BY-NC 4.0; TailGrids no es pot redistribuir).

## Decisió
- Sistema de disseny a `docs/design-system.md`. Els valors són a `design/wireframes/tokens.css`, que n'és la font de veritat mentre no hi hagi frontend.
- Dos temes, clar i fosc, amb els mateixos tokens. Per defecte segueixen la preferència del sistema; el botó té tres estats (Sistema, Clar, Fosc) i desa la tria a `localStorage`. La barra lateral és fosca als dos temes.
- Colors per zona: pública, soci i admin. El groc es reserva per a l'acció principal i l'element actiu, que també porta barra i negreta. Els estats es mostren sempre amb símbol, text i color.
- Regla de les fletxes al tema clar: el primer valor és decoratiu (3:1) i el segon és per a text (4,5:1). El contrast està comprovat (`design-system.md` §2.4).
- Tipografia: Barlow Condensed (títols), Source Sans 3 (text) i JetBrains Mono (codis i imports).
- Punts de canvi: mòbil fins a 599 px, tauleta de 600 a 1023 px i escriptori a partir de 1024 px.
- Logotips: `CRIS_SenseFons.png` al tema clar, i `CRIS_Blanc_per fons Negre (Blanc).png` al tema fosc i a la barra lateral, sense disc clar.
- Menús i blocs de l'administració filtrats segons la matriu provisional de la spec 00 (P-04).
- Les referències de 21st.dev només s'han consultat per veure'n l'estructura i l'estil, sense copiar-ne codi. La pila del frontend no es decideix aquí.

## Conseqüències
- Les specs de la web pública (07) i de l'àrea de socis (01) poden fer referència als ids de blocs i als components de `design-system.md`.
- En producció, les fonts s'han d'allotjar a `assets/fonts/` amb la llicència documentada [A validar].
- Del logotip, falten una versió reduïda per a la capçalera del mòbil i la icona de la PWA, una versió SVG i un nom de fitxer sense espais [A validar].
- Si es tria React i Tailwind, els tokens es traslladen a la configuració del tema sense canviar-ne els valors.
- Abans del disseny final cal una revisió WCAG 2.2 AA amb eina (checklist B8).
- L'editor és l'etapa 4.

## Fonts
- Encàrrec de l'etapa 3 i confirmació de l'equip (27/10/2026)
- `design/mapa-plataforma.html` (tema fosc de referència)
- `specs/00-base-comuna/spec.md`, §2 (rols i permisos)
- `assets/marca/`
- [pendents.md](pendents.md), P-04 i P-10
