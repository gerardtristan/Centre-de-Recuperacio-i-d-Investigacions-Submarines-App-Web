# 064 — Una baixa es pot rebutjar amb motiu

- **Data:** 03/11/2026
- **Estat:** Acceptada en part. El responsable del projecte ha comunicat que la junta ho ha validat; data de la validació de la junta: no consta. Resol en part [P-50](pendents.md).

## Context
P-M01-C deia que la secretaria valida la baixa i en fixa la data efectiva, sense dir si la podia rebutjar. El wireframe de la T-M01-02 hi té «Rebutja…». RN-M01-20, S-M01-05 i L-M01-03 diuen què passa amb les quotes pendents posteriors a la data efectiva [A validar: tresorer].

## Decisió
- Una sol·licitud de baixa es pot rebutjar, amb motiu obligatori. La sol·licitud passa a `rejected` i el soci continua amb l'estat que tenia.

## Pendent (P-50, no s'implementa fins que es decideixi)
- Qui pot rebutjar una baixa i per quins motius.
- Què passa si el soci té quotes impagades.
- Qui pot perdonar o anul·lar una quota anterior, amb quin permís i amb quin motiu (sempre una anul·lació, mai un esborrat).
- Què es diu al soci abans d'enviar la sol·licitud.

## Conseqüències
- P-M01-C, pas 2: «la valida i fixa la data efectiva, o la rebutja amb motiu obligatori».
- Model: el motiu de la baixa i el de la resolució es guarden en camps separats, `request_reason` i `resolution_reason`, que substitueixen el camp `reason` de `MemberRequest` ([addenda de M01-6](../planning.md#M01-addenda-064), amb CA-M01-47). La taula aprovada no s'edita. La T-M01-11 els construeix i la T-M01-22 els anonimitza.

## Fonts
- Comunicació del responsable del projecte, 03/11/2026
- [pendents.md](pendents.md) (P-50); RN-M01-20, S-M01-05 i L-M01-03 del [pla](../planning.md)
