# 106. Editor visual de la web pública

- **Data:** 24/11/2026
- **Estat:** Acceptada (encàrrec escrit del propietari del 24/11/2026, [`docs/plans/editor-web-07.md`](../plans/editor-web-07.md)). És un canvi de norma del pla; el propietari en va donar el «fusiona» per escrit (sí del 25/11/2026, donat el 27/11/2026: «Fusiona la #575»).
- **Completa:** la secció [M07](../planning.md#M07), amb l'[addenda de la 106](../planning.md#M07-addenda-106); [`pendents.md`](pendents.md) i el [tauler](tauler-preguntes.yml) (P-574 i P-575); l'estat de les tasques del [07](../estat/M07.md) i del [02](../estat/M02.md). La part de les fotos reals és la [107](107-fotos-reals-del-club-per-a-plantilles-mostres-i-captures.md).

## Context

La secció M07 (aprovada el 24/11/2026) ja preveu pàgines fetes de blocs, amb versions, i una llista tancada de nou tipus de bloc. El propietari vol que la web es pugui editar des de l'administració com un editor de webs: blocs que s'arrosseguen, vista prèvia en viu, plantilles que reprodueixin l'aspecte de la web actual ([`design/wireframes/publica.html`](../../design/wireframes/publica.html), decisió [034](034-patrons-magic-portfolio.md)), vídeos de YouTube, menús, versions i publicació programada, i que mostri les activitats del 02 i fotos de l'app.

El propietari ha triat:

1. Un editor de blocs propi, integrat a l'app: ni Wagtail ni cap CMS extern.
2. YouTube amb clic per carregar, des de `youtube-nocookie.com`, darrere de l'ajust `website.youtube_enabled`, apagat.
3. Blocs i variants tancades: cap color, mida ni tipografia lliure, i cap HTML.
4. Un flux de revisió disponible però apagat d'inici.
5. Un permís d'editar per pàgina.
6. Una vista prèvia només amb sessió i permís.

## Decisió

S'amplia el 07 amb un editor visual propi. Les regles, el catàleg de blocs (el contracte amb la sessió de disseny), els permisos, els ajustos, les tasques i qui fa cadascuna són a l'[addenda de la 106](../planning.md#M07-addenda-106). En resum:

- **RN-M07-09** admet una sola excepció de tercers: `youtube-nocookie.com`, i només després del clic del visitant, amb avís i miniatura desada al nostre emmagatzematge. No s'encén a producció fins que la junta validi el text de l'avís (P-574).
- **RN-M07-10** concreta el format: un Markdown restringit, convertit amb l'HTML desactivat i escapat, i amb una llista tancada d'esquemes d'enllaç.
- **WP1 es parteix** en WP1a (editar esborranys) i WP1b (publicar, programar i restaurar), amb abast per pàgina, i s'afegeixen WP9 (menús, capçalera, peu i blocs compartits) i WP10 (patrons). Entren al catàleg amb la T-M07-26 i, el WP9, amb la T-M07-21; la T-M07-02, feta, no canvia. La configuració inicial és la de l'actual WP1. Qui publica a la pràctica continua obert (P-43, P-575).
- **Quatre ajustos nous** amb rang, dos d'apagats.
- **Pujades i CSP:** només JPEG, PNG i WebP, tornats a codificar (sense EXIF ni GPS); PDF com a descàrrega; CSP del mateix origen. El bloc de vídeo admet també un vídeo propi, com els tutorials (formats: P-610).
- **Paperera:** una pàgina retirada es recupera; cap pàgina no s'esborra.
- **Activitats i fotos de l'app:** tres blocs d'activitats i un selector de fotos amb dues pestanyes, sobre dos serveis de lectura nous del 02 (requisit RP-M07-02, tasca T-M02-53).
- **Tasques:** canvien cinc tasques, T-M07-01, 04, 06 (es parteix en 06a i 06b), 07 i 18; n'hi ha de noves, de T-M07-19 a T-M07-31, i la T-M02-53. T-M07-01, 19 i 31 són de la sessió de disseny; la resta, del pilot.
- **Dependències noves:** Pillow (fixada), markdown-it-py i SortableJS (a `static/vendor/`, sense CDN). Cadascuna entra en una PR `risc:alt` pròpia.

## Conseqüències

- La llista de tipus de bloc i de variants es queda al codi (M07-6 ja ho deia de la llista de tipus); els patrons i els blocs compartits són dades.
- El pas 2 (el codi) no comença fins que aquesta decisió sigui a `master`. L'ordre és el de l'estudi del propietari: el catàleg visual (T-M07-19) depèn dels wireframes (T-M07-01) i no del codi, perquè el contracte de camps és la taula del catàleg de l'addenda; el nucli de blocs (T-M07-04) pot anar en paral·lel.
- Cap regla d'un altre mòdul no canvia. El 02 n'ofereix dos serveis de lectura nous (RP-M07-02); no hi ha cap escriptura entre mòduls.
- No s'encén res a producció: `website.youtube_enabled` i `website.review_flow_enabled` comencen apagats.

## Fonts

- Encàrrec del propietari del 24/11/2026: [`docs/plans/editor-web-07.md`](../plans/editor-web-07.md) i, per a la sessió de disseny, [`design/encarrecs/editor-web-07.md`](../../design/encarrecs/editor-web-07.md).
- Estudi del propietari, [«Estudi: editor visual de la web pública (M07)»](https://claude.ai/artifact/NpiWqot3HiE225xj2sqpdw) (24/11/2026), al qual es remet l'encàrrec per a la llista de blocs i les dues taules de tasques. No es copia al repositori. L'addenda es va escriure primer a partir de l'encàrrec de disseny i el 24/11/2026 es va revisar contra l'estudi i es va corregir: vídeo propi al bloc de vídeo, accent de la pàgina, recuperar una pàgina retirada (RN-M07-25 i 26, CA-M07-33); la T-M07-02 no canvia i els permisos nous van a la T-M07-26 (i el WP9 a la T-M07-21); esborrany per pàgina i renderitzador únic a la T-M07-04; nou repartiment de la 06a i la 06b; punt focal i WebP a la T-M07-07; i esforç, dependències i «feta quan» de les T-M07-19 a 29 i de la T-M02-53 com a l'estudi. La T-M07-31 es queda com a la 107 (vegeu l'addenda).
