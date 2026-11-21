# T-M02-40b i F2-3 · Cost de material previst i prova de flux sencer del marge

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 21/11/2026 05:04 | (vegeu la PR) | 4 noves | [A comprovar] |

**En tres línies:** quan es crea una activitat, el cost de material previst per participant es copia sol de l'estàndard que calcula el 03, i qui té permís el pot canviar si hi posa la nota. Una prova recorre tota la llesca F2-3: del preu estàndard del lloc al marge congelat en tancar l'activitat.

## Què s'ha fet
- `apps/activities/material_cost.py`: `copy_standard` (la crida `services._create` després de desar l'activitat, quan el 03 ja hi ha copiat el material típic) i `set_material_cost` (AC23 per objecte, nota obligatòria si difereix de l'estàndard, registre amb el valor anterior; no crea cap càrrec).
- `apps/margins/tests/test_flow_f2_3.py`: lloc amb preu estàndard 4500 → preu propi de 6000 (rebutjat sense nota, acceptat amb nota) → cost de material 350 copiat del 03 → 10 inscripcions de socis pagades amb el proveïdor fictici (esdeveniment `charge.paid`, ingrés i comissió a la 04) → embarcació i aire amb factura, pagades i repartides → marge previst 60.000 − 37.000 − 3500 = 19.500 → activitat feta → tancament amb `MarginSnapshot` (22.700, 37,8 %).

## Decisions i perquè
- El marge real encara no resta el cost de material: el cost real del 03 arriba amb la T-M03-13 (drecera ja dita a `margins/services.py`); la prova ho diu.
- Una activitat sense material típic al 03 queda amb cost 0, no buit: el calculador del 03 hi és.

## Problemes trobats
L'ajudant `invoice()` de les proves de despeses fa servir sempre la mateixa clau de fitxer: la prova en fa una sola per a les dues factures.

## Com se sap que funciona
`apps/activities/tests/test_material_cost.py` (còpia en crear, CA-M02-45, AC23 per objecte) i la prova de flux sencer.

## Termes nous
- **Prova de flux sencer:** una prova que travessa diversos mòduls de punta a punta, com ho faria la feina real.
