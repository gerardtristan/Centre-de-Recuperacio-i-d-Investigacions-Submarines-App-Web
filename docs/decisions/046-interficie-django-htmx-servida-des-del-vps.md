# 046 — Interfície amb plantilles de Django i HTMX, servida des del VPS

- **Data:** 27/10/2026
- **Estat:** Acceptada. Substitueix la part de frontend de la [002](002-pila-tecnologica.md) («Web pública i PWA: Cloudflare Pages» i «Backend i API: Django amb API REST» en allò que toca la interfície). Resol la pila del frontend que la [030](030-sistema-de-disseny.md) deixava [A validar].

## Context
- La 002 preveia la web pública i la PWA a Cloudflare Pages i una API REST de Django per alimentar-les.
- La [042](042-proveidors-substituits-pel-requisit-ue.md) treu Cloudflare pel requisit de dades dins la UE ([035](035-dades-nomes-dins-ue.md)): la web i la PWA se serveixen des del VPS de Hetzner.
- La [034](034-patrons-magic-portfolio.md) manté els wireframes en HTML i CSS plans, i la [041](041-web-installable-i-avisos-sense-push.md) fixa una web instal·lable sense botigues ni push.
- L'equip és petit i voluntari: com menys peces s'hagin de construir i mantenir, millor.

## Alternatives
- **API REST i una aplicació de JavaScript separada** (com deia la 002): dues bases de codi, una compilació de frontend i més superfície d'atac.
- **Plantilles de Django i HTMX servides pel mateix Django:** una sola base de codi, sense compilació de frontend, permisos comprovats al servidor a cada vista.

## Decisió
- La interfície (web pública, compte personal i administració) es fa amb **plantilles de Django i HTMX**, servida pel mateix Django des del **VPS** de Hetzner.
- **L'arxiu d'HTMX es serveix des del servidor propi**, entre els fitxers estàtics, amb la versió fixada. **Sense CDN.** Quan s'actualitza, es comprova l'empremta de l'arxiu nou abans de desar-lo al repositori.
- Només s'exposen endpoints de dades on calguin, i sempre amb autenticació i permís per defecte (CLAUDE.md). Les notificacions dels proveïdors de pagament són endpoints públics declarats i verificats per firma, no part de cap API pública.
- El manifest i el service worker de la web instal·lable (041) se serveixen des del mateix origen.

## Conseqüències
- Les peticions d'HTMX porten el testimoni CSRF de Django; una prova ho comprova a cada formulari.
- La política de seguretat de continguts (CSP) pot prohibir scripts de tercers: tot el JavaScript és propi o servit des del servidor.
- Els tokens i els components del sistema de disseny (030 a 034) es fan servir directament a les plantilles.
- CLAUDE.md («Pila») i l'arquitectura s'alineen amb aquesta decisió en el mateix canvi que les alinei amb la 042 (no s'editen les decisions antigues).
- Si algun dia cal una app nativa, s'hi afegirà una API concreta per a aquell ús, amb una decisió nova.

## Fonts
- Aprovació del pla del mòdul 01, resposta 1, comunicada pel responsable del projecte el 27/10/2026
- [`docs/planning.md`](../planning.md), §3 (regles generals)
