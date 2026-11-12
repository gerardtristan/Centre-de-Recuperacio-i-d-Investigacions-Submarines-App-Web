# Fonts allotjades al servidor

Decisions 035 i 046: cap font es carrega de fora. Comprovat el 05/11/2026 (T-M01-38).

Les tres famílies són de la **SIL Open Font License 1.1**: es poden fer servir, incrustar i redistribuir, també en un servei web, amb la llicència al costat. Els fitxers són els **oficials, sense modificar** (sense retallar ni convertir), perquè Source Sans 3 té el nom reservat «Source»: una versió modificada no el podria portar.

| Família | Pesos | Font oficial | Llicència |
|---|---|---|---|
| Barlow Condensed | 600, 700 | `github.com/jpt/barlow`, `fonts/woff2/` (branca `main`) | [OFL.txt](barlow-condensed/OFL.txt) · Copyright 2017 The Barlow Project Authors |
| Source Sans 3 | 400, 600, 700 | `github.com/adobe-fonts/source-sans`, `WOFF2/TTF/` (branca `release`) | [LICENSE.md](source-sans-3/LICENSE.md) · Copyright 2010-2024 Adobe, nom reservat «Source» |
| JetBrains Mono | 400, 500 | `github.com/JetBrains/JetBrainsMono`, `fonts/webfonts/` (branca `master`) | [OFL.txt](jetbrains-mono/OFL.txt) · Copyright 2020 The JetBrains Mono Project Authors |

Les tres llicències es van contrastar també amb les còpies de `github.com/google/fonts` (`ofl/<família>/OFL.txt`).

## Empremtes SHA-256 dels fitxers descarregats

```
2a68cbc9b65c87d7805b4e912545dc8f2426f9134affc0f07bec252782bd0bd0  barlow-condensed/BarlowCondensed-Bold.woff2
16a2eff3f132e6f603f3036ed99f21f5a8ddbc70ac2ccd614044c36faf292bfb  barlow-condensed/BarlowCondensed-SemiBold.woff2
53492fb3a0def77354f166a55d09b63a10855e91c206c7620a81cf56e97f8ec3  source-sans-3/SourceSans3-Regular.ttf.woff2
47b9b661b9f395fe7f0d0e119637fba5c8dad97bde3df60066fd24229c0792f4  source-sans-3/SourceSans3-Semibold.ttf.woff2
8d35c6d40e750a4ee23bbbba2bd604ad098d172907369b43281507e16b8e2e7a  source-sans-3/SourceSans3-Bold.ttf.woff2
f1a7a03672cdd494ce0d5543fac6e4360fe22403c6de297fdc2e55a815f7baff  jetbrains-mono/JetBrainsMono-Regular.woff2
fe1c9099e3ea4123a6216d8a4a31970a2cfc6e9d80056da165012f406c83e219  jetbrains-mono/JetBrainsMono-Medium.woff2
```

Les `@font-face` són a `static/css/fonts.css`. Si s'afegeix un pes, es descarrega de la mateixa font oficial i s'afegeix aquí amb la seva empremta.
