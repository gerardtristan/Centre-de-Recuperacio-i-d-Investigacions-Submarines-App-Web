# 069 — Condició de soci i quota d'alta per mesos

- **Data:** 06/11/2026
- **Estat:** **Substituïda en part per la [070](070-quota-integra-i-renovacio-als-12-mesos-del-pagament.md) (09/11/2026):** el punt 2 (prorrata mensual i regla de novembre i desembre) i els exemples del punt 3 ja no valen; el punt 1 (condició de soci) es manté. Text original:
- Acceptada pel responsable del projecte el 06/11/2026. Substitueix RN-M01-16 i el supòsit de S-M01-02 («quota sencera a mig any»). Precisa RN-M01-07 i RN-M01-18 sense canviar-ne el text. Tres detalls del càlcul queden oberts a la [P-59](pendents.md) i l'activació dels exempts, a la [P-57](pendents.md).

## Context
RN-M01-16 deia que qui s'apunta a mig any paga la quota sencera [A validar: junta]. La revisió de la T-M01-13 va demanar que el formulari no ho donés per fet i va fixar què fa soci una persona. La [068](068-socis-menors-i-inici-del-pagament-de-la-quota.md) ja havia fixat l'exempció per edat.

## Decisió
1. **Condició de soci.** Paraules del responsable: «Un soci no és soci fins que no el donem d'alta —acceptem— i fins que no paga. 100% així sense cap mena de dubte.»
   - Enviar la sol·licitud no fa ningú soci. Aprovar-la o assignar un número tampoc no n'hi ha prou.
   - Activar el compte personal no dona la condició de soci.
   - Per a les altes amb quota exigible, cal l'alta aprovada i el pagament confirmat. Fins llavors, ni estat actiu, ni carnet, ni drets reservats als socis.
   - Si el número s'assigna abans de cobrar (RN-M01-05), el número sol no acredita una alta activa.
2. **Quota d'alta per mesos.**
   - **Altes de gener a octubre:** la quota de l'any en curs es prorrateja **per mesos**, mai per dies.
   - **Altes de novembre i desembre:** no es cobra quota de l'any en curs; es cobra la quota anual sencera de l'any següent, sense prorrata, que també cobreix el que queda de l'any d'alta. Amb l'alta aprovada i el pagament confirmat, la persona és sòcia sense esperar a l'1 de gener.
   - **Sense doble cobrament:** una anualitat ja coberta no es torna a cobrar en la renovació.
   - **Exempció per edat** ([068](068-socis-menors-i-inici-del-pagament-de-la-quota.md)): té prioritat per al període al qual s'aplica. En una alta de novembre o desembre es comprova si l'any següent ja és el primer any de quota.
3. **Presentació discreta.** El formulari mostra l'import i el període quan es poden calcular amb aquestes regles, sense explicar tot el calendari ni presentar-ho com una promoció. Per a novembre i desembre: «Quota [any següent]: [import]. Inclou el que queda de [any actual].» No es mostra cap import inventat mentre falti una regla, ni cap import exigible en un període exempt.

## Conseqüències
- **T-M01-13:** mostra la previsió (exempció, quota de l'any següent al novembre i desembre, i «proporcional als mesos que queden» sense import de gener a octubre) amb `apps/members/fee_rules.py`. No crea cap quota.
- **T-M01-14** (aprovar), **T-M01-18** (generar quotes i renovar), **05b** (pagament confirmat, `on_fee_paid`) i **T-M01-19** (carnet): apliquen aquesta decisió. Casos de prova previstos: prorrata mensual; octubre i novembre; desembre i gener; exempcions per edat; cap doble cobrament ([pla](../planning.md#M01-addenda-058-menors)).
- **Oberts:**
  - [P-59](pendents.md): si el mes de referència compta sencer, quin fet el fixa (enviament, aprovació o un altre) i l'arrodoniment. Fins llavors, cap import de gener a octubre.
  - [P-57](pendents.md): si els exempts per edat són una excepció a l'exigència de pagament.
- **No hi té res a veure:** la quota de 3 × 32 € del full en paper ([P-60](pendents.md)). No és un recàrrec, no s'activa i no és la prorrata.

## Fonts
- Decisions del responsable del projecte, 06/11/2026 (revisió de la T-M01-13).
- RN-M01-05, RN-M01-07, RN-M01-16, RN-M01-18 i S-M01-02 del [pla](../planning.md); [068](068-socis-menors-i-inici-del-pagament-de-la-quota.md).
