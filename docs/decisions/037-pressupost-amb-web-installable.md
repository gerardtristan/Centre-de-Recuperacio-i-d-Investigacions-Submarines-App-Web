# 037 — Pressupost amb web instal·lable i proveïdors dins la UE

- **Data:** 27/10/2026
- **Estat:** Proposada, pendent de la junta. Amplia la [016](016-pressupost-produccio-minima.md), que continua vigent. Origen: decisió 0006 del repositori anterior (històric).

## Context
- La 016 fixa la producció mínima en ≈160 €/any sense IVA (≈195 €/any amb IVA del 21 %), amb Cloudflare a 0 € i comissions de Stripe com a part variable.
- Un estudi anterior de publicació a les botigues d'apps (Apple 99 $/any, Google 25 $ un cop) portava el cost a uns 200-230 €/any.
- La [041](041-web-installable-i-avisos-sense-push.md) treu les botigues i la [042](042-proveidors-substituits-pel-requisit-ue.md) treu Cloudflare i Stripe.

## Alternatives
| Partida | Amb botigues | **Web instal·lable (041)** |
|---|---|---|
| Producció mínima (016) | ≈160 €/any | ≈160 €/any |
| Apple Developer Program | 99 $/any (≈85-95 €) | 0 € |
| Google Play | 25 $ un sol cop | 0 € |
| Web i PWA (abans Cloudflare Pages) | 0 € | 0 €: se serveix des del VPS de Hetzner |
| **Total fix sense IVA** | **≈245-255 €/any** | **≈160 €/any** |
| Total fix amb IVA del 21 % | ≈300-310 €/any | ≈195 €/any |

## Decisió
- Proposta a la junta: cost fix de **≈160 €/any sense IVA** amb la web instal·lable.
- La part variable passa a ser la del proveïdor de pagaments que es triï a la [043](043-proveidor-de-pagaments-dins-la-ue.md) [A verificar].

## Conseqüències
- Si la junta vol les botigues, cal una excepció escrita a la 035 i el cost puja a ≈250 €/any.
- Tots els preus són [A verificar] en el moment de contractar; IVA [A validar amb la gestoria]; tipus de canvi del dòlar [A verificar].

## Fonts
- [016](016-pressupost-produccio-minima.md); `docs/arquitectura-integracions.md`, §3
- Estudi de publicació a les botigues (22/10/2026)
