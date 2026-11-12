# 070 — Quota íntegra i renovació als 12 mesos del pagament

- **Data:** 09/11/2026
- **Estat:** **Substituïda en part per la [072](072-respostes-del-responsable-a-la-ronda-1-de-pendents.md) (09/11/2026):** al punt 3, els tres pagaments van repartits equitativament dins dels 12 mesos, no separats per dos mesos.
- Acceptada pel responsable del projecte el 09/11/2026. El pagament en tres quotes el va fixar la junta. **Substitueix el punt 2 de la [069](069-condicio-de-soci-i-quota-d-alta-per-mesos.md)** (prorrata mensual de gener a octubre i regla de novembre i desembre), els seus exemples del punt 3, i qualsevol formulació de quota per any natural fix o de carnet fins al 31/12. El punt 1 de la 069 (condició de soci) es manté. Tanca la [P-59](pendents.md) i la [P-60](pendents.md); obre la [P-61](pendents.md).

## Context
La 069 (06/11/2026) havia fixat una prorrata mensual per a les altes de gener a octubre i una regla especial per a novembre i desembre, amb tres detalls oberts (P-59). La revisió del responsable del 09/11/2026 la substitueix per una regla més simple, sense data comuna de renovació.

## Decisió
1. **Quota íntegra:** cada persona paga la quota sencera del seu tipus quan comença a pagar. No hi ha prorrata, ni mensual ni diària, ni cap regla especial per a novembre i desembre.
2. **Renovació individual:** la quota es renova 12 mesos després de la data en què es confirma el pagament. Exemple: qui paga al novembre torna a pagar al novembre de l'any següent. No hi ha cap data comuna de renovació.
3. **Pagament en tres quotes** (ple dret, 3 × 32 €; fixat per la junta): funciona igual, amb els tres pagaments separats per dos mesos. No cal que cobreixin tot l'any. El cicle de renovació el marca el primer pagament. **No s'implementa ara** ni es mostra cap opció de plaços al formulari d'alta.
4. **Menors:** es manté la [068](068-socis-menors-i-inici-del-pagament-de-la-quota.md). No paguen fins que han complert 14 anys i comencen a pagar l'1 de gener següent.
5. **Descartat**, perquè només tenia sentit amb la prorrata o amb una data comuna: la campanya anual de l'1 de gener, el carnet fix fins al 31/12, la protecció contra el doble cobrament d'una anualitat ja cobrada a l'alta i els casos de prova d'octubre/novembre i desembre/gener.

## Conseqüències
- **T-M01-13:** el formulari mostra la quota anual íntegra del tipus amb «L'import es confirma en aprovar l'alta» i, per als exempts, «sense quota fins al 31/12/AAAA». Cap text de prorrata, de «la resta de l'any», d'any natural ni de plaços.
- **T-M01-18** (generar i renovar quotes): renovació als 12 mesos del pagament confirmat, per persona; pagament en tres quotes amb el cicle marcat pel primer pagament.
- **T-M01-19** (carnet): vàlid fins a la data de renovació (12 mesos des del pagament), no fins al 31/12.
- **T-M01-14** (aprovar): crea la quota íntegra del tipus; no calcula cap prorrata.
- **RN-M01-12, RN-M01-17 i RN-M01-19** (quota per període, any natural, «vàlid fins a» a final del període): queden precisades al [pla](../planning.md) amb el període de 12 mesos des del pagament.
- **Oberts ([P-61](pendents.md)):**
  - quan passa a actiu i fins quan té carnet qui paga en tres quotes;
  - què passa si no paga un termini;
  - quan es pot triar el pagament en tres quotes;
  - si afecta els menors;
  - quina és la data de renovació d'un menor.
- **No canvia:** la condició de soci (069, punt 1) i la [P-57](pendents.md) (exempts), que continua oberta.

## Fonts
- Decisió del responsable del projecte, 09/11/2026 (revisió de la T-M01-13); pagament en tres quotes fixat per la junta, segons el responsable.
- [069](069-condicio-de-soci-i-quota-d-alta-per-mesos.md), [068](068-socis-menors-i-inici-del-pagament-de-la-quota.md); RN-M01-12, RN-M01-16, RN-M01-17, RN-M01-19 i RN-M01-67 a RN-M01-69 del [pla](../planning.md).
