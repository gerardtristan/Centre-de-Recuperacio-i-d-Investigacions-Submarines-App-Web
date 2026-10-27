# 020 — Baixa de Cluber sense restricció de data

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol P-20; concreta la [014](014-migracio-cluber-i-entrada-en-produccio.md))

## Context
Funcionalitats §9.13 preveia fer una campanya de quotes en paral·lel, sense cobrar a l'app mentre Cluber era actiu, i donar de baixa Cluber «quan li venç el contracte». La 014 fixa que Cluber es deixa quan la plataforma estigui activa amb pagaments.

## Decisió
- No hi ha contracte amb Cluber: el club el pot deixar quan vulgui. La 014 no té cap restricció de data.
- La campanya de quotes en paral·lel passa a ser **opcional**. La decideix la junta en preparar l'entrada en producció.

## Conseqüències
- El moment de deixar Cluber depèn només del criteri de la 014 (mòdul 05 acabat i provat) i de la migració única.
- Cluber gestiona els rebuts domiciliats actuals; com es traspassen els mandats es documenta a l'arquitectura, §4.9 (escenaris A i B, P-21).
- El text de funcionalitats §9.13 s'ha d'actualitzar; el text de substitució per al .docx és a [pendents.md](pendents.md) (P-22).

## Fonts
- Resolució de P-20 comunicada per l'equip el 27/10/2026
- `docs/funcionalitats-processos/funcionalitats-processos.pdf`, §9.13
