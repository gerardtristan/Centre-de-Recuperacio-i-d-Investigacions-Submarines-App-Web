# 032 — Immersió al compte personal, logotip més gran i secció del Centre

- **Data:** 27/10/2026
- **Estat:** Acceptada (bitàcola, contingut del darrere del carnet i textos de la secció [A validar]; el nom del club es va fixar el 27/10/2026: «Centre de Recuperacions i d'Investigacions Submarines»). Amplia la [030](030-sistema-de-disseny.md) i ajusta l'abast de la [031](031-estil-neumorfic-limitat.md) al compte personal.

## Context
L'equip vol refinar l'estructura de dues zones:
- **Compte personal:** ha de ser clarament diferent de l'administració i ha de tenir un caràcter propi, amb la metàfora d'una immersió.
- **Web pública:** ha de donar més pes al logotip i explicar què vol dir el nom del club (Centre de Recuperació i Investigacions Submarines).

L'administració no canvia.

## Alternatives
1. **Mantenir l'estructura de targetes de la 1.1.** És correcta, però s'assembla massa a un panell de gestió.
2. **Estructura d'immersió amb el «wow» limitat a peces no crítiques.** És l'opció triada.
3. **Una estructura vistosa a tota la pàgina, també a pagar i als avisos.** Es descarta perquè posa en risc el contrast i la claredat de les accions crítiques.

## Decisió
**Compte personal (`socis.html`):**
- Portada a pantalla gairebé completa, amb un degradat per profunditat, una ona, l'avatar, la salutació i un carnet gran que es gira.
- Sota la portada, una franja d'estat plana i gran («Tot al dia» o «N pagaments pendents» amb el botó «Paga ara»).
- Properes sortides en targetes grans dins d'un carril horitzontal amb scroll-snap.
- Bitàcola personal amb sortides, hores i insígnies per fites [A validar].
- Navegació: dock flotant al mòbil amb el carnet al centre. A l'escriptori, sense barra lateral, amb la capçalera superior i una graella bento asimètrica.
- Si la persona no és sòcia, una invitació a fer-se soci en lloc del carnet.
- Moviment només a tres llocs (entrada de la portada, gir del carnet i ona), amb tokens `--m-*`. L'ona s'atura sola abans de 5 s. Amb reduir moviment, tot el moviment queda aturat.
- Pagar i els avisos són sempre plans, grans i amb contrast ≥4,5:1.
- Amb més contrast, desapareixen els degradats, l'ona i les ombres.
- Tokens nous: `--c-ocea-1` a `--c-ocea-4`, `--c-ocea-text` i `--c-ocea-text-2` (un joc per tema); `--c-carnet-*` (iguals als dos temes); i les mides i el moviment de `design-system.md` §4.

**Ajust de la 031:** a la portada, l'avatar i el carnet van sobre un degradat i no sobre `--c-fons`. Per tant, ja no són neumòrfics. Als socis, l'únic element neumòrfic és el selector de tema. Els components `neu-anell` i `neu-relleu` continuen disponibles sobre `--c-fons`.

**Web pública (`publica.html`):**
- Logotip més gran: 52 px a la capçalera del mòbil, 72 px a partir de la tauleta i 120 px al peu.
- Nova secció `centre-recuperacio-investigacio`, entre `qui-som` i `medi-ambient`: introducció, tres àmbits (Recuperació, Investigació, Divulgació) i una crida a col·laborar. Tot el text és d'exemple [A validar].
- Navegació: «El Centre» entra a «Més» a la tauleta i a la pastilla a l'escriptori, que passa a tenir 7 enllaços i hi cap.

## Conseqüències
- `docs/design-system.md` §2.6, §4, §4.1, §5.1, §6.4, §6.5 i §8 recullen els canvis.
- L'id `pagaments-pendents` dels socis passa a `franja-estat`. El detall dels pagaments anirà a la pantalla de Pagaments.
- Cal validar amb el club:
  - ~~el nom oficial~~: fixat el 27/10/2026 («Centre de Recuperacions i d'Investigacions Submarines»);
  - els textos del Centre;
  - d'on surten les dades de la bitàcola, i si es volen insígnies;
  - què va al darrere del carnet.
- La bitàcola no pot contenir cap dada de salut (CLAUDE.md).

## Fonts
- Encàrrec de l'equip (27/10/2026)
- [030](030-sistema-de-disseny.md), [031](031-estil-neumorfic-limitat.md); `docs/design-system.md`
