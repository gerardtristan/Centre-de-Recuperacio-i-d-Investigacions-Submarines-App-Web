# 096. Una devolució torna a demanar el codi TOTP

- **Data:** 17/11/2026
- **Estat:** Acceptada (propietari, 17/11/2026; instrucció escrita: «aprovo que sí: una devolució mou diners i ha de tornar a demanar el codi TOTP»).
- **Origen:** [P-311](pendents.md), oberta pels wireframes del 05b (T-M05b-02, #176).
- **Canvia:** una regla del pla, al lloc de la regla: el pas 1 del procés [P-M05b-G](../planning.md#M05b-5-processos) (devolució iniciada pel club).

## Context

El procés P-M05b-G demana l'import i el motiu, i RN-T11 limita l'import al que s'ha cobrat. Cap regla no deia si el tresorer, que ja ha entrat a l'administració amb el doble factor, ha de tornar a escriure el codi per fer una devolució. Una devolució treu diners del club i no es pot desfer. Per revocar un mandat, la P-133 proposa no tornar-lo a demanar.

## Alternatives

- **A.** El codi TOTP al mateix diàleg de la devolució, amb l'import i el motiu (com en canviar permisos, [059](059-rols-i-permisos-editables.md)).
- **B.** Import, motiu i confirmació, sense tornar a demanar el codi.

## Decisió

**A.** Per fer una devolució, el tresorer torna a escriure el codi TOTP, al mateix diàleg on escriu l'import i el motiu. El servidor comprova el codi abans de cridar l'adaptador o de registrar la devolució. Amb un codi incorrecte o caducat, no es fa res.

## Conseqüències

- **Pla:** el pas 1 de P-M05b-G diu ara que el tresorer escriu l'import, el motiu i el codi TOTP.
- **Codi:** el servei `apps/payments/refunds.refund()` ja existeix, però encara no té cap pantalla ni ruta. Quan es faci la pantalla de devolucions (carril de pagaments), la vista comprova el codi abans de cridar el servei, amb una prova per a «codi incorrecte → cap devolució ni cap moviment». Els wireframes (`admin.html`, T-M05b-02) ja ho mostren així.
- **No canvia:** qui pot fer devolucions (B5, només el tresorer, [059](059-rols-i-permisos-editables.md)), el límit de RN-T11 ni la resta del procés.
