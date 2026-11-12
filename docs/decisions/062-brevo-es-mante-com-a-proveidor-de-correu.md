# 062 — Brevo es manté com a proveïdor de correu

- **Data:** 03/11/2026
- **Estat:** Acceptada. Tanca [P-46](pendents.md). Desenvolupa la [042](042-proveidors-substituits-pel-requisit-ue.md).

## Context
La [042](042-proveidors-substituits-pel-requisit-ue.md) mantenia Brevo només si es verificava que tots els subencarregats que tracten dades són dins la UE ([035](035-dades-nomes-dins-ue.md)).

## Decisió
- Es manté Brevo com a proveïdor de correu ([004](004-correu.md)).
- Que compleix el requisit de dades dins la UE està afirmat pel responsable del projecte el 03/11/2026.

## Conseqüències
- Si Brevo deixa de complir el requisit o canvia de subencarregats, es passa a Scaleway Transactional Email: el correu va per SMTP darrere del servei propi de la plataforma (T-M01-10), i canviar de proveïdor és canviar variables d'entorn.

## Fonts
- Afirmació del responsable del projecte, 03/11/2026
- [004](004-correu.md), [035](035-dades-nomes-dins-ue.md), [042](042-proveidors-substituits-pel-requisit-ue.md); [pendents.md](pendents.md) (P-46)
