# F2-4 · Prova de flux sencer de la llesca F2-4, de les necessitats al marge congelat

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 21/11/2026 06:50 | (vegeu la PR) | 1 nova | [A comprovar] |

**En tres línies:** una prova recorre tota la llesca F2-4: una sòcia s'inscriu dient que necessita jaquet i ampolla, paga, el responsable li assigna una ampolla del club i un jaquet llogat, envia la llista al centre, lliura i recull el material (l'ampolla va a revisió) i, en tancar l'activitat, el marge congelat ja resta el lloguer i el cost d'ús del club.

## Què s'ha fet
- `apps/equipment/tests/test_flow_f2_4.py`, amb els serveis reals del 02, el 03, el 04, el 05b fictici i el 09.

## Decisions i perquè
- Mentre no hi ha factura del centre, el marge fa servir l'estimació del lloguer (RN-M03-10).

## Problemes trobats
Cap.

## Com se sap que funciona
La prova passa: necessitats desades, peça oferta, motius de tancament mentre falta material, cost per participant (2850), marge del lloguer (500) i marge congelat de 1650.

## Termes nous
Cap.
