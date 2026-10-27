# 016 — Pressupost: començar amb la producció mínima

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol P-06)

## Context
Els documents d'origen preveien 100-120 €/any de servidor i còpies (context v3 §9, document incremental §4.2, funcionalitats §2). L'arquitectura del 27/10/2026 calcula més, perquè hi suma la segona destinació de còpies, el VPS de proves i, opcionalment, el correu de pagament. La junta coneix el cost i accepta que una plataforma sense cap cost no és realista.

## Alternatives
| Escenari | Cost fix sense IVA (preus consultats el 27/10/2026) |
|---|---|
| Previsió dels documents d'origen | 100-120 €/any |
| **Producció mínima** | ≈13 €/mes · ≈160 €/any (≈195 €/any amb IVA del 21 %) |
| Producció recomanada | ≈29,50 €/mes · ≈355 €/any |

## Decisió
- Es comença amb la **producció mínima**: VPS CX23, còpies de Hetzner, Storage Box BX11, Scaleway, Brevo gratuït i VPS de proves creat quan calgui.
- La xifra de referència de 100-120 €/any queda substituïda pel cost real de l'escenari mínim, amb data de consulta, i les comissions es tracten com a part variable.
- Comparació amb Cluber, on la part fixa és molt més alta:

  | | Plataforma (producció mínima) | Cluber |
  |---|---|---|
  | Fix | ≈160 €/any sense IVA | Des de 599 €/any (pla fins a 200 esportistes; preu publicat segons el document incremental). Pla i factura reals del club [A validar] |
  | Variable | Comissions de Stripe: ≈53-110 €/any per a les quotes, més ≈1,9 % del que es cobri per targeta o Bizum | Comissions de cobrament de Cluber [A validar] |

## Conseqüències
- Es pot passar a l'escenari recomanat (CX33, Brevo Starter, VPS de proves permanent) si el volum ho demana; cada canvi es registra com a decisió nova.
- Cal fixar límits i alertes de despesa a cada proveïdor (checklist D3).
- Tots els preus són [A validar] en el moment de contractar; l'IVA real depèn de si el club el recupera [A validar amb la gestoria].

## Fonts
- Decisió comunicada per l'equip el 27/10/2026 («la junta coneix el cost»)
- `docs/arquitectura-integracions.md`, §3
- `docs/entregues/document-incremental.pdf`, §4.2 (preu de Cluber)
- `docs/context-projecte.md`, §9 (xifra anterior)
