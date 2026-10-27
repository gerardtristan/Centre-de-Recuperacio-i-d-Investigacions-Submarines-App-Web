# 031 — Estil neumòrfic limitat

- **Data:** 27/10/2026
- **Estat:** Acceptada. Amplia la [030](030-sistema-de-disseny.md), que continua vigent.

## Context
L'equip vol afegir al sistema de disseny un detall d'identitat neumòrfic, amb relleu tou fet d'una ombra fosca i una de clara del mateix to que el fons. Ha de ser limitat i no pot perjudicar el contrast ni la llegibilitat. És un estil que sol tenir problemes d'accessibilitat: vores poc visibles i estats indicats només per l'ombra.

## Alternatives
1. **Neumorfisme a tota la interfície.** Es descarta: les taules, els formularis i els avisos perden contrast i els estats es confonen.
2. **Neumorfisme limitat a quatre peces, sempre amb vora i amb una marca d'estat que no sigui l'ombra.** És l'opció triada.
3. **No fer-lo servir.** És possible, però l'equip vol aquest detall d'identitat.

## Decisió
- Només a quatre peces: el selector de tema (control segmentat Sistema/Clar/Fosc), els avatars, el carnet de soci i la pastilla de navegació de la web pública.
- Mai a `admin.html`, a les taules, als formularis, als avisos ni als botons principals, que continuen plans.
- Quatre tokens per tema: `--neu-superficie` (igual que `--c-fons`), `--neu-ombra-fosca`, `--neu-ombra-clara` i `--neu-vora` (≥3:1). Les ombres es recalculen per a cada tema, no s'inverteixen.
- Les peces només es posen sobre el fons de pàgina. Per això, la capçalera de la pública i la del compte personal, la salutació i el carnet deixen de ser superfícies blanques.
- Cada peça té vora ≥3:1, focus visible i text ≥4,5:1. Cap estat s'indica només amb l'ombra: també porta negreta, una marca (✓ o barra) i l'estat a l'HTML.
- Amb `prefers-contrast: more`, l'efecte passa a vores plenes.
- El botó de tema que anava passant pels estats queda substituït pel control segmentat a les tres zones; a l'administració, el control és pla.

## Conseqüències
- `docs/design-system.md` §6.4 recull els tokens i els llocs on sí i on no es fa servir. `tokens.css` en té els tokens i els components.
- La capçalera pública passa a dues files a la tauleta i a l'escriptori. A més, corregeix un desbordament que hi havia entre 600 i ~1250 px.
- Quan es faci el disseny final, cal revisar amb eina el contrast de les vores i dels focus (checklist B8).

## Fonts
- Encàrrec de l'equip (27/10/2026)
- [030](030-sistema-de-disseny.md); `docs/design-system.md` §6.4 i §7
