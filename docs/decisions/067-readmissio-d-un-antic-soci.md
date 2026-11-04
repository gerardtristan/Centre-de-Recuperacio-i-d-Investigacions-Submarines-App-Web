# 067 — Readmissió d'un antic soci

- **Data:** 04/11/2026
- **Estat:** Acceptada pel responsable del projecte el 04/11/2026. Resol la [P-55](pendents.md).

## Context
RN-M01-07 diu «pendent, actiu o impagat → baixa. Cap altra transició». P-M01-C diu que qui torna es readmet amb el mateix número, i el soci és el mateix registre (un sol `Member` per persona). Per tant, la readmissió demanava una transició, de baixa a pendent, que la regla no permetia. Es va trobar en la revisió de la T-M01-11.

## Decisió
- **Transició:** baixa → pendent, només en aprovar una sol·licitud d'alta d'una persona que ja va ser sòcia (P-M01-C). Cap altra transició nova.
- **Mateix registre i mateix número:** el soci no es crea de nou i conserva el seu número ([039](039-numeros-de-soci-no-es-reutilitzen.md)).
- **Historial:** la readmissió crea una entrada d'historial.
- **`left_on`:** es buida en readmetre, dins la mateixa transacció que l'entrada d'historial. La data de la baixa continua a l'historial, que no es pot modificar.

## Conseqüències
- RN-M01-07 manté el text aprovat i hi afegeix la readmissió com a precisió d'abast datada ([pla](../planning.md)).
- La T-M01-12 implementa la transició i el buidatge de `left_on`. La seva prova comprova que l'entrada d'historial de la baixa existeix abans de buidar-lo.
- La T-M01-14 aplica la readmissió en aprovar l'alta. La seva prova separa dos casos: conservar el número del mateix soci (s'accepta i el comptador no avança) i rebre el d'un altre soci (es rebutja).
- No ho decideix aquesta decisió: la quota del període en una readmissió el mateix any ([P-54](pendents.md)).

## Fonts
- Aprovació del responsable del projecte, 04/11/2026
- [pendents.md](pendents.md) (P-55); RN-M01-07 i P-M01-C del [pla](../planning.md); [039](039-numeros-de-soci-no-es-reutilitzen.md)
