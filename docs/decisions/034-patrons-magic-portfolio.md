# 034 — Patrons de Magic Portfolio com a referència visual

- **Data:** 27/10/2026
- **Estat:** Acceptada (contingut real, fotos, servei de butlletí i manteniment del contingut [A validar]: P-40 a P-43). Amplia la [030](030-sistema-de-disseny.md), la [031](031-estil-neumorfic-limitat.md) i la [032](032-immersio-socis-i-centre.md). La [033](033-migracio-nextjs-once-ui.md) queda registrada com a «Descartada»: no es migra a Next.js amb Once UI Core.

## Context
L'equip vol enriquir el disseny amb patrons de Magic Portfolio (Once UI) sense canviar la pila: continuem amb HTML i CSS plans. La plantilla té llicència CC BY-NC 4.0 (cal citar l'autor i no se'n permet l'ús comercial), i per això no se'n pot copiar codi, textos ni imatges.

## Alternatives
1. **Fer servir la plantilla (Next.js i Once UI).** Es descarta perquè canvia la pila i obliga a complir la llicència.
2. **Fer-la servir només com a referència visual i reimplementar-ne els patrons amb els nostres tokens.** És l'opció triada.
3. **No fer-la servir.** És possible, però la web perdria patrons útils (sortida destacada, memòries, entrades amb data).

## Decisió
- Magic Portfolio és una **referència visual**: no se'n copia codi, textos ni imatges. L'anàlisi patró per patró és a [docs/analisi-magic-portfolio.md](../analisi-magic-portfolio.md).
- **Web pública:**
  - una portada més neta, amb una sola acció principal i una sortida destacada;
  - una secció «Projectes» amb targetes tipus memòria (objectiu, dades i resultats), per a medi ambient i Minka;
  - una secció «Notícies i conferències» amb entrades amb data;
  - una galeria submarina amb espais reservats;
  - una subscripció al butlletí al peu, amb consentiment.
  - La navegació no s'allarga: a l'escriptori es continuen veient 6 enllaços més «Més», i les seccions noves s'agrupen a «Més» a la tauleta i al mòbil.
- **Compte personal:** només s'afinen la tipografia, les targetes i els xips (targetes planes amb vora fina, xips en forma de pastilla, titulars més grans a les sortides). L'estructura de la 032 no canvia.
- **Administració:** no es toca. Els afinaments viuen a l'estil de cada pàgina i no a `tokens.css`, perquè no arribin a l'administració.
- **Butlletí:** s'aplica la [004](004-correu.md) (Brevo). Es descarta el proveïdor de la plantilla.
- **Atribució:** `docs/design-system.md` §10 recull una nota d'atribució cortesa.

## Conseqüències
- Cal contingut real per als projectes i les notícies, fotos amb drets d'imatge, la confirmació del servei de butlletí i una persona responsable del contingut (P-40 a P-43).
- Les idees de «contingut separat» i de «seccions activables» queden com a proposta per a l'editor (etapa 4) i el mòdul 07.
- La decisió 033 recull la migració a Next.js amb Once UI Core que s'ha valorat i descartat; aquesta decisió (034) és l'alternativa que s'aplica.

## Fonts
- Encàrrec de l'equip (27/10/2026)
- Magic Portfolio: pàgina del producte i README del repositori (llicència CC BY-NC 4.0)
- [030](030-sistema-de-disseny.md), [031](031-estil-neumorfic-limitat.md), [032](032-immersio-socis-i-centre.md), [004](004-correu.md)
