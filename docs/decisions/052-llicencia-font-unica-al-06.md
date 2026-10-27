# 052 — La llicència té una sola font: el mòdul 06

- **Data:** 27/10/2026
- **Estat:** Acceptada. Afegeix una **addenda mínima** al [M01](../planning.md#M01-addenda-052) de `planning.md`, que ja estava aprovat, **sense canviar-ne cap regla**. Es manté el servei de lectura de la [049](049-peces-noves-a-moduls-aprovats-per-al-02.md).

## Context
- El 01 (aprovat) guarda un registre mínim de llicència per no perdre-la en deixar Cluber (024), i la secretaria el pot editar.
- El 06 (llicències) porta el cicle complet: demanar, pagar, tramitar, vigència, renovació i cancel·lació.
- Amb totes dues coses editables hi hauria dues fonts, i el 02 i el carnet podrien dir coses diferents ([M06-13](../planning.md#M06-13-riscos), dubte 1).
- Si el 01 cridés el 06 per llegir la llicència, i el 06 cridés el 01 per saber si algú és soci, es crearia un cicle de dependències.

## Decisió
1. **El 06 és l'únic propietari de les dades de llicència.**
2. El 06 **emet esdeveniments** amb el mecanisme de la 049 (dins la mateixa transacció, lliurament a la cua, idempotent per esdeveniment i subscriptor, amb registre):
   - `licence.issued` (emesa, és a dir, passa a vigent);
   - `licence.renewed` (renovada);
   - `licence.expired` (caducada, l'emet la tasca diària);
   - `licence.cancelled` (anul·lada).
3. **El 01 només en guarda una còpia de lectura** (el seu registre mínim), que s'actualitza quan rep aquests esdeveniments. El 01 s'hi subscriu a través del mecanisme d'esdeveniments de la 00 i no importa cap codi del 06, de manera que **no hi ha cicle**: el 06 depèn del 01, i el 01 no depèn del 06.
4. El servei de lectura de la 049 (`members.licence_record` i `members.licence_records`) **es manté** i llegeix aquesta còpia.
5. **Cap regla del 01 canvia.** RN-M01-29 (tipus, data d'alta i de caducitat) es continua complint.
6. **Què deixa d'existir al 01** quan el 06 entri en producció:
   - el formulari per crear o editar a mà el registre mínim (la secretaria passa de «Sí» a «Consulta» a la fila P19);
   - l'origen `manual` per a registres nous.
7. **Què es conserva al 01:** el model del registre mínim, RN-M01-29, els registres importats de Cluber (origen `cluber`) i els fets a mà abans del 06, la lectura a la fitxa i al carnet, els serveis de la 049 i l'exportació i l'anonimització RGPD.
8. **El pas dels registres del 01 al 06** es fa una sola vegada. Cada llicència creada recorda de quin registre del 01 surt, i l'esdeveniment `licence.issued` d'aquestes llicències actualitza aquell registre en lloc de crear-ne un de nou.

## Conseqüències
- Tasca nova al 01: T-M01-31 (subscriptor dels esdeveniments de llicència i còpia de lectura). Tasca al 06: emetre els esdeveniments.
- El 02 llegeix `licences.current` quan existeixi el 06; fins llavors, `members.licence_record` (049).
- La llicència d'un dia no es lliga a cap activitat al 06. Si cal, és el 02 qui demana al 06 si una activitat necessita llicència d'un dia (requisit pendent del 02).

## Fonts
- Aprovació del responsable del projecte, 27/10/2026 (punts 4 i 5 de les aprovacions)
- [`planning.md`, M06-14](../planning.md#M06-14-aprovar)
