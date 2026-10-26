# 010 — Tres entorns i VPS de proves separat

- **Data:** 27/10/2026
- **Estat:** Acceptada

## Context
La checklist exigeix tres entorns (A2) i dades inventades fora de producció. El pressupost és ajustat, però compartir servidor o base de dades amb producció barreja dades i claus.

## Alternatives
- Proves i producció al mateix VPS: més barat, però un error a proves pot afectar producció i és fàcil barrejar secrets.
- VPS de proves permanent des del primer dia: cost innecessari mentre no hi ha pagaments.
- VPS de proves separat només quan s'integri Stripe.

## Decisió
- Entorns: local, proves i producció.
- Proves no comparteix VPS ni base de dades amb producció.
- Fins que existeixin pagaments: entorn local i entorn de proves temporal.
- Quan s'integri Stripe: VPS de proves separat, amb claus de Stripe en mode de proves.
- Stripe sempre en mode de proves fins a l'autorització escrita de la junta.
- Fora de producció, només dades inventades.

## Conseqüències
- Cost addicional d'un VPS petit des de la integració de Stripe (vegeu l'arquitectura, §3). Hetzner factura per hores: si es vol estalviar, el servidor de proves es pot crear i destruir quan calgui [A validar].
- Cada entorn té les seves pròpies variables d'entorn, buckets i claus.

## Fonts
- `docs/checklist-produccio.md`, A2
- `CLAUDE.md`, «Regles»
- Decisió de l'equip del 27/10/2026
