# 094. Les PR `risc:alt` es fusionen sense esperar el propietari, i fins a tres carrils alhora

- **Data:** 16/11/2026
- **Estat:** Acceptada (propietari, 16/11/2026; instrucció escrita). El text del propietari: «Norma nova: les PR risc:alt ja no esperen el meu sí. Fusiona-les tu quan compleixin tot això: CI en verd, revisió automàtica sense res pendent, i totes les normes del projecte (dades només a la UE, RGPD, tot valor configurable, decisions i tauler). Apunta aquesta norma a CLAUDE.md i al pla […]. Només m'has de preguntar abans de: tocar diners reals o producció, esborrar dades, o canviar una norma del pla. Per anar més ràpid, treballa en diverses tasques alhora (fins a 3 carrils), per ordre del camí crític i sense compartir fitxers ni migracions. […] Al resum diari, digues quines risc:alt has fusionat i per què, en una línia cadascuna.»
- **Canvia:** l'interruptor D4 de la [089](089-prova-d-acceleracio-interruptors-d1-a-d6.md) («el propietari aprova abans les `risc:alt`») i la regla de `CLAUDE.md` «no es comença cap altra tasca sense confirmació».

## Decisió

1. **Una PR `risc:alt` la fusiona Claude, sense esperar el propietari**, quan compleix les tres condicions:
   - el CI és verd i la branca està al dia amb `master`;
   - la revisió automàtica no té res pendent;
   - compleix totes les normes del projecte: dades només a la UE, RGPD, tot valor de negoci configurable, i les decisions i el tauler de preguntes al dia (cada dubte nou a `pendents.md` i a `tauler-preguntes.yml`, amb la seva opció per defecte).
2. **Claude pregunta abans al propietari només per a tres coses:** tocar diners reals o producció, esborrar dades, o canviar una norma del pla. Una PR que en faci alguna no es fusiona sense el seu sí escrit.
3. **Fins a tres carrils alhora**, per ordre del camí crític ([pla d'acceleració](../plans/pla-acceleracio.md), §3 i §4.1). Dos carrils no comparteixen cap fitxer de codi ni cap migració. Els índexs que creixen per addició (`pendents.md`, el tauler, l'índex del diari i l'estat) es resolen en fer el rebase. La tasca següent del camí crític es comença sense demanar confirmació.
4. **Resum diari:** quines `risc:alt` s'han fusionat i per què, en una línia cadascuna, a més del resum de 5 línies de la D4.

## Conseqüències

- Les etiquetes `risc:*` es mantenen: diuen què s'ha de revisar amb més cura, però ja no qui fusiona.
- Continua vigent la D2: un dubte irreversible es construeix apagat i no s'activa a producció sense resposta. Activar-lo és «tocar producció», i per tant cal preguntar.
- [A validar: propietari] El text s'ha escrit per a la sessió PILOT. S'entén que també val per a la sessió de DISSENY (carril D) i les seves `risc:alt`; si no és així, es corregeix aquí.
- En revocar-la, torna la D4 tal com era: «el propietari aprova abans les `risc:alt`».
