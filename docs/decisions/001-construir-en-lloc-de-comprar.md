# 001 — Construir una plataforma pròpia en lloc de comprar

- **Data:** 15/10/2026 (document incremental); ratificada al context v3 del 20/10/2026
- **Estat:** Acceptada

## Context
El club gestiona socis, activitats, material i diners amb 4-5 eines (Cluber, app del banc, Excel, Gmail, WhatsApp) que es creuen a mà. Les tres necessitats que més temps fan perdre són el material per participant, el marge per activitat i la justificació d'ajuts per departament.

## Alternatives
| Opció | Preu publicat (segons la font) | Valoració ponderada |
|---|---|---|
| A. Continuar amb Cluber + Excel | Cluber des de 599 €/any | 2,75 |
| B. Programari genèric per a clubs (Clupik, SportEasy, Playoff) | 0-99 €/mes segons pla; comissions de pagament | 3,05 |
| C. Programari de busseig (Dive Admin, Anolla, Kananas) | 39-119 USD/mes o a consultar | 2,85 |
| D. Programa propi per mòduls | 100-120 €/any de servidor i còpies + manteniment en hores | 4,20 |

Criteris: ajust funcional 30 %, cost a cinc anys 20 %, propietat de dades 15 %, integració 15 %, risc i manteniment 10 %, temps d'implantació 10 %.

## Decisió
Construir una plataforma pròpia per mòduls (opció D), amb la condició que el manteniment quedi assignat i documentat dins del club.

## Conseqüències
- El risc principal és el manteniment i la dependència de persones: cal responsable a la junta, repositori amb dos accessos i documentació (README, runbook).
- La puntuació depèn dels pesos: amb més pes al risc i al temps, les opcions comercials guanyarien.
- El cost de servidor (100-120 €/any) s'ha de revisar amb l'arquitectura actual; vegeu P-06 a [pendents.md](pendents.md).
- Les funcions diferencials «no consten» a les ofertes consultades: falta verificar-ho amb una demostració [A validar].

## Fonts
- `docs/entregues/document-incremental.pdf`, §4.2-4.7
- `docs/context-projecte.md`, §10
