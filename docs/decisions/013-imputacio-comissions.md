# 013 — Imputació de comissions per departament

- **Data:** 27/10/2026
- **Estat:** Proposada: pendent de validació de la junta (P-08)

## Context
El document de funcionalitats (§7) diu que «la comissió del cobrament es registra com a despesa de la mateixa activitat». Però les quotes de soci són ingrés general i no entren al marge de cap activitat (§3, Regles). Una comissió de quota no té cap activitat on anar.

## Alternatives
- Deixar les comissions de quotes sense imputar: impossible, perquè tota despesa ha de tenir departament (§7, Regles).
- Repartir-les entre activitats: arbitrari i distorsiona el marge.
- Imputar-les a un departament o centre de cost general.

## Decisió
- Cada ingrés i cada despesa té departament (centre de cost), perquè s'ha de poder justificar per departament.
- Comissions de quotes anuals: departament «General / Quotes de socis».
- Comissions d'inscripcions: despesa de la mateixa activitat (i del seu departament).
- Comissions de llicències: [A validar] (proposta: departament «General / Llicències», perquè el soci paga el preu de la federació sense marge per al club).

## Conseqüències
- La llista de departaments l'ha de fixar la junta (pregunta oberta de funcionalitats §7).
- Les comissions no es retornen quan es fa una devolució: la despesa es manté i la devolució és un moviment nou.

## Fonts
- `docs/funcionalitats-processos/funcionalitats-processos.pdf`, §3 «Regles», §7 i §8.1
- Recomanació de l'equip del 27/10/2026
