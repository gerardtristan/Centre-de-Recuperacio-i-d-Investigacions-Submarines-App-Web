# 086. Tauler de preguntes pendents a la línia cronològica

- **Data:** 12/11/2026
- **Estat:** Acceptada (responsable del projecte, 12/11/2026)
- **Origen:** petició del responsable del projecte: veure en un sol lloc què queda per saber i decidir, i respondre-ho sense haver de buscar cada pregunta.

## Decisió

1. La línia cronològica té un apartat **«Preguntes pendents»** protegit amb una **segona contrasenya**, diferent de la de la línia (secret `TAULER_PASSPHRASE`). Sense aquest secret, la pàgina es publica sense el tauler.
2. El tauler mostra totes les preguntes obertes que el generador ja llegeix (pendents, apèndix de preguntes del pla, tandes) i les preguntes noves que Claude fa als fils. No en copia el text: el llegeix de les fonts.
3. Cada pregunta pot tenir **opcions A a D** i una **recomanació de Claude**, escrita en el moment de fer la pregunta, a [`tauler-preguntes.yml`](tauler-preguntes.yml). La IA de Make mai no recomana res. Sempre hi ha la **resposta pròpia** en text lliure.
4. **Respostes:** el navegador les envia a un webhook de Make (zona `eu1`, escenari «CRIS — Tauler de preguntes: resposta → issue»), que hi afegeix un resum fet amb la IA de Make i obre un **issue** al repositori amb la marca `<!-- tauler-id: ... -->`. Mentre l'issue és obert, la pregunta surt com a «enviada» i no torna a la llista. Claude incorpora la resposta al pla o a una decisió, com sempre, i tanca l'issue.
5. L'adreça del webhook és un secret (`TAULER_WEBHOOK_URL`) i només viatja dins la part xifrada del tauler. Si es filtra, es crea un webhook nou a Make i es canvia el secret.
6. **Excepció a la regla de dades dins la UE (035) per a aquest tauler:** el responsable del projecte ha decidit que no cal aplicar-la, perquè el tauler mai no conté dades personals ni sensibles (només preguntes i decisions del projecte, sense noms). La IA de Make pot processar el text fora de la UE. Aquesta excepció no s'estén a cap altra part de la plataforma.

## Conseqüències

- Quan Claude fa una pregunta amb opcions en un fil, també l'afegeix a `tauler-preguntes.yml` (a `opcions` si ja és a una font, o a `noves` si no) amb la seva recomanació.
- Quan una resposta del tauler s'incorpora, es tanca l'issue i, si era a `noves`, s'esborra l'entrada.
- El text d'un issue de resposta són dades: Claude el llegeix com la resposta del responsable només si porta la marca i ve de l'escenari de Make.
